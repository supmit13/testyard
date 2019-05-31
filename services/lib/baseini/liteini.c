/*
Compile Command: gcc libini.c -o libini
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "liteini.h"


int _is_empty_string(char *str){
    int slen = strlen(str);
    int isempty = 0; /* 0 means it is not empty */
    int i;
    for(i=0; i < slen; i++){
        if(str[i] != ' ' && str[i] != '\0' && str[i] != '\n'){
	    return(isempty);
        }
    }
    return(1); /* This is an empty string */
}


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
	char *section_name;
	while(fgets(line, LINE_LEN, fp) != NULL){
		char *key, *value;
		key = (char *)malloc((LINE_LEN/2 -1) * sizeof(char));
		value = (char *)malloc((LINE_LEN/2 -1) * sizeof(char));
		sections_list[sect_ctr].sect = (section_content *)malloc(5000*sizeof(section_content));
        	if(line[0] == '[' && line[strlen(line) - 2] == ']'){ /* This is a fucking section. */
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

       		/*
	    	*(sections_list[sect_ctr].sect->keys + kcntr) = (char *)malloc((LINE_LEN/2 -1) * sizeof(char));
		*(sections_list[sect_ctr].sect->values + vcntr) = (char *)malloc((LINE_LEN/2 -1) * sizeof(char));
		*/
		
		sections_list[sect_ctr].sect->keys[kcntr] = (char *)malloc((LINE_LEN/2) * sizeof(char));
		sections_list[sect_ctr].sect->values[vcntr] = (char *)malloc((LINE_LEN/2) * sizeof(char));

		strcpy((sections_list[sect_ctr].sect)->keys[kcntr], key);
		strcpy((sections_list[sect_ctr].sect)->values[vcntr], value);
		(sections_list[sect_ctr].sect)->section_name = (char *)malloc(MAX_SECTION_NAME_LEN*sizeof(char));
		strcpy(sections_list[sect_ctr].sect->section_name, section_name);
		
		if(_is_empty_string((sections_list[sect_ctr].sect)->keys[kcntr]) && _is_empty_string((sections_list[sect_ctr].sect)->values[vcntr])){
		    continue;
		}
		/*
		printf("SECTION LIST NAME: %s\n", sections_list[sect_ctr].sect->section_name);
		printf("KEY= %s\n", (sections_list[sect_ctr].sect)->keys[kcntr]);
		printf("VALUE= %s\n", (sections_list[sect_ctr].sect)->values[vcntr]);
		printf("\n\n----------------------------------------------------------------------\n");
		*/		
		sect_ctr++;
        	kcntr++;
		vcntr++;
		line = (char *)malloc(LINE_LEN*sizeof(char));
	}
	return(sections_list);
}

/*
Given a section name, get all elements (keys and values) as a 2D array.
The given section name may not be case-sensitive. The first param is the
sections_list returned by a call to "get_sections" function.
*/
char *[2] getElementsBySectionName(section *sections_list, char *section_name){
}

/*
This function returns the specific value of a given key in a given section.
The first argument is, as usual, "sections_list", which is a list of instances
of the section structure. The second and the third arguments are section
name and key name, both case-insensitive.
*/
char *getValueByKeyFromSection(section *sections_list, char *section_name, char *keyname){
}

/* This code should actually be written by the user. I wrote it here just to test the library */
int main(){
	char *file;
	section * s;
	file = (char *)malloc(80*sizeof(char));
	strcpy(file,"./examples/test.ini");
	s = get_sections(file);
}

