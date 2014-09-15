/* (*1.5) Write a program that prints the sizes of the fundamental types, a few
   pointer types, a few enumerations of your choice. Use the sizeof operator.
*/

#include <iostream>

int main()
{
  enum state { gas, liquid, solid };
  struct student { int year; std::string state; bool isstupid();};

  char* letter;
  char a = 'a';
  letter = &a;
  int* number;
  int x = 100;
  number = &x;
  void* p;
  
  std::cout << "sizeof(short int) == " << sizeof(short int) << '\n';
  std::cout << "sizeof(int) == " << sizeof(int) << '\n';
  std::cout << "sizeof(char) == " << sizeof(char) << '\n';
  std::cout << "sizeof(float) == " << sizeof(float) << '\n';
  std::cout << "sizeof(double) == " << sizeof(double) << '\n';
  std::cout << "sizeof(long int) == " << sizeof(long int) << '\n';
  std::cout << "sizeof(long double) == " << sizeof(long double) << '\n';
  std::cout << "sizeof(bool) == " << sizeof(bool) << '\n';
  std::cout << "sizeof(int*) == " << sizeof(int*) << '\n';
  std::cout << "sizeof(enum state) == " << sizeof(state) << '\n';
  std::cout << "sizeof(struct student) == " << sizeof(student) << '\n';
  std::cout << "sizeof(char *letter) == " << sizeof(letter) << '\n';
  std::cout << "sizeof(int* number) == " << sizeof(number) << '\n';
  std::cout << "sizeof(void* p) == " << sizeof(p) << '\n';

  return 0;
}


