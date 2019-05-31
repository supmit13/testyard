/*
Compile Command: gcc -o listener listener.c
*** gcc -Wall -o listener $(xml2-config --cflags) $(xml2-config --libs) listener.c  -I/usr/include/libxml2  -lxml2 

'listener' will be the executable that would act as the daemon process to read the program requests, decode them from
Base64 encoding, push them to a specific docker container image that is "UP" and have it compiled (if necessary), and
execute it in the container image. Once that is done, it will be take the return value (if any) of the code being run
(please note that the code may actually fail during compilation process or run process), and this return value will then
be sent back to the caller program at testyard's main "run code" facility.

Note: 'listener' will spawn child processes (not threads, as we would not like to have memory shared between 2 or more
user fed programs) and so this code might need to scale horizontally. We will handle this situation as well as various
other variable values using a settings file (listen_settings.ini), which will be placed in a directory named "config"
that resides in the same directory where 'listener' resides. For now, you need to manipulate 'listen_settings.ini' by
using a text editor manually. May be, later on at some point in time, we will provide you with a GUI to do these changes.

Code writer: Supriyo Mitra. In case of any discrepancies/issues/failures, please contact me at testyard.in@gmail.com 

*/

#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <netdb.h>
#include <netinet/in.h>
#include <errno.h>
#include <stdlib.h>
#include <libxml/parser.h>

#define MAX_SIZE 20000


typedef struct codemap{
	int pid;
	char *proglang;
	char *code;
	char *returnval;
} codemap ;

typedef struct codequeue{
	int count;
	codemap *q;
} codequeue;

/* Forward Declarations */
char * handle_operation(int sessfd, char *data, char *proglang);
/* char * b64decode(const void* data, const size_t len); */
void readconfig(char *ipaddr, int *port, int *backlogs, int *reuseaddr, int *max_code_size);
void send_err_msg(int errnum);
/* void read_xml(char *data, int *user_id, int *test_id, int *challenge_id, char **code_enc, char **proglang); */
char ** get_xml_data(char *xmldump);
void b64decode(char *code_enc, char **code);
/* Forward declarations end here */


