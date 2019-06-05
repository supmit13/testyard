/*
Compile Command: gcc -o listener listener.c
*** gcc -Wall -o listener $(xml2-config --cflags) $(xml2-config --libs) listener.c  -I/usr/include/libxml2  -lxml2 

In order to run the above code, you need to install the following libraries using apt-get (on Ubuntu/Debian systems):
apt-get install libxml2
apt-get install libxml2-dev

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
#include <stdint.h>
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

    /* 
       I will be using 'malloc' very heavily here though I understand its vulnerabilities. Later on, I would put a 
       wrapper around it so that the vulnerabilities are taken care of. Till then, this code needs  to be very careful
       about accepting inputs from users and processing data anywhere in the code. ++ Supriyo Mitra. 
    */
    port = 8888; /* default port to listen to */
    data = (char *)malloc(MAX_SIZE * sizeof(char));
	proglang = (char *)malloc(20 * sizeof(char));
	ipaddr = (char *)malloc(16*sizeof(int)); 
	strcpy(ipaddr, "192.168.154.238"); /* SHOULD COME FROM CONFIG FILE */
	retval = (char *)malloc(100*sizeof(char));
	conn_backlogs = 5; /* default backlog connections. THIS SHOULD COME FROM CONFIG. */
	reuseaddr = 1; 
	/* 
	By default we would allow the network service to be restarted when there are connections in the ESTABLISHED and TIME_WAIT state.
	 */
	readconfig(ipaddr, &port, &conn_backlogs, &reuseaddr, &max_code_size);
	code = (char *)malloc(max_code_size * sizeof(char));
	code_enc = (char *)malloc(max_code_size * 4 * sizeof(char)); /* 4 times the max code size. This is pure speculation */

	sockfd = socket(AF_INET, SOCK_STREAM, 0);
	if(sockfd == -1){
		printf("Could not create socket errno=%d\n", errno); /* Please provide the reason for the error */
	}
	else{
		printf("Socket created successfully\n\n"); /* We are fine. */
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
	printf("r = %d\n",r);
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

/* Base64 decoding code starts here. */
static char encoding_table[] = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
                                'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
                                'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
                                'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f',
                                'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
                                'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
                                'w', 'x', 'y', 'z', '0', '1', '2', '3',
                                '4', '5', '6', '7', '8', '9', '+', '/'};
static char *decoding_table = NULL;

unsigned char *base64_decode(const char *data, size_t input_length, size_t *output_length) {
 
    if (decoding_table == NULL) build_decoding_table();
 
    if (input_length % 4 != 0) return NULL;
 
    *output_length = input_length / 4 * 3;
    if (data[input_length - 1] == '=') (*output_length)--;
    if (data[input_length - 2] == '=') (*output_length)--;
 
    unsigned char *decoded_data = malloc(*output_length);
    if (decoded_data == NULL) return NULL;
 
    for (int i = 0, j = 0; i < input_length;) {
 
        uint32_t sextet_a = data[i] == '=' ? 0 & i++ : decoding_table[data[i++]];
        uint32_t sextet_b = data[i] == '=' ? 0 & i++ : decoding_table[data[i++]];
        uint32_t sextet_c = data[i] == '=' ? 0 & i++ : decoding_table[data[i++]];
        uint32_t sextet_d = data[i] == '=' ? 0 & i++ : decoding_table[data[i++]];
 
        uint32_t triple = (sextet_a << 3 * 6)
        + (sextet_b << 2 * 6)
        + (sextet_c << 1 * 6)
        + (sextet_d << 0 * 6);
 
        if (j < *output_length) decoded_data[j++] = (triple >> 2 * 8) & 0xFF;
        if (j < *output_length) decoded_data[j++] = (triple >> 1 * 8) & 0xFF;
        if (j < *output_length) decoded_data[j++] = (triple >> 0 * 8) & 0xFF;
    }
 
    return decoded_data;
}
 

void build_decoding_table() {
 
    decoding_table = malloc(256);
 
    for (int i = 0; i < 64; i++)
        decoding_table[(unsigned char) encoding_table[i]] = i;
}
 
 
void base64_cleanup() {
    free(decoding_table);
}
/* Base64 decoding code ends here */

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

