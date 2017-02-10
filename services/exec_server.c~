/* Utiity header files */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>
#include <sys/mman.h>
#include <inttypes.h>

/* POSIX threads library */
#include <pthread.h>

/* Networking libraries */
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/ioctl.h>

/* VIX Library */
#include "vix.h"

/* Data serialization libraries */
#include <json/json.h>
#include <json/json_tokener.h>

/* Some Constants */
#define NUM_THREADS 5
#define INI_LINE_SIZE 80 /* Do not want anybody to write a config param with more than these many chars */
#define MAX_QUEUE_LENGTH 1000
#define PORT_NUM 5555
#define QUEUE_SCAN_INTERVAL 10 /* tasksqueue will be scanned every 10 seconds until one or more entr(y|ies) appear(s) in it */
#define MAX_CONFIG_LINES 500
#define MAX_SLEEP_TIME 5 /* max sleep time is 5 seconds */
#define MAX_CODE_SIZE 1048576 /* 1 MB - that is the maximum supported length of a program. */
#define TRUE 1
#define MAX_ARGS_COUNT 20 /* We feel 20 arguments to a program created by the user should be enough */
#define MAX_ARG_LEN 4096 /* 4096 is the max length of the character string argument. Again, we consider this to be sufficient. */
#define MAX_LIST_SIZE 1000 /* Maximum number of concurrent VM instances that may be made available in the pool. */
/* In a production environment, this value may be increased to 10000. This should be a configurable value. */
#define MAX_INSTANCE_LIFE 3600/* Maximum time (in seconds) for which the instance will exist before being purged by the system. */
/* Again, this should be a configurable value, so it should ideally come from the config file. For now, we define it as a constant. */
#define MAX_VM_TR_QUEUE_LEN 5 /* This is the maximum number of task requests that can be queued for any existing VM */
#define MGR_RR_INTRVL 5

/* Some VMWare instance specific values. All of these should be moved to the config file when it gets implemented in version 2.0 */
#define MAX_INSTANCE_NAME_LEN 40 /* Maximum length (in chars) of the size of an instance name. */
#define CPU_CORES_COUNT 2 /* This is the minimal value of the number of cores in the CPU. This should be a configurable option. */
#define MAX_PRIMARY_MEMORY 1 /* Maximum amount of RAM in gigabytes. This should be a configurable option. */
#define MAX_HARD_DISK_SIZE 40 /*Maximum amount of space (in Gigs) available on hard disk. Should be a configurable option. */
#define MAX_NETWORK_IFACE_CARD_COUNT 1 /* There will be a single NIC for each VM instance */

#define MAX_VM_INSTANCES_LIN = 10
#define MAX_VM_INSTANCES_WIN = 5

/* Constants pertaining to base64 encoding and decoding operations */
#define WHITESPACE 64
#define EQUALS     65
#define INVALID    66

/*
The Base64 encoding and decoding code is based heavily on the code available at
"http://stackoverflow.com/questions/342409/how-do-i-base64-encode-decode-in-c". 
Some changes have been made to it to satisfy the needs of the application in 
which it is being used. I thank the creator of this code. My understanding is that
this code is in the freeware domain (since any bit of code posted on stackoverflow
may be used without explicit permission of its creator). However, should the creator
expect any monetary benefit for this code from me, I would be glad to satisfy that.
-- S.
*/

/*
This program is a server application that waits for requests to come to it, and it executes the code sent
in the request on the environment specified in the request. The output is sent back to the requestor and the
connection is closed after that. It will maintain a queue of requests that arrive before it can handle the
current request. Each request is executed in a thread that picks up the requests from a queue populated by
the parent process.

-- S.
*/

/* Geez! Some boring stuff */
static char encoding_table[] = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
                                'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
                                'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
                                'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f',
                                'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
                                'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
                                'w', 'x', 'y', 'z', '0', '1', '2', '3',
                                '4', '5', '6', '7', '8', '9', '+', '/',
				'='};

static const unsigned char d[] = {
    66,66,66,66,66,66,66,66,66,66,64,66,66,66,66,66,66,66,66,66,66,66,66,66,66,
    66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,62,66,66,66,63,52,53,
    54,55,56,57,58,59,60,61,66,66,66,65,66,66,66, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
    10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,66,66,66,66,66,66,26,27,28,
    29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,66,66,
    66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,
    66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,
    66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,
    66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,
    66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,66,
    66,66,66,66,66,66 };
