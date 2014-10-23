#include "vector.h"

Vector add(Vector v1, Vector v2){
  Vector vs;
  vs.x = v1.x + v2.x;
  vs.y = v1.y + v2.y;
  return vs;
}

Vector subtract(Vector v1, Vector v2){
  Vector vs;
  vs.x = v1.x - v2.x;
  vs.y = v1.y - v2.y;
  return vs;
}

Vector multByScalar(Vector v, float scalar){
  v.x *= scalar;
  v.y *= scalar;
  return v;
}

Vector divideByScalar(Vector v, float scalar){
  v.x /= scalar;
  v.y /= scalar;
  return v;
}

Vector normalize(Vector v){
  float l = length(v);
  if(l > 1){
    float inverse = 1 / l;
    Vector norm;
    norm = multByScalar(v, inverse);
    return norm;
  }
  return v;
}
