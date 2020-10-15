from RPLCD.i2c import CharLCD

def dspwrite(dsp, message=" ", x=0, y=0, clear=1):
	if clear == 1:
		dsp.clear()
	dsp.cursor_pos = (y, x)
	dsp.write_string(message)