/* Got over with it. There should be a better way to do this. */

/* Now need to create some self referential structures.... I love them. */
typedef struct taskrequest{
	char* code;
	char* targetenv;
	char** codeargs;
	char* client_ip;
	char* client_port;
}taskrequest;


typedef struct node{
	char *data; /* Serialized JSON data representing "taskrequest" */
	struct node *next;
	struct node *previous;
}node;


typedef struct queue{
	struct node *front;
	struct node *back;
	int nodescount;
}queue;


typedef struct vminstance{
	int cpucores; /* Number of CPU cores available */
	int memory; /* This is the amount of primary memory available (in Gigs) */
	int harddiskmem; /* Amount of hard disk space available (in Gigs) */
	int nic_count; /* Number of network interface cards available on this instance */
	char **ip_addresses; /* Available IP addresses on the NICs */
	int state; /* Status of the instance - 0 is inactive (switched off), 1 is active (switched on and running), 2 is active but in hibernation */
	char *os; /* Operating system of the instance */
	char **envslist; /* list of programming environments available on the instance */
	char *privilege; /* privileges of the user logged into the system - default will be 'root' on linux/unix systems and 'administrator' on windows systems.  */
	long int create_timestamp; /* Unix/Linux timestamp (seconds) at which the instance was created. */
	int inuse; /* Whether the VM instance is currently being used by a client request or not. */
	/* If the value is TRUE, then the instance will not be purged immediately. The purging agent will wait for the value to become FALSE. */
	taskrequest **trqueue; /* Pointer to a list of pointers to taskrequest objects. This is the queue of requests that this instance has to handle. */
	int trqueuelen; /* Length of the above queue of taskrequest objects. */
}vminstance;


typedef struct vminstancepool{
	vminstance *instance_list[MAX_LIST_SIZE]; /* A list of pointers to VM instances */
	int cur_instance_count; /* Number of concurrent instances available at the current instant */
	int cur_instances_in_use; /* Number of the available instances that are actually in use at the current instant */
}vminstancepool;
/* Structs are over */

queue *tasksqueue = NULL;
/* Supported queue operations: insert (from back), delete (from front), traverse_bf (traverse from back to front), traverse_fb (traverse from front to back */
/* Note: At this point we haven't defined 'traverse_bf' and 'traverse_fb'. We will implement them if and when required. */
int lock_flag = 0;

vminstancepool *vmpool; /* This is the global pool of VM instances. We initialize it as an empty pool */

/* Function to handle addition of a node at the back of the queue. */
node *insert(char *d){
    node *qnode;
    if(tasksqueue == NULL){
	tasksqueue = (queue *)malloc(sizeof(queue));
        tasksqueue->front = (node *)malloc(sizeof(node));
	tasksqueue->back = (node *)malloc(sizeof(node));
	tasksqueue->front = NULL;
	tasksqueue->back = NULL;
	tasksqueue->nodescount = 0;
    }
    printf("Adding task in tasksqueue\n");
    qnode = (node *)malloc(sizeof(node));
    qnode->next = (node *)malloc(sizeof(node));
    qnode->previous = (node *)malloc(sizeof(node));
    qnode->data = (char *)malloc(strlen(d) * sizeof(char));
    strcpy(qnode->data, d);
    if(tasksqueue->back != NULL){
        (tasksqueue->back)->previous = qnode;
        qnode->next = tasksqueue->back;
        tasksqueue->back = qnode;
		qnode->previous = NULL;
    }
    else{
        qnode->next = NULL;
        qnode->previous = NULL;
        tasksqueue->back = qnode;
        tasksqueue->front = qnode;
	printf("TASK QUEUE FRONT IS SET TO QNODE: %s\n", tasksqueue->front->data);
    }
    tasksqueue->nodescount++;
    printf("Added task in tasks queue: %d\n", tasksqueue->nodescount);
    return (qnode);
}

