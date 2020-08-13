# initialize
from gpiozero import CPUTemperature
from RPLCD.i2c import CharLCD
from RPi import GPIO
import time

# init rotary encoder
clk = 17
dt  = 18
sw  = 27
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(sw, GPIO.IN, pull_up_down=GPIO.PUD_UP)
counter = 0
clkLastState = GPIO.input(clk)

# LCD
lcd = CharLCD('PCF8574', 0x27, cols=16, rows=2)


# Welcome message
lcd.write_string('Hey Kai, how are you doing?')
time.sleep(2)

def display_write(message=" ", x=0, y=0):
	lcd.cursor_pos = (y, x)
	lcd.write_string(message)

def exit():
	lcd.clear()
	lcd.write_string('Bye Bye')

def rotary_status():
	clkState = GPIO.input(clk)
	dtState = GPIO.input(dt)
	switch = GPIO.input(sw)
	global clkLastState,counter
	if clkState != clkLastState:
		if dtState != clkState:
			counter -= 1
		else:
			counter += 1
	clkLastState = clkState
	time.sleep(0.01)
	return(counter,switch)  # return count pstn and switch on or off

# main program loop
while True:
	counter=rotary_status()[0]
	switch=rotary_status()[1]

	display_write(str(counter),0,0)
	display_write(str(switch),0,1)
	time.sleep(0.05)
