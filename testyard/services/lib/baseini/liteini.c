/*
Compile Command: gcc -Wall liteini.c -o liteini
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


void get_sections(char *filepath, int **sect_count, section **sections_list){
    FILE *fp;
    char *line;
    int sect_ctr;
	
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
	**sect_count = 0;
	while(fgets(line, LINE_LEN, fp) != NULL){
		if(line[0] == ';'){ /* Comment line */
		    continue;
		}
		char *key, *value;
		key = (char *)malloc((LINE_LEN/2 -1) * sizeof(char));
		value = (char *)malloc((LINE_LEN/2 -1) * sizeof(char));
        	if(line[0] == '[' && line[strlen(line) - 2] == ']'){ /* This is a fucking section. */
			
			int line_len = strlen(line);
			section_name = (char *)malloc((line_len-1)*sizeof(char));
			int i;
			for (i=1;i < line_len - 2;i++){
			    section_name[i-1] = line[i];
			}
		    	section_name[i] = '\0';
			sections_list[sect_ctr] = (section *)malloc(sizeof(section));
			sections_list[sect_ctr]->sect_name = (char *)malloc(LINE_LEN*sizeof(char));
			strcpy(sections_list[sect_ctr]->sect_name, section_name);
			
			kcntr = 0;
			vcntr = 0;
			line = (char *)malloc(LINE_LEN*sizeof(char));

			**sect_count = sect_ctr;
			sections_list[sect_ctr]->sect = (section_content *)malloc(MAX_ELEMENTS_PER_SECTION * sizeof(section_content));
			sect_ctr++;
		}
		else{
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
				if(line[j] == '\0' || line[j] == '\n' || line[j] == ';'){
					value[valctr] = '\0';
					break;
				}
				if(line[j] == '='){
					key[keyctr] = '\0';
					equal_flag = 1;
					continue;
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
			value[valctr] = '\0';
		}

		sections_list[sect_ctr-1]->sect->keys[kcntr] = (char *)malloc((LINE_LEN/2) * sizeof(char));
		sections_list[sect_ctr-1]->sect->values[vcntr] = (char *)malloc((LINE_LEN/2) * sizeof(char));
		
		strcpy((sections_list[sect_ctr-1]->sect)->keys[kcntr], key);
		strcpy((sections_list[sect_ctr-1]->sect)->values[vcntr], value);
		(sections_list[sect_ctr-1]->sect)->section_name = (char *)malloc(MAX_SECTION_NAME_LEN*sizeof(char));
		strcpy(sections_list[sect_ctr-1]->sect->section_name, section_name);
		if(_is_empty_string((sections_list[sect_ctr-1]->sect)->keys[kcntr]) && _is_empty_string((sections_list[sect_ctr-1]->sect)->values[vcntr])){
		    continue;
		}
        	kcntr++;
		vcntr++;
		line = (char *)malloc(LINE_LEN*sizeof(char));
	}
}

/*
Given a section name, get all elements (keys and values) as a 2D array.
The given section name should be case-sensitive. The first param is the
sections_list returned by a call to "get_sections" function. The third
param is the count of the number of sections in the ini file. The fourth
param is a pointer to the number of params in the section found. All params
are required. None is optional.
*/
void getElementsBySectionName(section **sections_list, char *section_name, int *sect_count, int *params_count){
    int sect_ctr = 0;
    char *sect_name;
    int param_ctr = 0;
    
    int kcntr = 0;
    int vcntr = 0;
    for (sect_ctr=0; sect_ctr <= *sect_count; sect_ctr++){
	sect_name = (char *)malloc((strlen(sections_list[sect_ctr]->sect->section_name) + 1)*sizeof(char));
        strcpy(sect_name, sections_list[sect_ctr]->sect->section_name);
        if(!strcmp(sect_name, section_name)){
	    while(sections_list[sect_ctr]->sect->keys[kcntr]){
		//printf("Key Name: %s\n", sections_list[sect_ctr]->sect->keys[kcntr]);
	    	key_value_dict[param_ctr][0] = (char *)malloc(25 * sizeof(char)); /* Assuming the max length of a key is 25 characters */
	    	key_value_dict[param_ctr][1] = (char *)malloc(40 * sizeof(char)); /* Assuming the max length of a value is 40 characters */
		//printf("Value 3 Name: %s\n\n", sections_list[sect_ctr]->sect->values[vcntr]);
	    	strcpy(key_value_dict[param_ctr][0], sections_list[sect_ctr]->sect->keys[kcntr]);
		strcpy(key_value_dict[param_ctr][1], sections_list[sect_ctr]->sect->values[vcntr]);
		kcntr++;
		vcntr++;
		param_ctr++;
		*params_count = param_ctr;
            }
	}
    }
}

/*
This function returns the specific value of a given key in a given section. The 
first argument is the key name in the section. It is case-sensitive. The second 
argument is the number of keys in the section refered to in the call to the 
'getElementsBySectionName' function. This value is the same as contents of the
(fourth) argument 'params_count' (int *) in the call to 'getElementsBySectionName'
function.
Note: Prior to calling this function, you would need to call both 'get_sections'
and 'getElementsBySectionName' (in that order) with all the necessary arguments.
Please refer to the example code given in the file 'main.c' in the directory in
the 'samples' directory. The example ini file resides in the 'examples' 
directory.
*/
char *getValueByKeyFromSection(char *keyname, int pcount){
    int pctr = 0;
    for(pctr=0; pctr < pcount; pctr++){
	if(!strcmp(key_value_dict[pctr][0], keyname)){
	    return(key_value_dict[pctr][1]);
	}
    }
    printf("Your key was not found in the given section (provided by you in the call to 'getElementsBySectionName'\n\n");
    return(NULL);
}

/* Functions called when the library is loaded and exited */
void __attribute__ ((constructor)) initLibrary(void) {
 //
 // Function that is called when the library is loaded
 //
 //   printf("Library is initialized\n"); 
}

void __attribute__ ((destructor)) cleanUpLibrary(void) {
 //
 // Function that is called when the library is closed.
 //
}

