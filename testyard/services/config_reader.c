#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*
The structure of the config file will be as follows:
param_name = param_value
.....
.....

Comments will start with '#' character. So lines 
starting with '#' will be skipped/ignored by the
parser.

*/

char** splitstring(char *line, char divider){
	char *left, *right;
	int i;
	char *parts[2];
	left = (char *)malloc(80 * sizeof(char));
	right = (char *)malloc(70 * sizeof(char));
	for(i=0; i < strlen(line) && line[i] != divider; i++){
		if(line[i] == ' '){
			continue;
		}
		left[i] = line[i];
	}
	i +=1;
	line[i] = '\0';
	for(;i < strlen(line) && line[i] != '\n'; i++){
		if(line[i] == ' '){
			continue;
		}
		right[i] = line[i];
	}
	right[i + 1] = '\0';
	parts[0] = (char *)malloc(strlen(left) * sizeof(char));
	parts[1] = (char *)malloc(strlen(right) * sizeof(char));
	strcpy(parts[0], left);
	strcpy(parts[1], right);
	return (parts);
}


int main(int argc, char *argv[]){
	char *configfilename;
	FILE *cfgfp;
	char **params[2];
	char **parts;
	char *cfgline;
	size_t len = 0;
	int linecount = 100;
	int linectr = 1;
	if(argc < 2){
	    printf("The config file name was not passed in as an argument. Stopping further execution.\n");
		exit(1);
	}
	configfilename = (char *)malloc(strlen(argv[1]) * sizeof(char));
	strcpy(configfilename, argv[1]);
	/* printf("File name is %s\n", configfilename); */
	cfgfp = fopen(configfilename, "r");
	cfgline = (char *)malloc(150 * sizeof(char)); /* I am  setting the max line length at 150 characters. That should be enough. */
	params[0] = (char **)malloc(linecount * (sizeof(char **)));
	params[1] = (char **)malloc(linecount * (sizeof(char **)));
	parts = (char **)malloc(sizeof(char));
	while(getline(&cfgline, &len, cfgfp) != -1 && !feof(cfgfp)){
		printf("Config line: %s\n", cfgline);
		params[linectr][0] = (char *)malloc(80*sizeof(char));
		params[linectr][1] = (char *)malloc(70*sizeof(char));
		parts = splitstring(cfgline, '=');
		strcpy(params[linectr][0], parts[0]);
		strcpy(params[linectr][1], parts[1]);
		printf("Key: %s, Value: %s", params[linectr][0],params[linectr][1]);
		linectr++;
	}
	return(0);
}

/*
Compile:  gcc -Wall -o config_reader config_reader.c
Run: ./config_reader.exe

--S
*/