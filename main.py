#!/usr/bin/env python3
from chip8 import chip8
import curses
from curses import wrapper
import sys


with open(sys.argv[1], 'rb') as f:
    game_data = f.read();

f.close();

class CursesRenderer(chip8):
    def __init__(self, stdscr):
        self.stdscr = stdscr
        # Makes getch non-blocking
        self.stdscr.nodelay(True)
        chip8.__init__(self)
        # Hex Keypad, 0x0-0xF
        # 1,2,3,4     1,2,3,c
        # q,w,e,r     4,5,6,d
        # a,s,d,f     7,8,9,e
        # z,x,c,v     a,0,b,f
        self.keymap = {
             49: 0x1,  50: 0x2,  51: 0x3,  52: 0xC,
            113: 0x4, 119: 0x5, 101: 0x6, 114: 0xD,
             97: 0x7, 115: 0x8, 100: 0x9, 102: 0xE,
            122: 0xA, 120: 0x0,  99: 0xB, 118: 0xF
        }

    def getKey(self):
        return self.keymap.get(self.stdscr.getch(), -1)


    def load(self, game_data):
        self.load_rom(game_data)
        self.run()


    def render(self, gfx):
        """ Takes gfx array to render with curses
            array is 2080 in length, 32x64
        """
        # Clear screen
        self.stdscr.clear()

        for i, pixel in enumerate(gfx):
            x = i % 64
            y = i // 64
            if pixel == 1:
                self.stdscr.addch(y, x, 66)

        # Blit to screen
        self.stdscr.refresh()


def main(stdscr):
    # Setup Curses
    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    cr = CursesRenderer(stdscr)
    cr.load(game_data)

    cr.run()

wrapper(main)

