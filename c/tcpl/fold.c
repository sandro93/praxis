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
#define THRESHHOLD 80

/* fold lines longer than THRESHHOLD into two or more shorter lines */
int main(int argc, char* argv[]){
  int len; /* current and max line lengths */
  char line[MAXLINE]; /* current line */
  
  while((len = readline(line, MAXLINE)) > 0){
    printf("----------------\n");
    printf("len, -len    ---- %d: %s", findblnk(line, strlen(line), -1 * strlen(line)), line);
    printf("0, -len      ---- %d: %s", findblnk(line, 0, -1 * strlen(line)), line);
    printf("-2 len       ---- %d: %s", findblnk(line, -2, strlen(line)), line);
    printf("-2 -len      ---- %d: %s", findblnk(line, -2, -1 * strlen(line)), line);
    printf("2 -11 * len  ---- %d: %s", findblnk(line, 2, -11 * strlen(line)), line);    

  }
  return 0;
}

int fold(char s[], char d[]){
  return 0; 
}
