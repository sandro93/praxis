#define length(v) (sqrt(v.x * v.x + v.y * v.y))

typedef struct{
  float x;
  float y;
} Vector;

Vector add(Vector, Vector);
Vector multByScalar(Vector v, float scalar);
Vector subtract(Vector v1, Vector v2);
Vector divideByScalar(Vector v, float scalar);
Vector normalize(Vector v);
