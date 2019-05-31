/*
This is a minimal library (as of now) to read an INI file.
Please do not expect much out of it. It will do your job
of reading a properly formatted INI file. It doesn't yet
have the capability of writing ini files, but that will 
probably change in the future.

NOTE: It is expected that the entire length of a line will not exceed 127 characters.
If it should be longer than you need, please resize the 'LINE_LEN' variable below to
suit your needs.
++ Supriyo.
*/

#define LINE_LEN 128
#define MAX_SECTIONS 100
#define MAX_ELEMENTS_PER_SECTION 50
#define MAX_SECTION_NAME_LEN 100

typedef struct section_content{
	char *keys[100]; 
	char *values[100];
	/* 100 key value pairs per section seems reasonable enough to me */
	char *section_name;
}section_content;

typedef struct section{
    section_content *sect;
	char *sect_name;
}section;

section *get_sections(char *filepath);
char *[2] getElementsBySectionName(section *sections_list, char *section_name);
char *getValueByKeyFromSection(section *sections_list, char *section_name, char *keyname);

section_content *_get_content(section *sect); /* NOT TO BE USED PUBLICLY */


