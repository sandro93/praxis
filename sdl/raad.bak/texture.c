#include "raad.h"

int loadTexture(const char* filename, 
		SDL_Texture** texture, SDL_Renderer* renderer){
  SDL_Surface* tmpSurface = IMG_Load(filename);
  if(tmpSurface == 0){
    perror(SDL_GetError());
    return -1;
  }
  *texture = SDL_CreateTextureFromSurface(renderer, tmpSurface);
  /* SDL_QueryTexture(texture, NULL, NULL, &sourceRectangle.w, &sourceRectangle.h);  */
  SDL_FreeSurface(tmpSurface);
  if(texture != 0){
    return 1;
  }
  return -1;
}

void drawTexture(SDL_Texture* texture, int x, int y, int width,
		 int height, SDL_Renderer* renderer){
  SDL_RendererFlip flip = SDL_FLIP_NONE;
  
  SDL_Rect srcRect;
  SDL_Rect destRect;
  srcRect.x = 0;
  srcRect.y = 0;
  srcRect.w = destRect.w = width;
  srcRect.h = destRect.h = height;
  destRect.x = x;
  destRect.y = y;

  SDL_RenderCopyEx(renderer, texture, &srcRect, &destRect, 0, 0, flip);
}
void drawTextureFrame(SDL_Texture* texture, int x, int y, int width, int height, int currentRow, int currentFrame,  SDL_Renderer* renderer){
  SDL_RendererFlip flip = SDL_FLIP_NONE;
  
  SDL_Rect srcRect;
  SDL_Rect destRect;

  srcRect.x = width * currentFrame;
  srcRect.y = height * (currentRow - 1);
  srcRect.w = destRect.w = width;
  srcRect.h = destRect.h = height;
  destRect.x = x;
  destRect.y = y;

  SDL_RenderCopyEx(renderer, texture, &srcRect, &destRect, 0, 0, flip);
}
