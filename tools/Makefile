.PHONY: all clean

CC := gcc
CFLAGS := -O3 -std=c11 -Wall -Wextra -pedantic
PYTHON ?= python
RMFILES ?= $(PYTHON) rm_files.py

tools := \
	gbcpal \
	gfx \
	lzcomp \
	make_patch \
	png_dimensions \
	scan_includes \
	stadium

all: $(tools)
	@:

clean:
	$(RMFILES) $(tools)

lzcomp: CFLAGS += -Wno-strict-overflow -Wno-sign-compare
lzcomp: $(wildcard lz/*.c) $(wildcard lz/*.h)
	$(CC) $(CFLAGS) -o $@ lz/*.c

%: %.c common.h
	$(CC) $(CFLAGS) -o $@ $<
