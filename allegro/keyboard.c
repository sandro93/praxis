#include <stdio.h>
#include <allegro5/allegro.h>

#define FPS 60
#define SCREEN_W 1024
#define SCREEN_H 768
#define BOUNCER_SIZE 32

enum ARROW_KEYS
  {
    UP, RIGHT, DOWN, LEFT
  };
  

void change_color(ALLEGRO_BITMAP *, ALLEGRO_COLOR, ALLEGRO_BITMAP *);
void destroy_resources(void);

ALLEGRO_DISPLAY *display = NULL;
ALLEGRO_EVENT_QUEUE *event_queue = NULL;
ALLEGRO_TIMER *timer = NULL;
ALLEGRO_BITMAP *bouncer = NULL;

int main(int argc, char *argv[])
{

  struct Bouncer
  {
    float x, y, dx, dy, size;
  } rect;

  if(!al_init())
    {
      fprintf(stderr, "failed to initialize allegro!\n");
      return -1;
    }

  

  rect.x = SCREEN_W / 2.0 - BOUNCER_SIZE / 2.0;
  rect.y = SCREEN_H / 2.0 - BOUNCER_SIZE / 2.0;
  rect.dx = -4.0, rect.dy = 4.0;
  rect.size = BOUNCER_SIZE;

  bool key[4] = {false, false, false, false};
  bool doexit = false;  
  bool redraw = true;

  timer = al_create_timer(1.0 / FPS);
  if(!timer)
    {
      fprintf(stderr, "couldn't initialize timer.\n");
      return -1;
    }

  display = al_create_display(SCREEN_W, SCREEN_H);
  if(!display)
    {
      fprintf(stderr, "failed to create the display.\n");
      al_destroy_timer(timer);

      return -1;
    }
  
  if(!al_install_keyboard())
    {
      fprintf(stderr, "failed to initialize keyboard.\n");
      al_destroy_display(display);
      al_destroy_timer(timer);

      return -1;
    }

  bouncer = al_create_bitmap(BOUNCER_SIZE, BOUNCER_SIZE);
  if(!bouncer)
    {
      fprintf(stderr, "couldn't create bitmap.\n");
      al_destroy_timer(timer);
      al_destroy_display(display);
      return -1;
    }
  
  
  event_queue = al_create_event_queue();
  if(!event_queue)
    {
      fprintf(stderr, "failed to create event queue.\n");
      al_destroy_bitmap(bouncer);
      al_destroy_display(display);
      al_destroy_timer(timer);
      return -1;
    }

  al_register_event_source(event_queue, al_get_keyboard_event_source());
  al_register_event_source(event_queue, al_get_display_event_source(display));
  al_register_event_source(event_queue, al_get_timer_event_source(timer));

  al_set_target_bitmap(bouncer);
  al_clear_to_color(al_map_rgb(255, 0, 255));
  al_set_target_bitmap(al_get_backbuffer(display));

  al_clear_to_color(al_map_rgb(0,0,0));
  al_flip_display();

  al_start_timer(timer);

  while(!doexit)
    {
      ALLEGRO_EVENT ev;
      al_wait_for_event(event_queue, &ev);
      
      if(ev.type == ALLEGRO_EVENT_TIMER)
	{
	  if(key[UP] && rect.y >= 4.0)
	    {
	      rect.y -= 4.0;
	      change_color(bouncer, al_map_rgb(99, 255, 99), al_get_backbuffer(display));
	    }
	  if(key[RIGHT] && rect.x <= SCREEN_W - rect.size - 4.0)
	    rect.x += 4.0;

	  if(key[DOWN] && rect.y <= SCREEN_H - rect.size - 4.0)
	    rect.y += 4.0;

	  if(key[LEFT] && rect.x >= 4.0)
	    rect.x -= 4.0;

	  redraw = true;
	}
      else if(ev.type == ALLEGRO_EVENT_KEY_DOWN)
	{
	  switch(ev.keyboard.keycode)
	    {
	    case ALLEGRO_KEY_UP:
	      key[UP] = true;
	      break;
	    case ALLEGRO_KEY_RIGHT:
	      key[RIGHT] = true;
	      break;
	    case ALLEGRO_KEY_DOWN:
	      key[DOWN] = true;
	      break;
	    case ALLEGRO_KEY_LEFT:
	      key[LEFT] = true;
	      break;
	    }
	}
      else if(ev.type == ALLEGRO_EVENT_KEY_UP)
	{
	 switch(ev.keyboard.keycode)
	    {
	    case ALLEGRO_KEY_UP:
	      key[UP] = false;
	      break;
	    case ALLEGRO_KEY_RIGHT:
	      key[RIGHT] = false;
	      break;
	    case ALLEGRO_KEY_DOWN:
	      key[DOWN] = false;
	      break;
	    case ALLEGRO_KEY_LEFT:
	      key[LEFT] = false;
	      break;
	    case ALLEGRO_KEY_ESCAPE:
	      doexit = true;
	      break;
	    }
	} 
    
      if(redraw && al_is_event_queue_empty(event_queue))
	{
	  redraw = false;
	  al_clear_to_color(al_map_rgb(0, 0, 0));

	  al_draw_bitmap(bouncer, rect.x, rect.y, 0);
	  al_flip_display();
	}
    }

  al_destroy_bitmap(bouncer);
  al_destroy_timer(timer);
  al_destroy_display(display);
  al_destroy_event_queue(event_queue);

  return 0;
}   
    
void change_color(ALLEGRO_BITMAP *obj, ALLEGRO_COLOR color, ALLEGRO_BITMAP *context)
{
  al_set_target_bitmap(obj);
  al_clear_to_color(color);
  al_set_target_bitmap(context);
  al_flip_display();
}

void destroy_resources(void)
{
  if(bouncer)
    al_destroy_bitmap(bouncer);
  if(timer)
    al_destroy_timer(timer);
  if(display)
    al_destroy_display(display);
  if(event_queue)
    al_destroy_event_queue(event_queue);
}
