int loadTexture(const char* filename, SDL_Texture** texture, SDL_Renderer* renderer);
void drawTexture(SDL_Texture* texture, int x, int y, int width, int height, SDL_Renderer* renderer);

void drawTextureFrame(SDL_Texture* texture, int x, int y, int width, int height, int currentRow, int currentFrame,  SDL_Renderer* renderer);
