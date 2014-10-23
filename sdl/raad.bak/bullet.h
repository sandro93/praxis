#include "SDL2/SDL.h"

typedef struct{
  float x, y, dx;
} Bullet;

#define MAX_BULLETS 1000

void addBullet(float x, float y, float dx);
void removeBullet(int i);

