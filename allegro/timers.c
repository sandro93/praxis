#include <stdio.h>
#include <allegro5/allegro.h>

const float FPS = 60;

int main(int argc, char *argv[])
{
  if(!al_init())
    {
      fprintf(stderr, "Failed to initialize allegro!\n");
      return -1;
    }

  ALLEGRO_DISPLAY *display = NULL;
  ALLEGRO_EVENT_QUEUE *event_queue = NULL;
  ALLEGRO_TIMER *timer = NULL;

  bool redraw = true;

  timer = al_create_timer(1.0 / FPS);
  if(!timer)
    {
      fprintf(stderr, "failed to create the timer.\n");
      return -1;
    }

  display = al_create_display(1024, 768);

  if(!display)
    {
      fprintf(stderr, "Failed to create the display.\n");
      al_destroy_timer(timer);
      return -1;
    }

  event_queue = al_create_event_queue();
  if(!event_queue)
    {
      fprintf(stderr, "failed to create event queue.\n");
      al_destroy_display(display);
      al_destroy_timer(timer);
      return -1;
    }


  al_register_event_source(event_queue, al_get_display_event_source(display));
  al_register_event_source(event_queue, al_get_timer_event_source(timer));
  al_clear_to_color(al_map_rgb(0,0,0));
  al_flip_display();

  al_start_timer(timer);

  while(true)
    {
      ALLEGRO_EVENT ev;
      al_wait_for_event(event_queue, &ev);

      if(ev.type == ALLEGRO_EVENT_TIMER)
	redraw = true;
      else if(ev.type == ALLEGRO_EVENT_DISPLAY_CLOSE)
	{
	  fprintf(stderr, "display closed\n");
	  break;
	}

      if(redraw && al_is_event_queue_empty(event_queue))
	{
	  redraw = false;
	  al_clear_to_color(al_map_rgb(99, 99, 99));
	  al_flip_display();
	}
    }
  al_destroy_timer(timer);
  al_destroy_display(display);
  al_destroy_event_queue(event_queue);

  return 0;
}
    
