/* 5.9.7 *.15
   Define a table of the names of months of the year and the number of
   days in each month.Write out that table. Do this twice; once using
   an array of char for the names and an array for the number of days
   and once using an array of structures, with each structure holding
   the name of a month and the number of days in it.
*/
#include <iostream>

#define DECOR_LINE  "------------------------\n"
#define SHORT_NAME "\t\t| " // delimiter
#define LONG_NAME " \t| " 

int main()
{
  struct month {
    char* name;
    int ndays;
  };

  month months[12] = { "January", 31, "February", 28, "March", 31, "April", 30, "May", 31,
		       "June", 30, "July", 31, "August", 31, "September", 30, "October", 31, "Nobember", 30, "December", 31 };
  
  std::cout << DECOR_LINE;
  std::cout << "Month\t\t| days\t|\n";
  std::cout << DECOR_LINE;
  
  for(int i = 0; i < 12; ++i)
    {
      char* tab;
      if(i > 1 && i < 8)
	tab = SHORT_NAME;
      else
	tab = LONG_NAME;
      std::cout << months[i].name << tab << months[i].ndays << "\t|\n";
    }
  std::cout << DECOR_LINE;

  return 0;
}
