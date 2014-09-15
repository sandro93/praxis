#include <iostream>
#include <vector>
#include <iterator>
#include <algorithm>

using namespace std;
void counting_sort(vector<int>& a,vector<int>& b)
{
  int k = a.size();
  vector<int> c(k+1);
  for(int i=0;i<=k;i++)
    c[a[i]]++;
  for(int i=1;i<=k;i++)
    c[i]+=c[i-1];
  for(int i = a.size();i>=0;i--){
    b[ c[ a[i] ]  - 1 ] = a[i];
    c[ a[i] ] --;
  }
}
int main(){
  vector<int> v;


  v.push_back(8);
  v.push_back(4);
  v.push_back(4);
  v.push_back(3);
  v.push_back(2);
  v.push_back(6);

  vector<int> h(v.size());
  counting_sort(v, h);
  ostream_iterator<int> d(cout,"  ");
  copy(h.begin(), h.end(), d);
  return 0;
}
