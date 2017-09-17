import time
import random

class chip8(object):
    ''' Chip8 Class, implements its run cycle and populates it graphics buffer

        Inherit from this class and provide the folliing functions
        render: Takes a single dimention array of the graphics buffer
        getKey: Should return -1 when no key is pressed, if a key is pressed
                return a value 0x0 - 0xF (0 - 15)

        Load a game by calling the load_rom function, it expects a byte array
        containing the bytes from a rom file ie, open with 'rb' on a rom file
    '''

    def __init__(self):
        # 16 Bit Regiseters, holds values (0x0 - 0xFFFF)
        # Index Register, indexes into memory
        self.I = 0
        # PC Register (program counter)
        self.PC = 0

        # 8 Bit Regiseters, holds values (0x0 - 0xFF)
        # 16 general purpose registers, 0x0 - 0xF
        # v[0xF] doubles as carry flag
        self.v = [0] * 0x10

        # Memory, 4096 bytes
        # In the original system, the first 512 (0x200) bytes
        # stored the actual interpreter
        # bytes 3744 - 3829 (0xEA0-0xEFF) callstack, internal use, other
        # butes 3840 - 4095 (0xF00-0xFFF) display refresh (not used?)
        self.ram = [0] * 0x1000

        # Address return stack
        # 24 levels at two bytes each
        self.stack = [0] * 0x30

        # Stack Pointer, index into stack
        self.SP = 0

        # Timers, decremented at 60Hz
        self.sound_timer = 0
        self.delay_timer = 0

        # Graphics Buffer
        # 64 x 32 resolution, 2048 pixels (0x800)
        self.gfx_buffer = [0] * 0x800
        self.draw = False

        # Value of pressed key
        self.key = -1

        # Comes with built in sprite set for displaying hex codes
        self.font_set = [
            0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
            0x20, 0x60, 0x20, 0x20, 0x70, # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
            0x90, 0x90, 0xF0, 0x10, 0x10, # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
            0xF0, 0x10, 0x20, 0x40, 0x40, # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90, # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
            0xF0, 0x80, 0x80, 0x80, 0xF0, # C
            0xE0, 0x90, 0x90, 0x90, 0xE0, # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
            0xF0, 0x80, 0xF0, 0x80, 0x80  # F
        ];


    def load_rom(self, rom_bytes):
        ''' Byte Array of ROM contents, ie open and read file as rb '''
        self.reset()
        # Rom data gets loaded directly into the system ram
        # starting at offset 512 (0x200)
        for i, byte in enumerate(rom_bytes):
            self.ram[0x200 + i] = byte;


    def reset(self):
        ''' Reset machine to initial state '''
        self.I = 0
        self.PC = 0x200
        self.v = [0] * 0x10
        self.ram = [0] * 0x1000
        self.stack = [0] * 0x30
        self.SP = 0
        self.sound_timer = 0
        self.delay_timer = 0
        self.gfx_buffer = [0] * 0x800
        self.draw = False
        self.key = -1
        # Font lives at 80 (0x50)
        for i, byte in enumerate(self.font_set):
            self.ram[0x50 + i] = byte;

    def run(self):
        # Timers decrease at 60Hz, 10 ticks per frame is a guess
        # that nets 600 ticks per second
        while True:
            start = time.time()
            self.key = self.getKey()
            for i in range(10):
                self.step()
            if (self.draw):
                self.render(self.gfx_buffer)
                self.draw = False
            if (self.delay_timer > 0):
                self.delay_timer = self.delay_timer - 1
            if (self.sound_timer > 0):
                self.sound_timer = self.sound_timer - 1
            stop = time.time()

            dt = 1.0/60 - (start - stop)
            if dt > 0:
                time.sleep(dt)


    def step(self):
        ''' Steps the emulation one time,
            fetchs opcode,
            decodes opcode,
            executes instruction '''
        # Fetch, op codes are 2 bytes
        op = (self.ram[self.PC] << 8) | self.ram[self.PC +1]
        self.PC = self.PC + 2

        # Decode
        # Most op codes can be determined via the top four bits
        # Some ops need the last four of eight bits
        # 0x0xxx, Not used
        # 0x00xx, 0x00xx
        # 0x8xxx, 0x8__x
        # 0xExxx, 0xE_xx
        # 0xFxxx, 0xF_xx
        # determine opcode
        op_code = op & 0xF000
        # 0, 1, 2, A, B
        nnn     = op & 0x0FFF
        # 3, 4, 6, 7, C
        kk      = op & 0x00FF
        # D
        n       = op & 0x000F
        # 3, 4, 5, 6, 7, 8, 9, C, D, E, F
        x       = (op & 0x0F00) >> 8;
        # 5, 8, D
        y       = (op & 0x00F0) >> 4;

        # Execute
        if (op_code == 0x0000):
            if (op == 0x00E0): self.__00E0()
            elif (op == 0x00EE): self.__00EE()
            else: raise ValueError ('Unknown opcode ', op)
        elif (op_code == 0x1000): self.__1NNN(nnn)
        elif (op_code == 0x2000): self.__2NNN(nnn)
        elif (op_code == 0x3000): self.__3XKK(x, kk)
        elif (op_code == 0x4000): self.__4XKK(x, kk)
        elif (op_code == 0x5000): self.__5XY0(x, y)
        elif (op_code == 0x6000): self.__6XKK(x, kk)
        elif (op_code == 0x7000): self.__7XKK(x, kk)
        elif (op_code == 0x8000):
            sub_op = op & 0x000F
            if (sub_op == 0):   self.__8XY0(x, y)
            elif (sub_op == 0x1): self.__8XY1(x, y)
            elif (sub_op == 0x2): self.__8XY2(x, y)
            elif (sub_op == 0x3): self.__8XY3(x, y)
            elif (sub_op == 0x4): self.__8XY4(x, y)
            elif (sub_op == 0x5): self.__8XY5(x, y)
            elif (sub_op == 0x6): self.__8XY6(x)
            elif (sub_op == 0x7): self.__8XY7(x, y)
            elif (sub_op == 0xE): self.__8XYE(x)
            else: raise ValueError ('Unknown opcode ', op)
        elif (op_code == 0x9000): self.__9XY0(x, y)
        elif (op_code == 0xA000): self.__ANNN(nnn)
        elif (op_code == 0xB000): self.__BNNN(nnn)
        elif (op_code == 0xC000): self.__CXKK(x, kk)
        elif (op_code == 0xD000): self.__DXYN(x, y, n)
        elif (op_code == 0xE000):
            sub_op = op & 0x00FF
            if (sub_op == 0x9E):   self.__EX9E(x)
            elif (sub_op == 0xA1): self.__EXA1(x)
            else: raise ValueError ('Unknown opcode ', op)
        elif (op_code == 0xF000):
            sub_op = op & 0x00FF
            if (sub_op == 0x07):   self.__FX07(x)
            elif (sub_op == 0x0A): self.__FX0A(x)
            elif (sub_op == 0x15): self.__FX15(x)
            elif (sub_op == 0x18): self.__FX18(x)
            elif (sub_op == 0x1E): self.__FX1E(x)
            elif (sub_op == 0x29): self.__FX29(x)
            elif (sub_op == 0x33): self.__FX33(x)
            elif (sub_op == 0x55): self.__FX55(x)
            elif (sub_op == 0x65): self.__FX65(x)
            else: raise ValueError ('Unknown opcode ', op)
        else: raise ValueError ('Unknown opcode ', op)

    # These are the 35 OP CODES
    # Descriptions taken from http://devernay.free.fr/hacks/chip8/C8TECH10.HTM
    # cowgods chip-8 documentation
    def __0NNN(self):
        '''
            Jump to a machine code routine at nnn.
            This instruction is only used on the old computers on which Chip-8
            was originally implemented. It is ignored by modern interpreters.
        '''
        pass

    def __00E0(self):
        ''' CLS
            Clear the display
        '''
        self.gfx_buffer = [0] * 0x800

    def __00EE(self):
        ''' RET
            Return from a subroutine.
            The interpreter sets the program counter to the address at the top
            of the stack, then subtracts 1 from the stack pointer.
        '''
        self.PC = self.stack[self.SP]
        self.SP = self.SP - 1

    def __1NNN(self, nnn):
        ''' JMP addr
            Jump to location nnn.
            The interpreter sets the program counter to nnn.
        '''
        self.PC = nnn;

    def __2NNN(self, nnn):
        ''' CALL addr
            Call subroutine at nnn.
            The interpreter increments the stack pointer, then puts the current
            PC on the top of the stack. The PC is then set to nnn.
        '''
        self.SP = self.SP + 1
        self.stack[self.SP] = self.PC
        self.PC = nnn

    def __3XKK(self, x, kk):
        ''' SE Vx, byte
            Skip next instruction if Vx = kk.
            The interpreter compares register Vx to kk, and if they are equal,
            increments the program counter by 2.
        '''
        if (self.v[x] == kk):
            self.PC = self.PC + 2

    def __4XKK(self, x, kk):
        ''' SNE Vx, byte
            Skip next instruction if Vx != kk.
            The interpreter compares register Vx to kk, and if they are not
            equal, increments the program counter by 2.
        '''
        if (self.v[x] != kk):
            self.PC = self.PC + 2

    def __5XY0(self, x, y):
        ''' SE Vx, Vy
            Skip next instruction if Vx = Vy.
            The interpreter compares register Vx to register Vy,
            and if they are equal, increments the program counter by 2.
        '''
        if (self.v[x] == self.v[y]):
            self.PC = self.PC + 2

    def __6XKK(self, x, kk):
        ''' LD Vx, byte
            Set Vx = kk.
            The interpreter puts the value kk into register Vx.
        '''
        self.v[x] = kk

    def __7XKK(self, x, kk):
        ''' ADD Vx, byte
            Set Vx = Vx + kk.
            Adds the value kk to the value of register Vx,
            then stores the result in Vx.
        '''
        self.v[x] = (self.v[x] + kk) & 0xFF

    def __8XY0(self, x, y):
        ''' LD Vx, Vy
            Set Vx = Vy.
            Stores the value of register Vy in register Vx.
        '''
        self.v[x] = self.v[y]

    def __8XY1(self, x, y):
        ''' OR Vx, Vy
            Set Vx = Vx OR Vy.
            Performs a bitwise OR on the values of Vx and Vy, then stores the
            result in Vx. A bitwise OR compares the corrseponding bits from
            two values, and if either bit is 1, then the same bit in the
            result is also 1. Otherwise, it is 0.
        '''
        self.v[x] = self.v[x] | self.v[y]

    def __8XY2(self, x, y):
        ''' AND Vx, Vy
            Set Vx = Vx AND Vy.
            Performs a bitwise AND on the values of Vx and Vy,
            then stores the result in Vx.  A bitwise AKD compares the
            corrseponding bits from two values, and if both bits are 1,
            then the same bit in the result is also 1. Otherwise, it is 0.
        '''
        self.v[x] = self.v[x] & self.v[y]

    def __8XY3(self, x, y):
        ''' XOR Vx, Vy
            Set Vx = Vx XOR Vy.
            Performs a bitwise exclusive OR on the values of Vx and Vy,
            then stores the result in Vx. An exclusive OR compares the
            corrseponding bits from two values, and if the bits are not both
            the same, then the corresponding bit in the result is set to 1.
            Otherwise, it is 0.
        '''
        self.v[x] = self.v[x] ^ self.v[y]

    def __8XY4(self, x, y):
        ''' ADD Vx, Vy
            Set Vx = Vx + Vy, set VF = carry.
            The values of Vx and Vy are added together. If the result is
            greater than 8 bits (i.e., > 255,) VF is set to 1, otherwise 0.
            Only the lowest 8 bits of the result are kept, and stored in Vx.
        '''
        result = self.v[x] + self.v[y]
        self.v[0xF] = 1 if result > 255 else 0
        self.v[x] = result & 0xFF

    def __8XY5(self, x, y):
        ''' SUB Vx, Vy
            Set Vx = Vx - Vy, set VF = NOT borrow.
            If Vx > Vy, then VF is set to 1, otherwise 0.
            Then Vy is subtracted from Vx, and the results stored in Vx.
        '''
        result = self.v[x] - self.v[y]
        self.v[0xF] = 1 if self.v[x] > self.v[y] else 0
        self.v[x] = result & 0xFF

    def __8XY6(self, x):
        ''' SHR Vx {, Vy}
            Set Vx = Vx SHR 1.
            If the least-significant bit of Vx is 1, then VF is set to 1,
            otherwise 0. Then Vx is divided by 2.
        '''
        self.v[0xF] = self.v[x] & 0x1
        # shifting by one is the same is int division
        self.v[x] = self.v[x] >> 1

    def __8XY7(self, x, y):
        ''' SUBN Vx, Vy
            Set Vx = Vy - Vx, set VF = NOT borrow.
            If Vy > Vx, then VF is set to 1, otherwise 0.
            Then Vx is subtracted from Vy, and the results stored in Vx.
        '''
        result = self.v[y] - self.v[x]
        self.v[0xF] = 1 if self.v[y] > self.v[x] else 0
        self.v[x] = result & 0xFF

    def __8XYE(self, x):
        ''' SHL Vx {, Vy}
            Set Vx = Vx SHL 1.
            If the most-significant bit of Vx is 1, then VF is set to 1,
            otherwise to 0. Then Vx is multiplied by 2.
        '''
        self.v[0xF] = (self.v[x] >> 7) & 0x1
        self.v[x] = (self.v[x] << 1) & 0xFF

    def __9XY0(self, x, y):
        ''' SNE Vx, Vy
            Skip next instruction if Vx != Vy.
            The values of Vx and Vy are compared, and if they are not equal,
            the program counter is increased by 2.
        '''
        if (self.v[x] != self.v[y]):
            self.PC = self.PC + 2

    def __ANNN(self, nnn):
        ''' LD I, addr
            Set I = nnn.
            The value of register I is set to nnn.
        '''
        self.I = nnn

    def __BNNN(self, nnn):
        ''' JP V0, addr
            Jump to location nnn + V0.
            The program counter is set to nnn plus the value of V0.
        '''
        self.PC = (nnn + self.v[0]) & 0xFFFF

    def __CXKK(self, x, kk):
        ''' RND Vx, byte
            Set Vx = random byte AND kk.
            The interpreter generates a random number from 0 to 255,
            which is then ANDed with the value kk.
            The results are stored in Vx.
            See instruction 8xy2 for more information on AND.
        '''
        self.v[x] = random.randint(0, 0xFF) & kk

    def __DXYN(self, x, y, n):
        ''' DRW Vx, Vy, nibble
            Display n-byte sprite starting at memory location I at (Vx, Vy),
            set VF = collision.
            The interpreter reads n bytes from memory, starting at the address
            stored in I. These bytes are then displayed as sprites on screen
            at coordinates (Vx, Vy). Sprites are XORed onto the existing
            screen. If this causes any pixels to be erased, VF is set to 1,
            otherwise it is set to 0. If the sprite is positioned so part of it
            is outside the coordinates of the display, it wraps around to the
            opposite side of the screen.
            See instruction 8xy3 for more information on XOR, and section 2.4,
            Display, for more information on the Chip-8 screen and sprites.
        '''
        vx = self.v[x]
        vy = self.v[y]
        self.v[0xF] = 0
        self.draw = True

        for yi in range(n):
            sprite_byte = self.ram[self.I + yi]
            pixels = [int(x) for x in format(sprite_byte, '08b')]
            for xi, pixel in enumerate(pixels):
                location = ((vy + yi) * 64) + ((vx + xi) % 64)
                if (pixel & self.gfx_buffer[location]) == 1:
                    self.v[0xF] = 1
                self.gfx_buffer[location] = self.gfx_buffer[location] ^ pixel


    def __EX9E(self, x):
        ''' SKP Vx
            Skip next instruction if key with the value of Vx is pressed.
            Checks the keyboard, and if the key corresponding to the value of
            Vx is currently in the down position, PC is increased by 2.
        '''
        if self.v[x] == self.key:
            self.PC = self.PC + 2


    def __EXA1(self, x):
        ''' SKNP Vx
            Skip next instruction if key with the value of Vx is not pressed.
            Checks the keyboard, and if the key corresponding to the value of
            Vx is currently in the up position, PC is increased by 2.
        '''
        if self.v[x] != self.key:
            self.PC = self.PC + 2

    def __FX07(self, x):
        ''' LD Vx, DT
            Set Vx = delay timer value.
            The value of DT is placed into Vx.
        '''
        self.v[x] = self.delay_timer

    def __FX0A(self, x):
        ''' LD Vx, K
            Wait for a key press, store the value of the key in Vx.
            All execution stops until a key is pressed, then the value of that
            key is stored in Vx.
        '''
        while (self.key == -1):
            self.key = self.getKey()
            if (self.key != -1):
                self.v[x] = self.key



    def __FX15(self, x):
        ''' LD DT, Vx
            Set delay timer = Vx.
            DT is set equal to the value of Vx.
        '''
        self.delay_timer = self.v[x]

    def __FX18(self, x):
        ''' LD ST, Vx
            Set sound timer = Vx.
            ST is set equal to the value of Vx.
        '''
        self.sound_timer = self.v[x]

    def __FX1E(self, x):
        ''' ADD I, Vx
            Set I = I + Vx.
            The values of I and Vx are added, and the results are stored in I.
        '''
        self.I = self.I + self.v[x]

    def __FX29(self, x):
        ''' LD F, Vx
            Set I = location of sprite for digit Vx.
            The value of I is set to the location for the hexadecimal sprite
            corresponding to the value of Vx. See section 2.4, Display,
            for more information on the Chip-8 hexadecimal font.
        '''
        self.I = self.v[x] * 5

    def __FX33(self, x):
        ''' LD B, Vx
            Store BCD representation of Vx in memory locations I, I+1, and I+2.
            The interpreter takes the decimal value of Vx, and places the
            hundreds digit in memory at location in I, the tens digit at
            location I+1, and the ones digit at location I+2.
        '''
        bcd = self.v[x]
        self.ram[self.I     ] = int(bcd // 100) % 10
        self.ram[self.I + 1 ] = int(bcd //  10) % 10
        self.ram[self.I + 2 ] = int(bcd //   1) % 10

    def __FX55(self, x):
        ''' LD [I], Vx
            Store registers V0 through Vx in memory starting at location I.
            The interpreter copies the values of registers V0 through Vx into
            memory, starting at the address in I.
        '''

        for i in range(x + 1):
            self.ram[self.I + i] = self.v[i]

    def __FX65(self, x):
        ''' LD Vx, [I]
            Read registers V0 through Vx from memory starting at location I.
            The interpreter reads values from memory starting at location I
            into registers V0 through Vx.
        '''
        for i in range(x + 1):
            self.v[i] = self.ram[self.I + i]