int main(int argc, char *argv[]){
	int sockfd, clientsock, readlen, s, r, conn_backlogs, reuseaddr;
	struct sockaddr_in server, client;
	char *ipaddr;
	int port, max_code_size;
    int sessfd, read_size;
	pid_t pid;
    codequeue *queue;
	char *code;
	char *code_enc; /* code encoded as base64 */
	char *buffer;
	char *retval;
	char *data;
	char *proglang;
	int user_id, test_id, challenge_id;
	char **retlist;

    /* I will be using 'malloc' very heavily here though I understand its vulnerabilities. Later on, I would put a 
	   wrapper around it so that the vulnerabilities are taken care of. Till then, this code needs  to be very careful
	   about accepting inputs from users and processing data anywhere in the code. ++ Supriyo Mitra.
    port = 8888; /* default port to listen to */
    data = (char *)malloc(MAX_SIZE * sizeof(char));
	proglang = (char *)malloc(20 * sizeof(char));
	ipaddr = (char *)malloc(16*sizeof(int)); 
	strcpy(ipaddr, "192.168.154.238"); /* SHOULD COME FROM CONFIG FILE */
	retval = (char *)malloc(100*sizeof(char));
	conn_backlogs = 5; /* default backlog connections */
	reuseaddr = 1; 
	/* By default we would allow the network service to be restarted when there are connections in the ESTABLISHED and TIME_WAIT state. */
	readconfig(ipaddr, &port, &conn_backlogs, &reuseaddr, &max_code_size);
	code = (char *)malloc(max_code_size * sizeof(char));
	code_enc = (char *)malloc(max_code_size * 4 * sizeof(char)); /* 4 times the max code size. This is pure speculation */

	sockfd = socket(AF_INET, SOCK_STREAM, 0);
	if(sockfd == -1){
		printf("Could not create socket errno=%d\n", errno); /* Please provide the reason for the error */
	}
	else{
		printf("Socket created successfully\n\n");
	}
	r = setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &reuseaddr, sizeof(reuseaddr));
	if(r == -1){
		printf("Socket could not be reused - %s. It's OK, we will carry on regardless.",strerror(errno));
	}
	printf("Socket could be reused successfully...\n");
	server.sin_family = AF_INET;
    server.sin_addr.s_addr = INADDR_ANY;
	
	server.sin_port = htons(port); 
	printf("Trying to bind the socket....\n\n");
	fflush(stdout);
    r = bind(sockfd, (struct sockaddr *)&server, sizeof(server));
	printf("r = %d",r);
	if(r < 0){
		printf("Bind to socket failed. errno=%d\n", errno);
		_exit(0);
	}
	printf("Successfully bound to the given address and port");
	fflush(stdout);
	listen(sockfd, conn_backlogs);
	while(1){ /* Take incoming connections */
	    sessfd = accept(sockfd, 0, 0); /* call blocks if there are no connections to accept. */
		if (sessfd == -1){
            if (errno==EINTR){
				continue;
			}
            printf("failed to accept connection (errno=%d)",errno);
			continue; /* Let us take a try with our next incoming connection. */
        }
		/* Now, if we could take the connection, we will fork of and let a child process to 
		handle the connection and let the parent process go back to accept more connections. */
		pid = fork();
		if(pid == -1){
			printf("fork call failed with error %d\n", errno);
			send_err_msg(errno);
			continue;
		}
		else if(pid == 0){ /* This is the child process. Close the socket descriptor */
		    close(sockfd);
			buffer = (char *)malloc(MAX_SIZE * sizeof(char));
			read_size = recv(sessfd, buffer, MAX_SIZE, 0);
			while (read_size > 0){
				strcat(data, buffer);
				read_size = recv(sessfd , buffer , MAX_SIZE , 0); 
				/* sessfd is our client socket descriptor, so we need to write the results of our operations through it. */
			}
			retlist = get_xml_data(data);
			b64decode(code_enc, &code);
			retval = handle_operation(sessfd, code, proglang); /* Handle the data using 'codequeue' in the function. */
			close(sessfd);
			_exit(0);
		}
		else{ /* Parent process */
		    close(sessfd);
		}
	}
	return(0);
}

/*
static const int B64index[256] = { 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 62, 63, 62, 62, 63, 52, 53, 54, 55,
56, 57, 58, 59, 60, 61,  0,  0,  0,  0,  0,  0,  0,  0,  1,  2,  3,  4,  5,  6,
7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,  0,
0,  0,  0, 63,  0, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51 };

char * b64decode(const void* data, const size_t len){
    unsigned char* p = (unsigned char*)data;
    int pad = len > 0 && (len % 4 || p[len - 1] == '=');
    const size_t L = ((len + 3) / 4 - pad) * 4;
    char * str(L / 4 * 3 + pad, '\0');

    for (size_t i = 0, j = 0; i < L; i += 4){
        int n = B64index[p[i]] << 18 | B64index[p[i + 1]] << 12 | B64index[p[i + 2]] << 6 | B64index[p[i + 3]];
        str[j++] = n >> 16;
        str[j++] = n >> 8 & 0xFF;
        str[j++] = n & 0xFF;
    }
    if (pad){
        int n = B64index[p[L]] << 18 | B64index[p[L + 1]] << 12;
        str[str.size() - 1] = n >> 16;

        if (len > L + 2 && p[L + 2] != '='){
            n |= B64index[p[L + 2]] << 6;
            str.push_back(n >> 8 & 0xFF);
        }
    }
    return str;
}
*/

void readconfig(char *ipaddr, int *port, int *backlogs, int *reuseaddr, int *max_code_size){
}

void send_err_msg(int errnum){
}

