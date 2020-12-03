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
