#include "getline.h"

/* read a line into s. return length */
int fold(char s[], int len);
/* find a blank in s[] if it appears between the `start` and the `n'th
   character. Return -1 if no blanks found. Negative n implies search
   between the start and the `n'th character /before/ that */
int findblnk(char s[], int start, int n);
