#include <SDL2/SDL.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdbool.h>

/* game */ 
int init(const char* title, int xpos, int ypos, int height, int width,
	 int flags);

void clean();
void render();
void update();
void handleEvents();

/* textures */
int loadTexture(const char* filename, SDL_Texture** texture, SDL_Renderer* renderer);
void drawTexture(SDL_Texture* texture, int x, int y, int width, int height, SDL_Renderer* renderer);

void drawTextureFrame(SDL_Texture* texture, int x, int y, int width, int height, int currentRow, int currentFrame,  SDL_Renderer* renderer);

/* vectors */
#define length(v) (sqrt(v.x * v.x + v.y * v.y))

typedef struct _vector {
  float x;
  float y;
} Vector;

Vector add(Vector, Vector);
Vector multByScalar(Vector v, float scalar);
Vector subtract(Vector v1, Vector v2);
Vector divideByScalar(Vector v, float scalar);
Vector normalize(Vector v);

/* character */
typedef struct _runner {
  Vector position;
  Vector velocity;
  Vector acceleration;
  int currentFrame;
  int currentRow;
  SDL_Texture* texture;
} Runner;

Runner createRunner(Vector, Vector, Vector, SDL_Texture*);

/* input */
enum mouse_buttons {
  LEFT = 0,
  MIDDLE = 1,
  RIGHT = 2
};