/* Function to handle the deletion of a node from the front of the queue. */
node* delete(){
    node *qprev, *delnode;
    qprev = (node*)malloc(sizeof(node));
    delnode = (node *)malloc(sizeof(node));
    printf("Deleting node...\n");
    if(tasksqueue == NULL){
	return (NULL);
    }
    if(tasksqueue->front == NULL){ /* This can be NULL only when there are no nodes in the tasksqueue. */
	tasksqueue->back = NULL; /* Hence, the back pointer should be NULL as well. */
	return(NULL);
    }
    printf("Manipulating pointers for deletion...\n");
    qprev = (tasksqueue->front)->previous;
    delnode = tasksqueue->front;
    tasksqueue->front = qprev;
    printf("tasksqueue nodes count = %d\n", tasksqueue->nodescount);
    if(qprev != NULL){
        qprev->next = NULL;
        qprev->previous = (node *)malloc(sizeof(node));
    }
    delnode->previous = NULL;
    tasksqueue->nodescount--;
    if(tasksqueue->nodescount == 0){ /* If the number of nodes is 0, then there are no front or back nodes. */
	tasksqueue->front = NULL;
	tasksqueue->back = NULL;
    }
    printf("Deleted node successfully.\n");
    return (delnode);
}


int base64decode (char *in, size_t inLen, char *out, size_t *outLen){
    char *end = in + inLen;
    char iter = 0;
    uint32_t buf = 0;
    size_t len = 0;
    while(in < end){
        char c = d[*in++];
	/* printf("C INTEGER = %d\n", c); */
	if(c == WHITESPACE){
	    continue;/* skip whitespace */
	}
	else if(c == INVALID){
	    out = "";
	    return(1);/* invalid input, return error */
	}
	else if(c == EQUALS){
	    in = end;
	    continue;
	}
	else{
	    buf = buf << 6 | c;
	    iter++; // increment the number of iteration
	    /* If the buffer is full, split it into bytes */
	    if (iter == 4) { 
	        if ((len += 3) > *outLen) return 1; /* buffer overflow */
	        *(out++) = (buf >> 16) & 255;
	        *(out++) = (buf >> 8) & 255;
	        *(out++) = buf & 255;
	        buf = 0; iter = 0;
	    }
	}
    } /* End of while loop */

    if (iter == 3) {
        if ((len += 2) > *outLen) return 1; /* buffer overflow */
        *(out++) = (buf >> 10) & 255;
        *(out++) = (buf >> 2) & 255;
    }
    else if (iter == 2) {
        if (++len > *outLen) return 1; /* buffer overflow */
        *(out++) = (buf >> 4) & 255;
    }
    *outLen = len; /* modify to reflect the actual output size */
    return 0;
}


char *remove_char_from_str(char ch, char *str){
    char *newstr;
    int ctr, len, newctr;
    len = strlen(str);
    ctr = 0;
    newctr = 0;
    newstr = (char *)malloc(len * sizeof(char));
    while(ctr < len){
	if(*(str + ctr) == ch){	
	    ctr++;
	}
	else{
	    *(newstr + newctr) = *(str + ctr);
	    newctr++;
	    ctr++;
	}
    }
    *(newstr + newctr) = '\0';
    return(newstr);
}

/* Forward Decarations */
char * executeCodeOnVM(taskrequest *, int, int, char **);
int returnResultToRequestorPage(taskrequest *, char *);
vminstance *lookupSuitableVMinPool(taskrequest *);
vminstance *createNewVmInstance(taskrequest *, int , int , char **);