char * handle_operation(int sessfd, char *data, char *proglang){ /* NOTE: The 'data' is basically an XML chunk */
	char *return_val;
	return_val = (char *)malloc(1000*sizeof(char));
	strcpy(return_val, "successful");
	/* Do something to get the data to one of the running docker container images. Run it there. Get the output and return it back. */
	return(return_val);
}

/* 
   This function reads the XML data and returns the code as a return value. All other values provided as 
   arguments are changed and since they are all pointers, the changes are available outside the function.
*/
/*
void read_xml(char *data, int *user_id, int *test_id, int *challenge_id, char **code_enc, char **proglang){
	xmlChar *xmldoc;
	xmlDoc *document;
    xmlNode *root, *first_child, *node;
    xmlChar *key;
	xmldoc = xmlCharStrdup(data);
	document = xmlParseDoc(xmldoc);
	root = xmlDocGetRootElement(document);
    fprintf(stdout, "Root is <%s> (%i)\n", root->name, root->type);
    first_child = root->children;
    for (node = first_child; node; node = node->next) {
        fprintf(stdout, "\t Child is <%s> (%i)\n", node->name, node->type);
		if(!xmlStrcmp(node->name,"challenge_id")){
			key = xmlNodeListGetString(document, node->xmlChildrenNode, 1);
			*challenge_id = key;
		}
		else if(!xmlStrcmp(node->name,"user_id")){
			key = xmlNodeListGetString(document, node->xmlChildrenNode, 1);
			*user_id = key;
		}
		else if(!xmlStrcmp(node->name,"test_id")){
			key = xmlNodeListGetString(document, node->xmlChildrenNode, 1);
			*test_id = key;
		}
		else if(!xmlStrcmp(node->name,"code")){
			key = xmlNodeListGetString(document, node->xmlChildrenNode, 1);
			strcpy(*code_enc, key);
		}
		else if(!xmlStrcmp(node->name,"proglang")){
			key = xmlNodeListGetString(document, node->xmlChildrenNode, 1);
			strcpy(*proglang, key);
		}
    }
}
*/

char ** get_xml_data(char *xmldump){
	xmlChar *xmldoc;
    xmldoc = xmlCharStrdup(xmldump);
    xmlDoc *document;
    xmlNode *root, *first_child, *node;
    xmlChar *key;
	char **retlist;
	retlist = (char **)malloc(5 * sizeof(char[20000]));
    document = xmlParseDoc(xmldoc);
    root = xmlDocGetRootElement(document);
    fprintf(stdout, "Root is <%s> (%i)\n", root->name, root->type);
    first_child = root->children;
    for (node = first_child; node; node = node->next) {
		if(!xmlStrcmp(node->name,"challenge_id")){
				key = xmlNodeListGetString(document, node->xmlChildrenNode, 1);
				/*printf("Challenge Id: %s\n", key);*/
				*(retlist + 0) = key;
		}
		else if(!xmlStrcmp(node->name,"user_id")){
				key = xmlNodeListGetString(document, node->xmlChildrenNode, 1);
				/*printf("User Id: %s\n", key);*/
				*(retlist + 1) = key;
		}
		else if(!xmlStrcmp(node->name,"test_id")){
				key = xmlNodeListGetString(document, node->xmlChildrenNode, 1);
				/*printf("Test Id: %s\n", key);*/
				*(retlist + 2) = key;
		}
		else if(!xmlStrcmp(node->name,"code")){
				key = xmlNodeListGetString(document, node->xmlChildrenNode, 1);
				/*printf("Code: %s\n", key);*/
				*(retlist + 3) = key;
		}
		else if(!xmlStrcmp(node->name,"proglang")){
				key = xmlNodeListGetString(document, node->xmlChildrenNode, 1);
				/*printf("Programming Language: %s\n", key);*/
				*(retlist + 4) = key; 
		}
    }
	return(retlist);
}




void b64decode(char *code_enc, char **code){
}

