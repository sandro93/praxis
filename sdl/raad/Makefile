PREFIX=/usr/local
CC=gcc
W=-Wall -Wextra -Wstrict-prototypes -Wshadow -Wwrite-strings \
-Wold-style-definition -Wredundant-decls -Wnested-externs \
-Wmissing-include-dirs
CFLAGS=-I/usr/include/SDL2 -D_REENTRANT -L/usr/lib -lSDL2 -lSDL2_image -lpthread -lm -p -g $(W)
objects = raad.o texture.o vector.o

raad : $(objects)
	$(CC) $(CFLAGS) -o raad $(objects)

raad.o: raad.h ledge.h

texture.o: texture.h

vector.o: vector.h

.PHONY : clean

clean :
	rm raad $(objects)