/* 
This function takes an entry from the task requests queue 'tasksqueue', runs
the code in a virtual environment, gathers the results, and returns it back 
to the caller function.
*/
char * processTasks(int threadctr){
	/* Get the node from the front of the queue */
	node *codenode;
	char *exec_code;
        char *enc_code;
	char *code_resp;
	char *task_info;
	int s = 0;
	int p, status;
	json_object * jobj;
	taskrequest *tr;
	char *progenv, *client_ip, *client_port;	
	/* FILE *fp;
        fp = fopen("/tmp/mainlogger.log", "a+"); */
	codenode = (node *)malloc(sizeof(node));
        if(lock_flag == 0){
	    lock_flag = 1;
	    codenode = delete();
	    lock_flag = 0;
        }
	else{
	    codenode = NULL;
	    lock_flag = 0;
	}
        while(TRUE){
	while(codenode == NULL){
	    printf("No code to process.\nThread %d is Going to sleep for %d seconds.\n", threadctr, MAX_SLEEP_TIME);
	    s = sleep(MAX_SLEEP_TIME); /* If s is 0, then the program slept for the given time interval */
	    /* printf("lock_flag = %d, s = %d\n", lock_flag, s); */
	    if(lock_flag == 0){
		lock_flag = 1;
		codenode = delete();
		lock_flag = 0;
		if(codenode){
		    printf("Codenode is NOT NULL in thread %d\n", threadctr);
		}
		else{
		    printf("Codenode is NULL in thread %d\n", threadctr);
		}
	    }
	}

	/* printf("Nodes in tasks queue: %d\n======================\n", tasksqueue->nodescount);
	printf("Found code in tasksqueue... Processing it.\n"); */
	if(!codenode){
	    continue;
	}
	else{
	    task_info = (char *)malloc((strlen(codenode->data) + 1)*sizeof(char));
	    strcpy(task_info, codenode->data);
	    /*printf("codenode DATA in thread %d = %s\n", threadctr, task_info); */
	}
	jobj = json_tokener_parse(task_info);
	/* printf("JOBJ created in thread %d\n", threadctr); */
	json_object_object_foreach(jobj, key, val){
	    val = json_object_to_json_string(val);
	    printf("\nKEY = %s, VAL = %s\n", key, val);
	    val = remove_char_from_str('"', val);
	    if(!strcmp(key, "enc_code")){
		enc_code = (char *)malloc((strlen(val) + 1) * sizeof(char));
		strcpy(enc_code, val);
		/*fprintf(fp, "%s", enc_code);*/
		continue;
	    }
	    if(!strcmp(key, "code_env")){
		progenv = (char *)malloc((strlen(val) + 1) * sizeof(char));
		strcpy(progenv, val);
		/*fprintf(fp, "%s", progenv);*/
		continue;
	    }
	    if(!strcmp(key, "client_ip")){
		client_ip = (char *)malloc((strlen(val) + 1) * sizeof(char));
		strcpy(client_ip, val);
		/*fprintf(fp, "%s", client_ip);	*/
		continue;
	    }
	    if(!strcmp(key, "client_port")){
		client_port = (char *)malloc((strlen(val) + 1) * sizeof(char));
		strcpy(client_port, val);
		/*fprintf(fp, "%s", client_port);  */ 
		continue;                                                   
	    }
	}
	/* Create a taskrequest instance out of the above data. */
	tr = (taskrequest *)malloc(sizeof(taskrequest));
	
	/* fclose(fp); */
	/* if codenode is not NULL, get the base64 encoded code snippet from the node's data element */
	p = MAX_CODE_SIZE;
	exec_code = (char *)malloc(MAX_CODE_SIZE * sizeof(char));
 	/* printf("EXEC CODE INIT WITH %d\n", MAX_CODE_SIZE); */
	printf("ENC_CODE = %s\n",enc_code);
	status = base64decode(enc_code, strlen(enc_code), exec_code, &p);
	printf("STATUS CODE = %d\n",status);
    	printf("EXEC CODE = %s\n",exec_code);
	/* 
	***********************************************************************************************************
	***** TO DO: CHECK THE VALUE OF exec_code HERE. MALICIOUS CODE SHOULD BE TAKEN CARE OF AT THIS POINT ******
	***********************************************************************************************************
	*/
	tr->code = (char *)malloc((strlen(exec_code) + 1) * sizeof(char));
	strcpy(tr->code, exec_code);
	tr->targetenv = (char *)malloc((strlen(progenv) + 1) * sizeof(char));
	strcpy(tr->targetenv, progenv);
	tr->client_port = (char *)malloc((strlen(client_port) + 1) * sizeof(char));
	strcpy(tr->client_port, client_port);
	tr->client_ip = (char *)malloc((strlen(client_ip) + 1) * sizeof(char));
	strcpy(tr->client_ip, client_ip);
	tr->codeargs = (char **)malloc(MAX_ARGS_COUNT * sizeof(char *));
	for(int i=0; i < MAX_ARGS_COUNT; i++){
	    tr->codeargs[i] = (char *)malloc(MAX_ARG_LEN * sizeof(char));
	}
	if(lock_flag == 0){
	    lock_flag = 1;
	    codenode = delete();
	    lock_flag = 0;
	}
	else{
	    codenode = NULL;
	}
	/* 
	Now we have the code, so prepare the virtual machine instance where the code needs to be executed.
	The virtual machine instance needs to know the programming environment that needs to be loaded. It
	should also handle all dependencies and external libraries that are necessary to run the code.
	*/
	code_resp = executeCodeOnVM(tr, 2, 4, NULL); /* Empty set of IP addresses */
	printf("PAST VM CREATION....\n");
	returnResultToRequestorPage(tr, code_resp);
        }/* while(TRUE) ends */
    return ("Terminating thread\n");
}


