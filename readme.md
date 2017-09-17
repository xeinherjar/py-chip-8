## Chip-8 Emulator (core) written in Python

Chip-8 is a simple machine to emulate, this was built to give me more exposure to Python.
The code should be very easy to read.  This was implemented as a backend, a
Curses based frontend is included and can be run from the terminal
`./main.py <path_to_chip8_rom>`

## Using this as a library
  -  Have your class inherit from chip8
  -  Implement render and getKey

### render
Takes the graphics buffer, which is a single dimension array consisting 2048
pixels with the value of 1 or 0.  Resolution is 64 x 32.

### getKey
Should return -1 when no key is pressed, if a key is pressed return a
value 0x0 - 0xF (0 - 15)


