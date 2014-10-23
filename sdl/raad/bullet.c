#include "bullet.h"

SDL_Texture *bulletTexture;

Bullet *bullets[MAX_BULLETS] = { NULL };

void addBullet(float x, float y, float dx){
  int found = -1;
  int i;
  for(i = 0; i < MAX_BULLETS; i++){
    if(bullets[i] == NULL){
      found = i;
      break;
    }
  }
 
  if(found >= 0)
    {
      int i = found;
      bullets[i] = malloc(sizeof(Bullet));
      bullets[i]->x = x;
      bullets[i]->y = y;
      bullets[i]->dx = dx;    
    }
}

void removeBullet(int i){
  if(bullets[i])
    {
      free(bullets[i]);
      bullets[i] = NULL;
    }
}


