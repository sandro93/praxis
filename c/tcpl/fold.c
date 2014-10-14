/*
  Exercise 1-22. Write a program to ``fold'' long input lines into two
  or more shorter lines after the last non-blank character that occurs
  before the n-th column of input. Make sure your program does something
  intelligent with very long lines, and if there are no blanks or tabs
  before the specified column.
*/

#include "fold.h"
#include <string.h>

#define MAXLINE 200
#define LINE_LENGTH 80

/* fold lines longer than THRESHHOLD into two or more shorter lines */
int main(int argc, char* argv[]){
  int len; /* current and max line lengths */
  char line[MAXLINE]; /* current line */
  
  while((len = readline(line, MAXLINE)) > 0){
    
  }
  return 0;
}
/* copies s into d till the last whitespace is reached returning
   number of characters copied. */
int fold(char s[], char d[]){
  int length = 0;
  while(s[length] != '\0'){
    ++length;
  }
  int i;
  for (i = 0; i < LINE_LENGTH; ++i){
    d[i] = s[i];
  }
  if(s[i] != '\0'){
    d[findblnk(d, i, -i)] = '\n';
  }
  return i; 
}
