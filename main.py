# initialize
from gpiozero import LED
from gpiozero import CPUTemperature
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
import pyaudio
import wave
import struct
from datetime import datetime
import configparser as cfp

# custom modules
import AudioIO
import display_helper as dsphlp
import gbapps

# some important paths
basepath = os.getcwd()

# base configuration
config = cfp.ConfigParser()
config.read(basepath + "/config/default.cfg")

# audio I/O related variables
input_device = AudioIO.get_deviceid_byname(config['AUDIO_INPUT']['name'])
input_rate = 48000
input_channels = 1

output_device = AudioIO.get_deviceid_byname(config['AUDIO_OUTPUT']['name'])
output_rate = 44100
output_channels = 2

# LEDs
record_ledpin = 24
record_led = LED(record_ledpin)

# LCD
lcd = CharLCD('PCF8574', 0x27, cols=20, rows=4)

# status variables for the differenct functionalities
recording = False
playing = False
looping = False
idle = True
menu = False
shutdown_timer = 0
shutdown_bit = False

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
			"2.1":"CPU Temp",
			"2.2":"Storage"}

MainMenu = LCDmenu.LCDmenu(Menu_labels)

counter = 0
counter_max = 0

def standard_screen():
	dsphlp.dspwrite(lcd, "====== READY! ======")
	dsphlp.dspwrite(lcd, "Record, Play or Menu",y=1,clear=0)

def recording_screen(t="00:00"):
	if t != None:
		if t == "00:00" or t == "00:01":
			dsphlp.dspwrite(lcd, "==== RECORDING! ====")
			dsphlp.dspwrite(lcd, "Length: " + t,y=1,clear=0)
			time.sleep(0.5)
		else:
			dsphlp.dspwrite(lcd, t,x=8,y=1,clear=0)

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
	if len(recordings) > 0:
		recordings.sort(reverse = True)
		basenames = []
		for i in  range(0,len(recordings)):
			basenames.append(os.path.splitext(os.path.basename(recordings[i]))[0])
		recordings = [basenames,recordings]
	else:
		recordings = [["No recordings"],[""]]
	return(recordings)

