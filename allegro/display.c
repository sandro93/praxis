#include <stdio.h>
#include <allegro5/allegro.h>

int main(int argc, char *argv[])
{
  if(!al_init())
    {
      fprintf(stderr, "Failed to initialize allegro!\n");
      return -1;
    }

  ALLEGRO_DISPLAY *display = NULL;
  display = al_create_display(1024, 768);

  if(!display)
    {
      fprintf(stderr, "Failed to create the display.\n");
      return -1;
    }
  
  al_clear_to_color(al_map_rgb(0,0,0));
  al_flip_display();

  al_rest(10.0);
  
  al_destroy_display(display);
  return 0;
}
    