/* 
Function to create a virtual machine instance with the environment specified in the 
taskrequest struct variable. It will have a default value for memory and CPU cores, but
these may be set by explicitly specifying a value for each of them. Once the VM is set
up, we will execute the code on it and return the response/error/whatever. THe resuts
of the executed program will be returned in case it runs successfully, otherwise the 
error message will be returned. 
*/
char *executeCodeOnVM(taskrequest *trqst, int cpucores, int hdmemgigs, char **ip_addresses){
    	char *resp;
	vminstance *vm; /* Pointer to a suitable VM found in the vmpool for this task request. */
	vm = (vminstance *)malloc(sizeof(vminstance));
	/* First thing - search the virtual machines pool for a machine with similar environment. */
	vm = lookupSuitableVMinPool(trqst); /* This will look up for a suitable VM instance in the global VM Pool. */
	if(!vm || vm == NULL){ /* No suitable VM instance object is found. So we need to create a brand new one. */
	    vm = createNewVmInstance(trqst, cpucores, hdmemgigs, ip_addresses);
	    if(vm != NULL){
		printf("VM Created Successfully!");
	    }
	    else{ /* VM could not be created - take appropriate action here. Need to decide what the appropriate action should be. */
	    }
	}
	else{ /* We already have a suitable VM instance available. So let us check what the size of its taskrequest queue is. */
	    if(vm->trqueuelen < MAX_VM_TR_QUEUE_LEN){ /* Let us add our taskrequest to its queue. */
	    }
	    else{ /* This VM instance has already got its plate filled up. So we need to create a new VM instance for our task request. */
		vm = createNewVmInstance(trqst, cpucores, hdmemgigs, ip_addresses);
		if(vm != NULL){
		    printf("VM Created Successfully!");
		}
		else{ /* VM could not be created - take appropriate action here. Need to decide what the appropriate action should be. */
		}
	    }
	}
    	resp = (char *)malloc(1024 * sizeof(char));
    	strcpy(resp, "success");
    	return(resp);
}


/*
This will return the response of the executed code to the requestor
socket identified by the IP address and the port number specified in the
taskrequest variable.
*/
int returnResultToRequestorPage(taskrequest *trqst, char *response){
    printf("Resuts returned Successfully!");
    return(0);
}

/*
Create a new 'vminstance' object and return a pointer to it. Once the creation of the instance is
successful, it is added to the global 'vmpool' and also the 'trqueue' attribute of the vminstance
object is updated  with the taskrequest object for which it has been created.

Note: We need a way to 'add' and 'delete' taskrequest objects from the vminstance's 'trqueue' attribute.
Functions with the same names ('add' and 'delete') will perform these actions.
*/
vminstance *createNewVmInstance(taskrequest *trqst, int cpucores, int hdmemgigs, char **ip_addresses){
    vminstance *vminst;
    vminst = (vminstance *)malloc(sizeof(vminstance));
    return(vminst);
}


/*
Look up for a suitable virtual machine in the global VM instance pool pointed to by 'vmpool'.
The argument is a pointer to the taskrequest object in question. The return value is a pointer
to a 'vminstance' object. If a valid VM instance object is found, a pointer to that is returned.
If no such instance object is found, NULL is returned.
*/
vminstance *lookupSuitableVMinPool(taskrequest *trqst){
}

