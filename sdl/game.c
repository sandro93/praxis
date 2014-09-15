#include "game.h"

SDL_Window* window = 0;
SDL_Renderer* renderer = 0;

bool mouseButtStates[3] = {false, false, false};
Vector mousePosition;

const Uint8* keystates;

bool running = false;

enum game_states{
  MENU,
  PLAY,
  GAMEOVER
};

int currentState = PLAY;

Runner runner;

int main(int  argc, char* argv[]){
  int FPS = 60;
  int DELAY_TIME = 1000.0f / FPS;
  int frameStart, frameTime;
  
  if(init("Hello, World!", SDL_WINDOWPOS_CENTERED, 
	  SDL_WINDOWPOS_CENTERED, 
	  640, 480, SDL_WINDOW_SHOWN)){
    running = true;
  }
  while(running){
    frameStart = SDL_GetTicks();
    handleEvents();
    update();
    render();
    frameTime = SDL_GetTicks() - frameStart;

    if(frameTime < DELAY_TIME){
      SDL_Delay((int)(DELAY_TIME - frameTime));
    }
  }
  clean();
  return 0;
}

int init(const char* title, int xpos, int ypos, int height, int width, int flags){
  Vector pos = {0, 0};
  Vector vel = {0, 0};
  Vector acc = {0, 0};
  SDL_Texture* texture;
  if(SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO) >= 0){
    window = SDL_CreateWindow(title, xpos, ypos, height, width, flags);
  }
  if(window != 0)
    renderer = SDL_CreateRenderer(window, -1, 0);
  else
    return 0; /* SDL couldn't initialize. */
  

  loadTexture("assets/animate.bmp", &texture, renderer);
  runner = createRunner(pos, vel, acc, texture);
  return 1;
}

void update(){
  switch(currentState){
  case MENU:
    break;
  case PLAY:
    /* an example of doing something on mouse click. */
    if(mouseButtStates[LEFT]){
      runner.velocity.x = 1;
    }
    /* follow the mouse! REMOVE this to enable keyboard motion! */
    runner.velocity = divideByScalar(subtract(mousePosition, runner.position), 1); 

    /* move the player with the keyboard if the keystate is assigned to */
    if(keystates != 0){
      if(keystates[SDL_SCANCODE_RIGHT]){
	runner.velocity.x = 2;
      }
      if(keystates[SDL_SCANCODE_LEFT]){
	runner.velocity.x = -2;
      }
      if(keystates[SDL_SCANCODE_UP]){
	runner.velocity.y = -2;
      }
      if(keystates[SDL_SCANCODE_DOWN]){
	runner.velocity.y = 2;
      }
    }
    runner.currentFrame =  (int)(((SDL_GetTicks() / 100) % 6));
    runner.velocity = add(runner.velocity, runner.acceleration);
    runner.position = add(runner.position, runner.velocity);
    break;
  case GAMEOVER:
    break;
  }
}

void render(){
  SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
  
  SDL_RenderClear(renderer);
  drawTextureFrame(runner.texture, runner.position.x, runner.position.y, 128, 82, 1, runner.currentFrame, renderer);

  SDL_RenderPresent(renderer);
}

void clean(){
  SDL_DestroyWindow(window);
  SDL_DestroyRenderer(renderer);
  SDL_DestroyTexture(runner.texture);
  SDL_Quit();
}

void handleEvents(){
  SDL_Event event;
  if(SDL_PollEvent(&event)){
    switch(event.type){
    case SDL_QUIT:
      running = false;
      break;
    case SDL_MOUSEBUTTONDOWN:
      if(event.button.button == SDL_BUTTON_LEFT){
	mouseButtStates[LEFT] = true;
      }
      if(event.button.button == SDL_BUTTON_MIDDLE){
	mouseButtStates[MIDDLE] = true;
      }
      if(event.button.button == SDL_BUTTON_RIGHT){
	mouseButtStates[RIGHT] = true;
      }
      break;
    case SDL_MOUSEBUTTONUP:
      if(event.button.button == SDL_BUTTON_LEFT){
	mouseButtStates[LEFT] = false;
      }
      if(event.button.button == SDL_BUTTON_MIDDLE){
	mouseButtStates[MIDDLE] = false;
      }
      if(event.button.button == SDL_BUTTON_RIGHT){
	mouseButtStates[RIGHT] = false;
      }
      break;
    case SDL_MOUSEMOTION:
      mousePosition.x = event.motion.x;
      mousePosition.y = event.motion.y;
    case SDL_KEYDOWN:
      keystates = SDL_GetKeyboardState(NULL);
      break;
    case SDL_KEYUP:
      keystates = SDL_GetKeyboardState(NULL);
      break;
    default:
      break;
    }
  }
}
