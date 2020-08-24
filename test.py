# initialize
from gpiozero import LED
from RPLCD.i2c import CharLCD
from RPi import GPIO
import time
import threading
from collections import deque
import signal
import sys
import glob
import os
import LCDmenu

# some important paths
basepath = os.getcwd()

# LEDs
record_ledpin = 24
record_led = LED(record_ledpin)

# LCD
lcd = CharLCD('PCF8574', 0x27, cols=16, rows=2)

def display_write(message=" ", x=0, y=0, clear=1):
	if clear == 1:
		lcd.clear()
	lcd.cursor_pos = (y, x)
	lcd.write_string(message)

def exit():
	lcd.clear()
	lcd.write_string('Bye Bye')

# status variables for the differenct functionalities
recording = False
playing = False
idle = True
menu = False

# Define the main menu
Menu_labels = { "0":"List Recordings",
			"0.0":"Test.wav",
		"1":"Audio Settings",
			"1.0":"Sound Input",
				"1.0.0":"Refresh List",
			"1.1":"Input Volume",
			"1.2":"Sound Output",
				"1.2.0":"Refresh List",
			"1.3":"Output Volume",
		"2":"System Info",
			"2.0":"CPU Usage",
			"2.1":"CPU Temp"}

MainMenu = LCDmenu.LCDmenu(Menu_labels)

counter = 0
counter_max = 0

def standard_screen():
	display_write("=== READY! ===")
	display_write("Rec Play or Menu",y=1,clear=0)

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
			record.append(record_state)
			record_OLDstate = record_state
		if play_state != play_OLDstate:
			play.append(play_state)
			play_OLDstate = play_state
		if loop_state != loop_OLDstate:
			loop.append(loop_state)
			loop_OLDstate = loop_state
		if enter_state != enter_OLDstate:
			enter.append(enter_state)
			enter_OLDstate = enter_state
		time.sleep(0.05)

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
			rot.append(inc)

		# the following situation is for turning the knob clockwise (right)
		if clkState != clkLastState and clkState != dtState and clkState == 1:
			inc = 1
			rot.append(inc)
		# update the last state
		clkLastState = clkState
		# sleep
		time.sleep(0.003)

# declare list holding list of recordings and get the list of recordings
def get_recordingsList(path):
	recordings = glob.glob(path + "*.wav")
	basenames = []
	for i in  range(0,len(recordings)):
		basenames.append(os.path.splitext(os.path.basename(recordings[i]))[0])
	recordings = [basenames,recordings]
	return(recordings)

# Startup routine
def startup():
	# welcoe message ;)
	display_write("=== WELCOME! ===")
	# get the list of existing recordings and update the menu with it
	reclist = get_recordingsList(basepath + "/recordings/")
	MainMenu.replaceLevelItemList("0.",reclist[0])
	# save the filenames
	time.sleep(2)
	standard_screen()

# setup and start the rotary switch daemon
rot = deque([0,0,0,0,0],5)
rotary = threading.Thread(target=rotary_status, args = (rot, ), daemon = True)
rotary.start()
# setup and start the button hanler
record = deque([0],1)
play = deque([0],1)
loop = deque([0],1)
enter = deque([0],1)
buttons = threading.Thread(target=button_handler, args = (record,play,loop,enter, ), daemon = True)
buttons.start()

# main program
if __name__ == "__main__":
	# call the startup routine and then move on to the main part
	startup()
	while True:
		# check the rotary thread for new input
		while len(rot) > 0:
			item = rot.popleft()
			if menu:
				if item == 1:
					MainMenu.setNextItem()
				else:
					MainMenu.setPrevItem()
				display_write(MainMenu.AllItems[MainMenu.CurrentItem])

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
			if item is 0 and menu:
				if MainMenu.CurrentLevel == 0:
					standard_screen()
					idle = True
					menu = False
				else:
					MainMenu.levelAscent()
					display_write(MainMenu.AllItems[MainMenu.CurrentItem])
		while len(enter) > 0:
			item = enter.popleft()
			if item is 0 and idle:
				idle = False
				menu = True
				display_write(MainMenu.AllItems[MainMenu.CurrentItem])
			elif item is 0 and menu and not MainMenu.currentItemIsAction():
				MainMenu.levelDescent()
				display_write(MainMenu.AllItems[MainMenu.CurrentItem])


		# some delay to reduce CPU
		time.sleep(0.01)



