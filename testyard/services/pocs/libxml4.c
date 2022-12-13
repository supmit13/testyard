/*
   Simple test with libxml2 <http://xmlsoft.org>. It displays the name
   of the root element and the names of all its children (not
   descendents, just children).

   On Debian, compiles with:
   gcc -Wall -o libxml4 $(xml2-config --cflags) $(xml2-config --libs) libxml4.c  -I/usr/include/libxml2  -lxml2

*/


#include <stdio.h>
#include <string.h>
#include <libxml/parser.h>

char ** get_xml_data(char *xmldump){
	xmlChar *xmldoc;
    xmldoc = xmlCharStrdup(xmldump);
    xmlDoc *document;
    xmlNode *root, *first_child, *node;
    xmlChar *key;
	char **retlist;
	retlist = (char **)malloc(5 * sizeof(char[2000]));
    document = xmlParseDoc(xmldoc);
    root = xmlDocGetRootElement(document);
    //fprintf(stdout, "Root is <%s> (%i)\n", root->name, root->type);
    first_child = root->children;
    for (node = first_child; node; node = node->next) {
        //fprintf(stdout, "\t Child is <%s> (%i)\n", node->name, node->type);
                /* Added lines */
                if(!xmlStrcmp(node->name,"challenge_id")){
                        key = xmlNodeListGetString(document, node->xmlChildrenNode, 1);
				        //printf("Challenge Id: %s\n", key);
						*(retlist + 0) = key;
                }
                else if(!xmlStrcmp(node->name,"user_id")){
						key = xmlNodeListGetString(document, node->xmlChildrenNode, 1);
                        //printf("User Id: %s\n", key);
						*(retlist + 1) = key;
                }
                else if(!xmlStrcmp(node->name,"test_id")){
                        key = xmlNodeListGetString(document, node->xmlChildrenNode, 1);
                        //printf("Test Id: %s\n", key);
						*(retlist + 2) = key;
                }
                else if(!xmlStrcmp(node->name,"code")){
                        key = xmlNodeListGetString(document, node->xmlChildrenNode, 1);
                        //printf("Code: %s\n", key);
						*(retlist + 3) = key;
                }
                else if(!xmlStrcmp(node->name,"proglang")){
                        key = xmlNodeListGetString(document, node->xmlChildrenNode, 1);
                        //printf("Programming Language: %s\n", key);
						*(retlist + 4) = key; 
                }
                /* Added lines end */
    }
	return(retlist);
}

int main(int argc, char **argv){
	char **retvals;
	int j;
    retvals = get_xml_data("<?xml version = \"1.0\"?><challenge><user_id>23</user_id><test_id>106</test_id><challenge_id>71</challenge_id><code>dkjhskhdjsdjsdh dhs djskhd sdhjkdh ksdhakdh</code><proglang>python</proglang></challenge>");
	for(j=0; j < 5; j++){
		if(j == 0){
		    printf("challenge id: %s\n",*(retvals + j));
		}
		if(j == 1){
		    printf("user id: %s\n",*(retvals + j));
		}
		if(j == 2){
		    printf("test id: %s\n",*(retvals + j));
		}
		if(j == 3){
		    printf("code: %s\n",*(retvals + j));
		}
		if(j == 4){
		    printf("proglang: %s\n",*(retvals + j));
		}
	}
    return 0;
}
