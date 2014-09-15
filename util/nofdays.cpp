/* 5.9.7 *.15
   Define a table of the names of months of the year and the number of
   days in each month.Write out that table. Do this twice; once using
   an array of char for the names and an array for the number of days
   and once using an array of structures, with each structure holding
   the name of a month and the number of days in it.
*/

#include <iostream>
int main()
{
  char* months[12] = {"January", "February", "March", "April", "May", "June", "July",
		      "August", "September", "October", "November", "December"};
  int nofdays[12] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};

  std::cout << "------------------------\n" << "Month\t\t| days\t|\n" << "------------------------\n";

  for(int i = 0; i < 12; ++i)
    std::cout << months[i] << ((i > 1 && i < 8)?"\t\t| ":" \t| ") << nofdays[i] << "\t|\n";
  std::cout << "------------------------\n";

  return 0;

}
