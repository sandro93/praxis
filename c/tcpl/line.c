#include <stdio.h>
#include "getline.h"

/* read a line into s. return length */
int readline(char s[], int len){
  int c, i;
  for(i = 0; i < len-1 && (c = getchar()) != EOF && c != '\n'; ++i)
    s[i] = c;
  if(c == '\n'){
    s[i] = c;
    i++;
  }
  s[i] = '\0';
  return i;
}

int findblnk(char s[], int start, int n){
  int pos = -1;
  
  /* if searching backwards, move cursor to the last character before '\0' */
  if(n < 0){
    if(s[start] == '\0'){
      --start;
    }
    if(s[start] == '\n'){
      --start;
    }
  }else{
    /* correct improper start, but leave it as it is if searching backwards */
    if(start < 0){
      start = 0;
    }
  }
  while(s[start] != '\0' &&  s[start] != '\n' && s[start] != EOF){
    if(start < 0){
      printf("Searching in vaid: %d\n", start);
    }
    if(s[start] == ' '){
      pos = start;
    }
    if(n > 0){
      ++start;
    }else{
      --start;
    }
  }
  return pos;
}

    
