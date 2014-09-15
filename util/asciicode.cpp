/* (*1.5) Write a program that prints out the letters 'a' .. 'z' and the digits
'0'...'9' and theri integer values. Do the same for other printable characters.
Do the same again but use hexadecimal notation.
*/

#include <iostream>

int main()
{
  for (char c = '0'; c <= 'z'; c++)
    if((c >= 'a' && c <= 'z') || c >= '0' && c <= '9')
      std::cout << "int(" << c << ") == " << int(c) << '\n';

  std::cout << '\n';
  std::cout << int('.') << std::endl;

  for (char c = '0'; c <= 'z'; c++)
    if((c >= 'a' && c <= 'z') || c >= '0' && c <= '9')
      ;
    else
      std::cout << "int(" << c << ") in hex == " << std::hex << int(c) << '\n';
  return 0;
}
