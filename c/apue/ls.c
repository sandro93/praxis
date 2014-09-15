#include <stdio.h>
#include <dirent.h>
#include <sys/types.h>
#include <errno.h>

int main(int argc, char *argv[]){
  DIR *dp;

  struct dirent *dirp;

  if(argc != 2){
    printf("usage: ls directory\n");
    return 2;
  }

  if((dp = opendir(argv[1])) == NULL){
    fprintf(stderr, "can't open %s: ", argv[1]);
    perror(NULL);
    return errno;
  }

  while((dirp = readdir(dp)) != NULL){
    printf("%s\n", dirp->d_name);
  }

  closedir(dp);

  return 0;
}
    
    
