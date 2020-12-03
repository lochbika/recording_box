def dspwrite(dsp, message=" ", x=0, y=0, clear=1):
    if clear == 1:
        dsp.clear()
    dsp.cursor_pos = (y, x)
    dsp.write_string(message)


class display_screen(object):
    def __init__(self, lcd):
        self.lcd = lcd
        self.oldtext = "xxx2xxx"

    def __enter__(self):
        return(self)

    def __exit__(self, exception, value, traceback):
        self.close()

    def _lcdwrite(self, message=" ", x=0, y=0, clear=1):
        if clear == 1:
            self.lcd.clear()
        self.lcd.cursor_pos = (y, x)
        self.lcd.write_string(message)
        return

    def draw_screen(self, text):
        if text != self.oldtext:
            self._lcdwrite(text, clear=0)
            self.oldtext = text
        return

    def close(self):
        self._lcdwrite()
        return


class DSPcharacters(object):
    def __init__(self, lcd):
        self.lcd = lcd

    def load_progress(self):
        char1 = (0b10000,
                 0b10000,
                 0b10000,
                 0b11111,
                 0b10000,
                 0b10000,
                 0b10000,
                 0b00000)
        char2 = (0b01000,
                 0b01000,
                 0b01000,
                 0b11111,
                 0b01000,
                 0b01000,
                 0b01000,
                 0b00000)
        char3 = (0b00100,
                 0b00100,
                 0b00100,
                 0b11111,
                 0b00100,
                 0b00100,
                 0b00100,
                 0b00000)
        char4 = (0b00010,
                 0b00010,
                 0b00010,
                 0b11111,
                 0b00010,
                 0b00010,
                 0b00010,
                 0b00000)
        char5 = (0b00001,
                 0b00001,
                 0b00001,
                 0b11111,
                 0b00001,
                 0b00001,
                 0b00001,
                 0b00000)
        char6 = (0b01010,
                 0b01010,
                 0b01010,
                 0b01010,
                 0b01010,
                 0b01010,
                 0b01010,
                 0b01010)
        self.lcd.create_char(0, char1)
        self.lcd.create_char(1, char2)
        self.lcd.create_char(2, char3)
        self.lcd.create_char(3, char4)
        self.lcd.create_char(4, char5)
        self.lcd.create_char(5, char6)
        return

    def load_level(self):
        char1 = (0b11000,
                 0b11000,
                 0b11000,
                 0b11000,
                 0b11000,
                 0b11000,
                 0b11000,
                 0b11000)
        char2 = (0b01100,
                 0b01100,
                 0b01100,
                 0b11100,
                 0b11100,
                 0b01100,
                 0b01100,
                 0b01100)
        char3 = (0b00110,
                 0b00110,
                 0b01110,
                 0b11110,
                 0b11110,
                 0b01110,
                 0b00110,
                 0b00110)
        char4 = (0b00011,
                 0b00011,
                 0b00111,
                 0b11111,
                 0b11111,
                 0b00111,
                 0b00011,
                 0b00011)
        char5 = (0b00000,
                 0b00000,
                 0b00000,
                 0b11111,
                 0b11111,
                 0b00000,
                 0b00000,
                 0b00000)
        self.lcd.create_char(0, char1)
        self.lcd.create_char(1, char2)
        self.lcd.create_char(2, char3)
        self.lcd.create_char(3, char4)
        self.lcd.create_char(4, char5)
        return