# Startup routine
def startup():
	global reclist
	global input_devices
	# welcoe message ;)
	dsphlp.dspwrite(lcd, "===== WELCOME! =====")
	# get the list of existing recordings and update the menu with it
	reclist = get_recordingsList(basepath + "/recordings/")
	MainMenu.replaceLevelItemList("0.",reclist[0])
	# get input devices and put into menu
	input_devices = AudioIO.get_audioInputList()
	MainMenu.replaceLevelItemList("1.0.",input_devices[1])
	# get output devices and put into menu
	output_devices = AudioIO.get_audioOutputList()
	MainMenu.replaceLevelItemList("1.2.",output_devices[1])
	# save the filenames
	time.sleep(1)
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
				if looping:
					print("looper action - implement this!")
					looping = False
				if playing:
					player_stream.stop_playing()
					player_stream.close()
					play_screen.close()
					playing = False
				if item == -1:
					MainMenu.setNextItem()
				elif item == 1:
					MainMenu.setPrevItem()
				dsphlp.dspwrite(lcd, MainMenu.AllItems[MainMenu.CurrentItem])

		# check the buttons thread for new input
		while len(record) > 0:
			item = record.popleft()
			if item is 0 and idle:
				dsphlp.dspwrite(lcd, "==== RECORDING! ====")
				idle = False
				recording = True
				rec = AudioIO.Recorder(channels=input_channels, rate=input_rate, device=input_device)
				rec_stream = rec.open(fname = basepath + "/recordings/" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".wav")
				rec_stream.start_recording()
				record_led.blink()
			if item is 1 and recording:
				print("Button RECORD released",item)
				idle = True
				recording = False
				rec_stream.stop_recording()
				rec_stream.close()
				#time.sleep(0.5)
				reclist = get_recordingsList(basepath + "/recordings/")
				MainMenu.replaceLevelItemList("0.",reclist[0])
				record_led.off()
				standard_screen()
		while len(play) > 0:
			item = play.popleft()
			if item is 0 and menu and MainMenu.CurrentItem.startswith("0.") and not playing:
				selectedrecording = int(MainMenu.CurrentItem.split(".")[MainMenu.CurrentLevel])
				player = AudioIO.Player(channels=output_channels, rate=output_rate, device=output_device)
				player_stream = player.open(reclist[1][selectedrecording])
				player_stream.start_playing()
				play_screen = dsphlp.display_screen(lcd)
				playing = True
			elif playing:
				player_stream.toggle()
		while len(loop) > 0:
			item = loop.popleft()
			if item is 0 and menu and not playing:
				if MainMenu.CurrentLevel == 0:
					standard_screen()
					idle = True
					menu = False
				else:
					MainMenu.levelAscent()
					dsphlp.dspwrite(lcd, MainMenu.AllItems[MainMenu.CurrentItem])
			elif item is 0 and idle:
				shutdown_bit = True
				start_time = time.time()
				shutdown_timer = time.time() - start_time
				dsphlp.dspwrite(lcd, "Shutdown in:")
			elif item is 1 and idle and shutdown_timer > 0:
				shutdown_bit = False
				shutdown_timer = 0
				standard_screen()
			# handle the initiation and termination of a playing loop
			elif item is 0 and playing and not looping:
				print("startLoop - implement this!")
				looping = True
			elif item is 0 and playing and looping:
				print("stopLoop - implement this")

		while len(enter) > 0:
			item = enter.popleft()
			if item is 0 and idle:
				idle = False
				menu = True
				dsphlp.dspwrite(lcd, MainMenu.AllItems[MainMenu.CurrentItem])
			elif item is 0 and menu and not MainMenu.currentItemIsAction():
				MainMenu.levelDescent()
				dsphlp.dspwrite(lcd, MainMenu.AllItems[MainMenu.CurrentItem])
			elif looping:
				print("quitLoop - implement this!")
				looping = False
			elif item is 0 and menu and MainMenu.currentItemIsAction():
				# system monitor
				if MainMenu.CurrentItem == '2.1':
					dsphlp.dspwrite(lcd, "Temperature:")
					dsphlp.dspwrite(lcd, str(round(CPUTemperature().temperature))+" degC",x=5,y=1,clear=0)
				if MainMenu.CurrentItem == '2.2':
					statvfs = os.statvfs(basepath)
					fs_free = (statvfs.f_frsize * statvfs.f_bavail)/1000000000
					fs_fullpercent = fs_free/((statvfs.f_frsize * statvfs.f_blocks)/1000000000)
					dsphlp.dspwrite(lcd, "FS: " +
						str(round(fs_free,2)) +
						" GB free")
					dsphlp.dspwrite(lcd, str(round(100-fs_fullpercent*100,2)) +
						" % full", x=3, y=1, clear=0)
				if MainMenu.CurrentItem == '2.3':
					sysmon.start()
				# input level
				if MainMenu.CurrentItem == '1.1':
					app = threading.Thread(target=gbapps.app_input_volsetting, args = (lcd, input_device, input_channels, input_rate, loop, ), daemon = False)
					app.start()
				# if MainMenu.CurrentItem == '1.1':
					# rec = AudioIO.InputLeveller(channels=1, rate=48000, device=0)
					# rec_stream = rec.open()
					# rec_stream.start_recording()
					# while True:
						# time.sleep(0.2)
						# dsphlp.dspwrite(lcd,'#'*round(rec_stream.get_level()*20,0).astype(int),x=0,y=1)
		if recording:
			recording_screen(rec_stream.get_recordingtime())

		# special section for the shutdown timer
		if shutdown_bit:
			shutdown_timer = time.time() - start_time
			dsphlp.dspwrite(lcd, str(5 - round(shutdown_timer)) + " seconds",x=2,y=1,clear=0)
			if shutdown_timer > 5:
				os.system("sudo shutdown -h now")
			time.sleep(0.05)

		if playing:
			play_screen.draw_screen(player_stream.get_pos_formatted())
			#dsphlp.dspwrite(lcd, player_stream.get_pos_formatted())
			#time.sleep(0.2)

		# some delay to reduce CPU
		time.sleep(0.01)
