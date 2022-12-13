/*  
compile command: gcc testxml.c -o testxml -lexpat 
*/
#include <expat.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define MAX_SIZE 20


struct setting {
    const char *key;
    char *value;
} config[] = {
    {"user_id", NULL}, {"test_id", NULL}, {"challenge_id", NULL}, {"code" , NULL}, {"proglang" , NULL}
};

struct setting *current_setting;

char *tagstack[MAX_SIZE];
int tagctr = 0;

int key_cmp(void const *ld, void const *rd){
	int retval = 1;
    struct setting const *const l = ld;
    struct setting const *const r = rd;
	/*
	printf("#### l = %s\n",l->key);
	printf("#### r = %s\n",r->key);
	*/
	if(tagctr < MAX_SIZE){
		tagstack[tagctr] = (char *)malloc(40*sizeof(char)); 
	}
    retval = strcmp(l->key, r->key);
	if(!retval){
		return(retval);
	}
    strcpy(tagstack[tagctr],l->key);
	printf("3##############TAGCSTACK = %s, %d\n", tagstack[tagctr], tagctr);
	
	int i;
	for(i=0; i < tagctr; i++){
		retval = strcmp(r->key, tagstack[i]);
		if(!retval){
			return(retval);
		}
	}
	/*
	if(retval){
		return(retval);
	}
	*/
	return(-1);
}

void XMLCALL handler(void *userData, const XML_Char *s, int len){
    if(len == 0){
        return;
    }

    if(!current_setting){
        return;
    }

    char *value = malloc((len+1) * sizeof(XML_Char));
    strncpy(value, s, len);
	/* printf("VALUE ==== %s\n",value); */
    current_setting->value = value;
}

static void XMLCALL startElement(void *userData, const char *name, const char **atts){
    struct setting key = { .key = name };
	/* printf("###########Size: %lu\n",sizeof(config)/sizeof(config[0]));
	printf("NAME ---- %s\n",name);
	 printf("KEY ---- %s\n",key); */
    current_setting = bsearch(&key, config, sizeof(config)/sizeof(config[0]), sizeof(config[0]), key_cmp);
	tagctr++;
}

static void XMLCALL endElement(void *userData, const char *name){
    current_setting = NULL;
}

int main(int argc, char *argv[]){
    char buf[BUFSIZ];

    XML_Parser parser = XML_ParserCreate(NULL);

    int done;
    int depth = 1;

    XML_SetUserData(parser, &depth);
    XML_SetElementHandler(parser, startElement, endElement);
    XML_SetCharacterDataHandler(parser, handler);

	strcpy(buf, "<?xml version = \"1.0\"?><challenge><user_id>23</user_id><test_id>106</test_id><challenge_id>71</challenge_id><code>dkjhskhdjsdjsdh dhs djskhd sdhjkdh ksdhakdh</code><proglang>python</proglang></challenge>");

    do {
		int len = strlen(buf);
        done = len < sizeof(buf);
		XML_Parse(parser, buf, len, done);
        
    } while (!done);

    XML_ParserFree(parser);

    int i;
    for (i = 0; i < (sizeof(config)/sizeof(config[0])); i++){
        struct setting current = config[i];
        printf("%s: %s\n", current.key, current.value);
        free(current.value);
    }
    return 0;
}
