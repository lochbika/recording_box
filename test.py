# initialize
from gpiozero import LED
from RPLCD.i2c import CharLCD
from RPi import GPIO
import time
import threading
from collections import deque
import signal
import sys

testset = ["Hello","World","Kai","Maria","Max", "Vinzenz"]

counter = 0
counter_max = len(testset)-1
counter_min = 0
inc_old = 0
inc_new = 0

# LCD
lcd = CharLCD('PCF8574', 0x27, cols=16, rows=2)

# LEDs
record_ledpin = 24
record_led = LED(record_ledpin)

# Welcome message
lcd.write_string('Hey Kai, how are you doing?')
time.sleep(2)

def display_write(message=" ", x=0, y=0, clear=1):
	if clear == 1:
		lcd.clear()
	lcd.cursor_pos = (y, x)
	lcd.write_string(message)

def exit():
	lcd.clear()
	lcd.write_string('Bye Bye')

# this function handles all button presses
def button_handler(record,play,loop,enter):
	# the current states of all buttons
	record_state = 0
	play_state = 0
	loop_state = 0
	enter_state = 0
	# last known states
	record_OLDstate = 0
	play_OLDstate = 0
	loop_OLDstate = 0
	enter_OLDstate = 0

	#initiate the GPIO pins
	record_pin = 4
	play_pin = 22
	loop_pin = 23
	enter_pin = 27
	GPIO.setup(record_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(play_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(loop_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(enter_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	# the event loop
	while True:
		record_state = GPIO.input(record_pin)
		play_state = GPIO.input(play_pin)
		loop_state = GPIO.input(loop_pin)
		enter_state = GPIO.input(enter_pin)
		if record_state != record_OLDstate:
			#print("Button RECORD pressed!", record_state)
			record.append(record_state)
			record_OLDstate = record_state
		if play_state != play_OLDstate:
			#print("Button PLAY pressed!", play_state)
			play.append(play_state)
			play_OLDstate = play_state
		if loop_state != loop_OLDstate:
			#print("Button LOOP pressed!", loop_state)
			loop.append(loop_state)
			loop_OLDstate = loop_state
		if enter_state != enter_OLDstate:
			#print("Button ENTER pressed!", enter_state)
			enter.append(enter_state)
			enter_OLDstate = enter_state
		time.sleep(0.1)

def rotary_status(increment):
	# init rotary encoder
	clk = 17
	dt  = 18
	inc = 0
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	clkLastState = GPIO.input(clk)
	# the main daemon loop
	while True:
		clkState = GPIO.input(clk)
		dtState = GPIO.input(dt)
		# the following situation is for turning the knob anti-clockwise (left)
		if clkState != clkLastState and clkState == dtState and clkState == 1:
			inc = -1
			#print("turning CCW")
			#print("clk State:",clkState)
			#print("dt  State:",dtState)
			rot.append(inc)

		# the following situation is for turning the knob clockwise (right)
		if clkState != clkLastState and clkState != dtState and clkState == 1:
			inc = 1
			#print("turning CW")
			#print("clk State:",clkState)
			#print("dt  State:",dtState)
			rot.append(inc)
		# update the last state
		clkLastState = clkState
		# sleep
		time.sleep(0.003)

def signal_handler(sig, frame):
	exit()
	time.sleep(1)
	sys.exit(0)

# start the rotary switch daemon
#rotary_queue = Queue(maxsize = 5)
rot = deque([0,0,0,0,0],5)
rotary = threading.Thread(target=rotary_status, args = (rot, ), daemon = True)
record = deque([0],1)
play = deque([0],1)
loop = deque([0],1)
enter = deque([0],1)
buttons = threading.Thread(target=button_handler, args = (record,play,loop,enter, ), daemon = True)
rotary.start()
buttons.start()
time.sleep(1)

# main program loop
if __name__ == "__main__":
	print("entering main part")
	while True:
		# check the rotary thread for new input
		while len(rot) > 0:
			item = rot.popleft()
			counter += item
			if counter > counter_max:
				counter = counter_min
			if counter < counter_min:
				counter = counter_max
			print(counter)
		if counter != inc_old:
			display_write(str(counter),0,0)
			display_write(testset[counter],2,0,clear=0)
			inc_old = counter

		# check the buttons thread for new input
		while len(record) > 0:
			item = record.popleft()
			if item is 0:
				print("Button RECORD pressed",item)
				record_led.blink()
			if item is 1:
				print("Button RECORD released",item)
				record_led.off()
		while len(play) > 0:
			item = play.popleft()
			if item is 0:
				print("Button PLAY pressed",item)
			if item is 1:
				print("Button PLAY released",item)
		while len(loop) > 0:
			item = loop.popleft()
			if item is 0:
				print("Button LOOP pressed",item)
			if item is 1:
				print("Button LOOP released",item)
		while len(enter) > 0:
			item = enter.popleft()
			if item is 0:
				print("Button ENTER pressed",item)
			if item is 1:
				print("Button ENTER released",item)


		# check for exit condition
		#signal.signal(signal.SIGINT, signal_handler)
		#signal.pause()

		# some delay to reduce CPU
		time.sleep(0.01)



