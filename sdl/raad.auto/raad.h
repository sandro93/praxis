#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

#include "raven.h"
#include "vector.h"
#include "texture.h"
#include "ledge.h"

typedef struct{
  Vector position;
  Vector velocity;
  Vector acceleration;
  short life;
  int currentFrame;
  int currentRow;
  SDL_Texture* texture;
} Runner;

typedef struct{
  Runner man;
  Raven ravens[20];
  Ledge ledges[100];
  SDL_Texture *raven;
  SDL_Texture *brick;

  SDL_Renderer *renderer;
} GameState;

void loadGame(GameState*);
void handleEvents(GameState*);
void render(GameState*);
