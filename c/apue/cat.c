#include <stdio.h>

int main(int argc, char* argv[]){
  int c;

  while((c = getc(stdin)) != EOF){
    if(putc(c, stdout) == EOF){
      perror("errer while writing");
    }
  }

  if(ferror(stdin)){
    perror("input error");
  }

  return 0;
}