/*
This function manages the entries in 'vmpool'. Will work on a separate thread of its own.
This will work as a manager to see to it that the number of VM instances do not go down
beneath a certain limit and if necessary, it will also terminate some instances that are
running beyond a stipulated frame of time. This thread will be spawned as soon as the 
server is launched.
*/
int manageVMInstances(){
    vminstance **vms; /* A list of pointers to virtual machines that will be part of the instance pool. */
    vminstance *vminst; /* pointer to a single vm instance in the pool. */
    char **envlist; /* Pointers to a list of environments */
    char *env;
    int *forkretval;
    int pid;
    char *software_resources[] = {"C" , "/usr/bin/gcc", \
                         "Perl" , "/usr/bin/perl", \
                         "Python" , "/home/supriyo/work/testyard/pyenv/bin/python", \
                         "Python3" , "", \
                         "Ruby" , "/usr/local/bin/ruby", \
                         "Curl" , "/usr/bin/curl", \
                         "Bash" , "/bin/bash", \
                         "Cshell" , "/bin/csh", \
                         "C++" , "/usr/bin/g++", \
                         "C#" , "/usr/bin/mono", \
                         "F#" , "/usr/bin/fsharp", \
                         "Go" , "/usr/bin/go", \
                         "Java" , "/usr/bin/java", \
                         "JavaScript" , "/usr/bin/js", \
                         "Lua" , "/usr/local/bin/lua", \
                         "Objective-C" , "/usr/bin/clang", \
                         "PHP" , "/usr/bin/php5", \
                         "VB.NET" , "", \
                         "VBScript" , "", \
                         "Pascal" , "/usr/local/bin/fpc", \
                         "Fortran" , "/usr/bin/gfortran", \
                         "Lisp" , "", \
                         "SmallTalk" , "", \
                         "Scala" , "", \
                         "Tcl" , "/usr/bin/tclsh", \
                         "Ada95" , "", \
                         "Delphi" , "", \
                         "Rust" , "", \
                         "Scheme" , "", \
                         "Swift" , "", \
                         "ColdFusion" , ""};
    envlist = (char **)malloc(MAX_LIST_SIZE * sizeof(char));
    vms = (vminstance **) malloc(MAX_LIST_SIZE * sizeof(int)); /* Pointers are integers, so we initialize them as such. */
    forkretval = (int *)malloc(MAX_LIST_SIZE * sizeof(int));
    /* Now create each VM instance with one of the supported environments. Besides installing that we
       will also install frequently used modules that are part of the programming environments. 
       Since at this point of time, the user or test creator cannot choose the OS, we will install
       "Ubuntu" for all non-microsoft technology applications, and "Windows7" for all Microsoft
       technology apps. So, in the case of creation, we will create 2 VM instances at a time, one for
       'Ubuntu Linux (14.0498)' and another for 'Windows 7'.
    */
    for(int i=0; i < MAX_LIST_SIZE; i++){
	*(vms + i) = (vminstance *)malloc(sizeof(vminstance));
        vminst = *(vms + i); /* Pointer to a single VMWare guest instance */
	*(envlist + i) = (char *) malloc(MAX_INSTANCE_NAME_LEN * sizeof(char));
	env = *(envlist + i);
	/* 
	   Note: I am considering vmware player for this functionality. We can create a VMWare player
	   instance with a certain environment automatically, and use it for our purposes. This will
	   be lightweight and since we are only going to use it to test code written by test takers, we
	   don't need an enterprise class machine. We can preconfigure vmware player instances for all
	   supported environments. In order to handle a surge in connections, there can be multiple
	   instances of identical vmware player running concurrently, each having a task queue of its 
	   own. The vmware player instances will be launched automatically by the code here.

	   Another Thought: We can have a number of preconfigured VMWare Player instances in a pool and 
	   each of them will contain all linux programming environments or windows programming environments.
	   That way, each instance will be able to keep a queue with various programming environments.
	   Every such instance will have a max lifetime value, after which they will be purged and a new
	   instance created in its place. The list of task requests (queue) belonging to the new instance
	   will be automatically transferred to the newly created instance. The number of such instances
	   operating at any given instance will be a configurable value set in the config file.

	   This method will possibly be the fastest way to execute code. The reason is that it eliminates
	   the time required to create a virtual machine when a request comes to the webserver. All it
	   would need is to start up the VM Player for the first time when a request comes to the app or
	   once a newly created  server is started after purging a running server.In all other cases, the
	   only activity the VM has to do is execute the given code in an appropriate 
	   
	   In the above scheme, purging means shutting down the server and rebooting it again to perform
	   the desired activities. The shutting down and rebooting will eliminate chances ofrunning malicious
	   code on the VM.

	   S.
        */
	/* Fork a child process here... this will run the python code to create the VMs. */
	pid = fork();
	if(pid == 0){ /* Child process. First connect to the ESXi server host. */
	}
	else{ /* Parent process. This needs to do nothing special. It should simply go to the next iteration. */
	    *(forkretval + i) = pid;
	}
    }
    return (0);
}

