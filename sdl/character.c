#include "game.h"

Runner createRunner(Vector pos, Vector vel, Vector acc, SDL_Texture* texture){
  Runner runner = {pos, vel, acc, 1, 0, texture};
  return runner;
}
