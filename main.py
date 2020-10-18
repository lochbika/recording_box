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

# get menu items for audio input
def get_audioInputList():
	indices = []
	names = []
	p = pyaudio.PyAudio()
	for i in range(p.get_device_count()):
		if p.get_device_info_by_index(i).get('maxInputChannels') > 0:
			indices.append(i)
			dev_name = p.get_device_info_by_index(i).get('name')
			if len(dev_name) > 16:
				dev_name = dev_name[:14] + ".."
			names.append(dev_name)
	input_list = [indices,names]
	p.terminate()
	return(input_list)

def get_audioOutputList():
	indices = []
	names = []
	p = pyaudio.PyAudio()
	for i in range(p.get_device_count()):
		if p.get_device_info_by_index(i).get('maxOutputChannels') > 0:
			indices.append(i)
			dev_name = p.get_device_info_by_index(i).get('name')
			if len(dev_name) > 16:
				dev_name = dev_name[:14] + ".."
			names.append(dev_name)
	output_list = [indices,names]
	p.terminate()
	return(output_list)



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
	input_devices = get_audioInputList()
	MainMenu.replaceLevelItemList("1.0.",input_devices[1])
	# get output devices and put into menu
	output_devices = get_audioOutputList()
	MainMenu.replaceLevelItemList("1.2.",output_devices[1])
	# save the filenames
	time.sleep(1)
	standard_screen()

# audio related stuff
def audioplayer(file, action):

	loopA = 0
	loopB = 0
	active = False
	ctime = 0.0

	def startPlay(filename):
		wf = wave.open(filename, 'rb')

		# instantiate PyAudio (1)
		p = pyaudio.PyAudio()

		# define callback (2)
		def callback(in_data, frame_count, time_info, status_flags):
			data = wf.readframes(frame_count)
			return (data, pyaudio.paContinue)

		# open stream using callback (3)
		stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
				channels=wf.getnchannels(),
				rate=wf.getframerate(),
				output=True,
				stream_callback=callback)

		# start the stream (4)
		stream.start_stream()

		# return handlers
		return(wf, p, stream)

	def togglePause(stream_id):
		if stream_id.is_active():
			stream_id.stop_stream()
		else:
			stream_id.start_stream()

	def stopPlay(stream_id, wf_id, p_id):
		stream_id.stop_stream()
		stream_id.close()
		wf_id.close()
		p_id.terminate()

	def getPlayTime(wf_id):
		nframes = wf_id.getnframes()
		cframe = wf_id.tell()
		rate = wf_id.getframerate()
		return(round(cframe/rate,1),round(nframes/rate,1))

	while True:
		# read for communication with main thread
		while len(player_file) > 0:
			item = player_file.popleft()
			playID = startPlay(item)
			active = True

		while len(player_action) > 0:
			item = action.popleft()
			if item == "toggle" and active:
				togglePause(playID[2])
			if item == "stop" and active:
				stopPlay(playID[2],playID[0],playID[1])
				del playID
				loopA = 0
				loopB = 0
				active = False
				time.sleep(0.1)
			if item == "startLoop" and active:
				loopA = playID[0].tell()
			if item == "stopLoop" and active:
				loopB = playID[0].tell()
			if item == "quitLoop" and active:
				print("message received")
				loopA = 0
				loopB = 0

		if active:
			ctime = getPlayTime(playID[0])[0]
			#print(ctime)
			#dsphlp.dspwrite(lcd, str(ctime),y=1,clear=0)
			if loopA != 0 and loopB != 0:
				if playID[0].tell() > loopB:
					playID[0].setpos(loopA)

		time.sleep(0.05)

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

# setup communicator with wave playing thread
player_file = deque([],1)
player_action = deque([],3)
player = threading.Thread(target=audioplayer, args = (player_file, player_action, ), daemon = True)
player.start()

# setup the system monitor thread
#sysmon = threading.Thread(target=smon.sysmonitor)
#sysmon = smon.sysmonitor()

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
					print("message sent")
					player_action.append("quitLoop")
					looping = False
				if playing:
					player_action.append("stop")
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
				player_file.append(reclist[1][selectedrecording])
				playing = True
			elif playing:
				player_action.append("toggle")
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
				player_action.append("startLoop")
				looping = True
			elif item is 0 and playing and looping:
				player_action.append("stopLoop")

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
				player_action.append("quitLoop")
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
					rec = AudioIO.InputLeveller(channels=1, rate=48000, device=0)
					rec_stream = rec.open()
					rec_stream.start_recording()
					while True:
						time.sleep(0.1)
						dsphlp.dspwrite(lcd,'#'*round(rec_stream.get_level()*20,0).astype(int),x=0,y=1)
		
		if recording:
			recording_screen(rec_stream.get_recordingtime())

		# special section for the shutdown timer
		if shutdown_bit:
			shutdown_timer = time.time() - start_time
			dsphlp.dspwrite(lcd, str(5 - round(shutdown_timer)) + " seconds",x=2,y=1,clear=0)
			if shutdown_timer > 5:
				os.system("sudo shutdown -h now")
			time.sleep(0.05)

		# some delay to reduce CPU
		time.sleep(0.01)