/* =========================================================================================

How a virtual machine pool will help performance: For every request for a vm instance, we will
first search the instances existing in the pool. If an appropriate instance is found, the 
request will make use of it. It will check whether it is in use at the current instant, and if
so, it will wait till it becomes free. An existing virtual machine instance may have a queue of
jobs waiting to be executed by the machine. Hence, a new job looking for an appropriate VM will
lodge itself behind the existing queue. The length of the queue will have a pre-determined max
value (let us call it MAX_VM_TR_QUEUE_LEN). If the new job 'sees' that length of the queue is
already equal to the MAX_VM_TR_QUEUE_LEN value, a new virtual machine will be created and it
will make use of it (by adding itself in its queue).

This will save the expensive overhead of creating a virtual machine every time a request comes 
in. A thread of this program will keep an eye on the existing VMs and if a VM passes the stipulated
lifetime, it would be purged by the thread. (If there is a job that is using the VM at the current
moment, the purging thread will wait for it to complete before destroying it. Its queue of jobs
will be transferred to the new machine instance.)

There will be a few corner cases, and we will deal with them as and when we come across them.

In case no appropriate VMs are available, a new VM will be created with the parameters specified
in the request, and it will be added to the pool before user's program can make use of it.

 S.
============================================================================================== */


int main(int argc, char** argv){
  pthread_t threadid = 0;
  int threadctr = 0;
  pthread_t* threadlist;
  pthread_t pool_mgr_thread; /* This thread will manage the virtual machine instance pool. */
  int mgr_thread_retval;
  /*
  The above thread will do the following: 
  1. Purge a virtual machine instance if the lifetime of the instance exceeds the MAX_INSTANCE_LIFE value.
  
  The rationale behind doing this is to destroy the environment in which any malicious bit of code has been 
  executed.
  2. This thread will keep checking all virtual machine instances in a round robin method, with a time interval
  of MGR_RR_INTRVL seconds.
  */
  vmpool = (vminstancepool *)malloc(sizeof(vminstancepool)); 
  mgr_thread_retval = pthread_create(&pool_mgr_thread, NULL, manageVMInstances, NUM_THREADS+10);
  
  int listenfd = 0, connfd = 0;
  struct sockaddr_in serv_addr, cli_addr;
  char recvBuff[1048576]; /* 1 MB - that is the maximum supported length of a program. */
  int nchars, size;
  char * progstatus;
  vminstancepool *vinstpool;
  char ***configparams;
  /* configparams = readinifile(); */
  /* json_object *jvalue; */
  int taskctr = -1;
  int ret[NUM_THREADS];
  node *nd;
  FILE *fp;
  fp = fopen("/tmp/exec_server.log", "w+");
  threadlist = (pthread_t*)malloc(NUM_THREADS*sizeof(pthread_t));
  
  while(threadctr < NUM_THREADS){
      ret[threadctr] = pthread_create( &threadlist[threadctr], NULL, processTasks, threadctr);
      if (ret[threadctr]){ /* thread creation failed */
	 printf("thread creation failed!\n");
      }
      else{
	 printf("Created thread with Id %d\n", threadlist[threadctr]);
	 threadctr++;
      }
  }
  /* Main thread - Open a socket and listen for task requests, thereby filling up the tasksqueue */
  listenfd = socket(AF_INET, SOCK_STREAM, 0);
  if(listenfd < 0){
      printf("Socket creation failed");
      lock_flag = 0;
      return 1;
  }
  memset(&serv_addr, '0', sizeof(serv_addr));

  serv_addr.sin_family = AF_INET;
  serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);
  serv_addr.sin_port = htons(PORT_NUM);

  bind(listenfd, (struct sockaddr*)&serv_addr, sizeof(serv_addr));
  listen(listenfd, 10);
  size = sizeof (cli_addr);
  printf("listening for incoming connections...\n");
  while(TRUE){
      connfd = accept(listenfd, (struct sockaddr*) &cli_addr, &size);
      if(connfd < 0){
	  printf("Could not accept incoming connection");
	  continue;
      }
      else{
	  printf("Accepted incoming connection... \n");
      }
      memset(recvBuff, 0, strlen(recvBuff)); /* Flush the earlier value */
      printf("Receiving incoming connections...\n");
      nchars = read(connfd, recvBuff, MAX_CODE_SIZE - 1);
      printf("Read data from incoming connection.\n");
      if(nchars == 0){ /* no data received */
	  printf("No data received\n");
	  continue;
      }
      /* recvBuff will contain JSON string which we need to parse before storing in tasksqueue */
      printf("Data Received: %s\n", recvBuff);
      /* recvBuff will be placed on the queue. */
      while(lock_flag){
          sleep(1);
      }
      nd = insert(recvBuff); /* A global queue of tasks */
  }
}


