CXX=g++
CFLAGS=-std=gnu++1y  `root-config --cflags --glibs` 
DEBUG=-Wall
EXEC=CheckPadPattern

all: $(EXEC)

CheckPadPattern: main.cpp
	 $(CXX) $(CFLAGS) $(DEBUG) $^ -o $@


clean:
	rm -rf  $(EXEC)


.PHONY: clean
