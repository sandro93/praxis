/* chapter 5.9.12 *2
   Write a function that counts the number of occurrences of a pair of
   letters in a atring and another that does the same in a
   zero-terminated array of char (a C-style string). For example, the
   pair "ab" aears twice in " xabaacbaxabb".
*/

#include <iostream>
#include <string>
#include <iterator>

int count(const std::string&, char[]);
int countinchar(const char*, char[]);

int main()
{
  const std::string str = "sentences are handful to operate on";
  int n = 0;
  n = count(str,"se");
  std::cout << n << '\n';
  n = countinchar("google glorius","gl");
  std::cout << n << '\n';

  return 0;
}

int count(const std::string& s, char letterset[2])
{
  std::string::const_iterator i = s.begin();
  std::string::const_iterator tempiter = s.begin();
  int n = 0;
  while(i != s.end())
    {
      i = find(i, s.end(), letterset[0]);
      tempiter = i;
        i = find(i, s.end(), letterset[1]);
      if(tempiter+1 == i)
	++n;
      
    }
  return n;

}

int countinchar(const char* ch, char letterset[2])
{
  int n = 0;
  for(int i = 0; ch[i] != 0; ++i)
    if(ch[i] == letterset[0] and ch[i+1] == letterset[1])
      ++n;
  return n;

}
