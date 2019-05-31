/*
Compile Command: gcc libini.c -o libini
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "liteini.h"




section *get_sections(char *filepath){
    FILE *fp;
	char *line;
	int sect_ctr;
    section *sections_list;
	section_content *sc;
	sections_list = (section *)malloc(MAX_SECTIONS*sizeof(section));
	fp = fopen(filepath, "r");
    if (fp == NULL){
      perror("Error while opening the file.\n");
      exit(EXIT_FAILURE);
    }
	line = (char *)malloc(LINE_LEN*sizeof(char));
	sect_ctr = 0;
	int kcntr = 0;
	int vcntr = 0;
	int done;
	while(fgets(line, LINE_LEN, fp) != NULL){
		char *key, *value;
		key = (char *)malloc((LINE_LEN/2 -1) * sizeof(char));
		value = (char *)malloc((LINE_LEN/2 -1) * sizeof(char));
        	if(line[0] == '[' && line[strlen(line) - 2] == ']'){ /* This is a fucking section. */
		    char *section_name;
			int line_len = strlen(line);
			section_name = (char *)malloc((line_len-1)*sizeof(char));
			int i;
			for (i=1;i < line_len - 2;i++){
			    section_name[i-1] = line[i];
			}
		    	section_name[i] = '\0';
			sections_list[sect_ctr].sect_name = (char *)malloc(LINE_LEN*sizeof(char));
			strcpy(sections_list[sect_ctr].sect_name, section_name);
			
			kcntr = 0;
			vcntr = 0;
			line = (char *)malloc(LINE_LEN*sizeof(char));
			done = 0;
		}
		else{
			/*sc =_get_content(sections_list[sect_ctr]);*/
			int line_len = strlen(line);
			int j = 0;
			int keyctr, valctr;
			key = (char *)malloc((LINE_LEN/2 -1) * sizeof(char));
		    value = (char *)malloc((LINE_LEN/2 -1) * sizeof(char));
			int equal_flag = 0;
			keyctr = 0;
		    valctr = 0;
			for(j=0;j < strlen(line); j++){
				if(line[j] == ' '){
					continue;
				}
				if(line[j] == '\0' || line[j] == '\n'){
					value[valctr] = '\0';
					break;
				}
				if(line[j] == '='){
					key[keyctr] = '\0';
					equal_flag = 1;
				}
				if(!equal_flag){
					key[keyctr] = line[j];
					keyctr++;
				}
				if(equal_flag){
					value[valctr] = line[j];
					valctr++;
				}
			}
		}

		 sections_list[sect_ctr].sect = (section_content *)malloc(5000*sizeof(section_content));
       		/*
	    	*(sections_list[sect_ctr].sect->keys + kcntr) = (char *)malloc((LINE_LEN/2 -1) * sizeof(char));
		*(sections_list[sect_ctr].sect->values + vcntr) = (char *)malloc((LINE_LEN/2 -1) * sizeof(char));
		*/
		(sections_list[sect_ctr].sect)->keys[kcntr] = (char *)malloc((LINE_LEN/2) * sizeof(char));
		(sections_list[sect_ctr].sect)->values[vcntr] = (char *)malloc((LINE_LEN/2) * sizeof(char));
		strcpy((sections_list[sect_ctr].sect)->keys[kcntr], key);
		strcpy((sections_list[sect_ctr].sect)->values[vcntr], value);
		if(!done){
			(sections_list[sect_ctr].sect)->section_name = (char *)malloc(MAX_SECTION_NAME_LEN*sizeof(char));
		    strcpy((sections_list[sect_ctr].sect)->section_name, sections_list[sect_ctr].sect_name);
			printf("SECTION NAME: %s\n", sections_list[sect_ctr].sect_name);
		    done = 1;
		}
		printf("SECTION LIST NAME: %s\n", (sections_list[sect_ctr].sect)->section_name);
		printf("KEY= %s\n", (sections_list[sect_ctr].sect)->keys[kcntr]);
		printf("VALUE= %s\n", (sections_list[sect_ctr].sect)->values[vcntr]);
		printf("\n\n----------------------------------------------------------------------\n");
				
		sect_ctr++;
        kcntr++;
		vcntr++;
		line = (char *)malloc(LINE_LEN*sizeof(char));
	}
	return(sections_list);
}

int main(){
	char *file;
	section * s;
	file = (char *)malloc(80*sizeof(char));
	strcpy(file,"./examples/test.ini");
	s = get_sections(file);
}

