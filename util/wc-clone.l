/* Word count */

%{
int chars = 0;
int words = 0;
int lines = 0;
%}

%%

[a-zA-z]+ { words++; chars += strlen(yytext);}
\n	  { lines++; chars++;}
.	  { chars++;}

%%

int main(int argc, char** argv)
{
  yylex();
  printf("\t%d %d %d\n", lines, words, chars);
}
