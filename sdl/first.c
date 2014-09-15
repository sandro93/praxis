#include <SDL2/SDL.h>
#include <stdio.h>
#include <errno.h>

SDL_Window* g_pWindow = 0;
SDL_Renderer* g_pRenderer = 0;

int main(int argc, char* argv[]){
  /* initialize SDL */
  if(SDL_Init(SDL_INIT_VIDEO | SDL_INIT_TIMER) >= 0){
    /* if succeeded, create the window */

    g_pWindow = SDL_CreateWindow("Hello, Graphical World!", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, 640, 680, SDL_WINDOW_SHOWN);
    /* if the window creation succeeded, create the renderer */
    if(g_pWindow != 0){
      g_pRenderer = SDL_CreateRenderer(g_pWindow, -1, 0);
    }
  }else{
    /* SDL couldn't initialize */
    perror("Couldn't initialize\n");
    return 1;
  }

  /* Everyting succeeded, draw the window */

  /* Set to black - this funcion expects RGBA */
  SDL_SetRenderDrawColor(g_pRenderer, 0, 0, 0, 255);

  SDL_RenderClear(g_pRenderer);

  // Show the window.
  SDL_RenderPresent(g_pRenderer);
  SDL_Delay(50000);
  SDL_Quit();

  return 0;
}

  

