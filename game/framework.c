#include "framework.h"
#include <stdbool.h>

#define TITLE "Hello, World"
#define WINDOW_WIDTH 640
#define WINDOW_HEIGHT 480
#define FPS 60
#define DELAY_TIME (1000.0f / FPS)

int main(int argc, char* argv[]){
  SDL_Window *window;
  SDL_Renderer *renderer;
  int status;

  /* initialize */
  status = SDL_Init(SDL_INIT_VIDEO);
  
  window = SDL_CreateWindow(TITLE, SDL_WINDOWPOS_CENTERED, 
			    SDL_WINDOWPOS_CENTERED,
			    WINDOW_WIDTH, WINDOW_HEIGHT, SDL_WINDOW_SHOWN);
  if(window != 0){
    renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);
  }else{
    return 1;
  }
  bool running = true;
  // done initialization. Create game loop!
  while(running){
  }    
		   

    return status;
  }