char ***readinifile(){
	char *str;
	FILE *fp;
	char ***configtable;
	char *param, *value;
	int foundequalsign = 0, j = 0, i = 0;
	int linenum = 0;
	fp = fopen( "localSandbox.ini" , "r");
	configtable = malloc(MAX_CONFIG_LINES * sizeof(char *));
	if (fp) {
		str = (char *)malloc(INI_LINE_SIZE * sizeof(char));
		while (fscanf(fp, "%s", str)!=EOF){
			if(*str == ' ' || *str == '#'){ /* if a line starts with a space or '#' character, then skip it. */
			   continue;
			}
			/* printf("%s",str); */
		    /* Want a new set of memory area every time I read a line */
			param = (char *)malloc(60*sizeof(char));
			value = (char *)malloc(20*sizeof(char));
			foundequalsign = 0;
			j = 0;
			for(i=0; i < strlen(str); i++){
				if(!foundequalsign && *(str + i) != '=' && *(str + i) != ' '){
					*(param + i) = *(str + i);
				}
				else if(*(str + i) == '='){
					*(param + i) = '\0';
					foundequalsign = 1;
					j = 0;
				}
				else if(*(str + i) == ' '){ /* Ignore space characters in config lines */
					continue;
				}
				else if(foundequalsign){
					*(value + j++) = *(str + i);
				}
			}
			*(value + j) = '\0';
			*(configtable + linenum) = malloc(2 * sizeof(int));
			**(configtable + linenum + 0) = (char *)malloc(strlen(param) * sizeof(char));
			**(configtable + linenum + 1) = (char *)malloc(strlen(value) * sizeof(char));
			strcpy(**(configtable + linenum + 0), param);
			strcpy(**(configtable + linenum + 1), value);
			linenum++;
		}
		fclose(fp);
	}
	return(configtable);
}




/*
Compilation and execution process:
$ gcc -Wall exec_server.c -l json -lpthread -std=c99 -o exec_server
./exec_server <Enter>

Reading materials:
------------------

http://www.cs.rpi.edu/~moorthy/Courses/os98/Pgms/socket.html
http://stackoverflow.com/questions/2354014/socket-programming-recv-read-issue
http://www.thegeekstuff.com/2011/12/c-socket-programming/?utm_source=feedburner
http://sanbarrow.com/vmx.html
http://stackoverflow.com/questions/792764/secure-way-to-run-other-people-code-sandbox-on-my-server
https://linuxprograms.wordpress.com/category/json-c/
	
https://github.com/json-c/json-c
On Debian, Ubuntu or Linux Mint:
$ sudo apt-get install libjsoncpp-dev

On Fedora or CentOS/RHEL 7 or higher:
$ sudo yum install jsoncpp-devel 
-- S.
*/
