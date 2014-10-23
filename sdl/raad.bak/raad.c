#include "raad.h"
#include  "bullet.h"

#define WINDOW_TITLE "Ravens Attack at Dusk"
#define WINDOW_WIDTH 800
#define WINDOW_HEIGHT 600

int running = 1;

const char *help = "Ravens!";

int main(int argc, char *argv[]){
  if(argc > 1 && !strcmp(argv[1], "-h")){
    puts(help);
    return 0;
  }
  GameState gameState;
  SDL_Window *window = NULL;
  SDL_Renderer *renderer = NULL;

  srandom(time(NULL));
  
  if(SDL_Init(SDL_INIT_VIDEO) >= 0){
    window = SDL_CreateWindow(WINDOW_TITLE, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, WINDOW_WIDTH, WINDOW_HEIGHT, SDL_WINDOW_SHOWN);
    if(window != 0){
      renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    }else{
      return 1;
    }
  }
  gameState.renderer = renderer;
  loadGame(&gameState);
  while(running){
    handleEvents(&gameState);
    render(&gameState);
  }


  /* Close and destroy the window */
  SDL_DestroyWindow(window);
  SDL_DestroyRenderer(renderer);
  SDL_DestroyTexture(gameState.man.texture);

  int i;
  for(i = 0; i < MAX_BULLETS; i++){
    removeBullet(i);
  }

  SDL_Quit();
  return 0;

} 

void loadGame(GameState *game){
  /* create a man */
  Vector pos = {0, 0};
  Vector vel = {0, 0};
  Vector acc = {0, 0};

  /* Makingn of the hero */
  Runner _man = {pos, vel, acc, 3, 1, 0, NULL}; 
  loadTexture("assets/animate-alpha.png", &_man.texture, game->renderer);
  game->man = _man;

  /* enemies */
  loadTexture("assets/raven.png", &game->raven, game->renderer);
  int i;
  for(i = 0; i < 10; i++){
    game->ravens[i].x = random()% WINDOW_WIDTH;
    game->ravens[i].y = random()% WINDOW_HEIGHT;
  }

  /* other game objects */
  /* bricks */
  loadTexture("assets/bricks.png", &game->brick, game->renderer);
  for(i = 0; i < 100; i++){
    game->ledges[i].x = i * 128;
    game->ledges[i].y = 472;
    game->ledges[i].w = 128;
    game->ledges[i].h = 128;
  }

  game->ledges[99].x = 320;
  game->ledges[99].y = 120;

}

void handleEvents(GameState *game){
  SDL_Event event;
  const Uint8* keystates;
  while(SDL_PollEvent(&event)){
    switch(event.type){
    case SDL_QUIT:
      running = 0;
      break;
    case SDL_KEYDOWN:
      switch(event.key.keysym.sym){
      case SDLK_ESCAPE:
	running = 0;
	break;
      }
      
      keystates = SDL_GetKeyboardState(NULL);

      if(keystates != 0){
	if(keystates[SDL_SCANCODE_RIGHT]){
	  game->man.velocity.x = 15;
	}
	if(keystates[SDL_SCANCODE_LEFT]){
	  game->man.velocity.x = -15;
	}
	if(keystates[SDL_SCANCODE_UP]){
	  game->man.velocity.y = -15;
	}
	if(keystates[SDL_SCANCODE_DOWN]){
	  game->man.velocity.y = 15;
	}
      }
  
      game->man.currentFrame =  (int)(((SDL_GetTicks() / 100) % 6));
      game->man.velocity = add(game->man.velocity, game->man.acceleration);
      game->man.position = add(game->man.position, game->man.velocity);
    }
  }

  
}

void render(GameState *game){
  SDL_SetRenderDrawColor(game->renderer, 0, 0, 255, 255);
  SDL_RenderClear(game->renderer);

  /* draw the hero */
  drawTextureFrame(game->man.texture, game->man.position.x, game->man.position.y,
		   128, 82, 1, game->man.currentFrame, game->renderer);

  /********  draw ravens */
  int i;
  for(i = 0; i < 10; i++){
    SDL_Rect ravenRect = {game->ravens[i].x, game->ravens[i].y, 64, 64};
    SDL_RenderCopy(game->renderer, game->raven, NULL, &ravenRect);
  }

  /* draw other game objects */
  /* ravens */
  for(i = 0; i < 100; i++){
    drawTexture(game->brick, game->ledges[i].x, game->ledges[i].y, game->ledges[i].w, game->ledges[i].h, game->renderer);
  }
  SDL_RenderPresent(game->renderer);
}
