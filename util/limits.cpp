/* chapter 4 section 11 - exercise 5 (*2)
   What, on your system, are the largest and the smallest values of the 
   following types: 
   char, short, int, long, float, double, long double, and unsigned
*/

#include <iostream>
#include <limits>

int main()
{

  std::cout << "largest char == " << int(std::numeric_limits<char>::max()) << '\n';
  std::cout << "smalleest char == " << int(std::numeric_limits<char>::min()) << '\n';
  std::cout << "smallest short == " << std::numeric_limits<short>::min() << '\n';
  std::cout << "largest short == " << std::numeric_limits<short>::max() << '\n';
  std::cout << "smallest int == " << std::numeric_limits<int>::min() << '\n';
  std::cout << "largest int == " << std::numeric_limits<int>::max() << '\n';
  std::cout << "smallest long == " << std::numeric_limits<long>::min() << '\n';
  std::cout << "largest long == " << std::numeric_limits<long>::max() << '\n';
  std::cout << "smallest float == " << std::numeric_limits<float>::min() << '\n';
  std::cout << "largest float == " << std::numeric_limits<float>::max() << '\n';
  std::cout << "smallest double == " << std::numeric_limits<double>::min() << '\n';
  std::cout << "largest double == " << std::numeric_limits<double>::max() << '\n';
  std::cout << "smallest long double == " << std::numeric_limits<long double>::min() << '\n';
  std::cout << "largest long double == " << std::numeric_limits<long double>::max() << '\n';
  std::cout << "smallest unsigned == " << std::numeric_limits<unsigned>::min() << '\n';
  std::cout << "largest unsigned == " << std::numeric_limits<unsigned>::max() << '\n';
  return 0;
}
