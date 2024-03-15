CXX = g++
CXXFLAGS = -std=c++17 -Wall

ifeq ($(TYPE), float)
CXXFLAGS += -DUSE_FLOAT
else ifeq ($(TYPE), double)
CXXFLAGS += -DUSE_DOUBLE
else
$(error Please specify array type: TYPE=float or TYPE=double)
endif

.PHONY: all clean

all: main

main: main.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

clean:
	rm -f main