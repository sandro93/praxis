#include <stdio.h>
#include <unistd.h>

int main(int argc, char *argv[]){
  char buf[256];

  getcwd(buf, 256);

  printf("%s\n", buf);

  return 0;
}
