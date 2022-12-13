#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "liteini.h"

/* This code should actually be written by the user. I wrote it here just to test the library */
/* Note: This code refers to a file named test.ini in the 'examples' directory. 
   Also Note: The variable 'key_value_dict' is a global variable defined in liteini.h. Its
   signature is "char *key_value_dict[MAX_ELEMENTS_PER_SECTION][2]". Please iterate over it
   as shown in the code below after calling 'get_sections' and 'getElementsBySectionName' both.
   This variable is actually populated in the function 'getElementsBySectionName'.
 */
int main(){
	char *file;
	int *sect_count;
	section *sections_list;
	int pcount = 0;
	sect_count = (int *)malloc(sizeof(int));
	*sect_count = 0;
	file = (char *)malloc(80*sizeof(char));
	strcpy(file,"./examples/test.ini");
	sections_list = (section *)malloc(MAX_SECTIONS * sizeof(section));
	get_sections(file, &sect_count, &sections_list);
	getElementsBySectionName(&sections_list, "elem-3", sect_count, &pcount);
        printf("\n\nPCOUNT  is %d\n\n", pcount);
	char *value;
	char *k = (char *)malloc(25 * sizeof(char));
        strcpy(k, "two");
	value = getValueByKeyFromSection(k, pcount);
        printf("\n----------------'\nValue for key '%s' is '%s'\n------------\n", k, value);
	int pctr = 0;
	for(pctr=0; pctr < pcount; pctr++){
	    char *key, *value;
	    key = (char *)malloc(25 * sizeof(char));
	    value = (char *)malloc(40 * sizeof(char));
	    strcpy(key, key_value_dict[pctr][0]);
	    strcpy(value, key_value_dict[pctr][1]);
	    printf("Key Value in element no. %d: %s, %s\n\n", pctr, key_value_dict[pctr][0], key_value_dict[pctr][1]);
	}
	
}

