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
import AudioIO

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
looping = False
idle = True
menu = False
shutdown_timer = 0
shutdown_bit = False

# audio I/O related variables
input_rate = 0
input_channels = 1
output_rate = 44100
output_channels = 2

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
			"2.2":"Storage",
			"2.0":"CPU Usage",
			"2.1":"CPU Temp"}

MainMenu = LCDmenu.LCDmenu(Menu_labels)

counter = 0
counter_max = 0

def standard_screen():
	display_write("==== READY! ====")
	display_write("Rec,Play or Menu",y=1,clear=0)

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
			names.append(p.get_device_info_by_index(i).get('name'))
	output_list = [indices,names]
	p.terminate()
	return(output_list)


# Startup routine
def startup():
	global reclist
	global input_devices
	# welcoe message ;)
	display_write("=== WELCOME! ===")
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
	time.sleep(2)
	standard_screen()

# audio related stuff
def audioplayer(file,action):

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
			# get average audio level over all channels
			#try:
			#	levels = []
			#	for _i in range(frame_count):
			#		levels.append(abs(struct.unpack('<h', data[_i:_i + 2])[0]))
			#	avg_chunk = sum(levels)/len(levels)
			#	print(str(round(avg_chunk,0)))
			#	display_write(str(round(avg_chunk,0)), y=1, clear=0)
			#except:
			#	pass
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
			if item == "toggle":
				togglePause(playID[2])
			if item == "stop":
				stopPlay(playID[2],playID[0],playID[1])
				del playID
				loopA = 0
				loopB = 0
				active = False
				time.sleep(0.1)
			if item == "startLoop":
				loopA = playID[0].tell()
			if item == "stopLoop":
				loopB = playID[0].tell()
			if item == "quitLoop":
				print("message received")
				loopA = 0
				loopB = 0

		if active:
			ctime = getPlayTime(playID[0])[0]
			#print(ctime)
			#display_write(str(ctime),y=1,clear=0)
			if loopA != 0 and loopB != 0:
				if playID[0].tell() > loopB:
					playID[0].setpos(loopA)

		time.sleep(0.05)

def audiorecorder(file,action):

	def startRecording():
		print("bla")

	while True:
		while len(player_action) > 0:
			item = action.popleft()
			if item == "bla":
				time.sleep(0.1)

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
				if item == 1:
					MainMenu.setNextItem()
				else:
					MainMenu.setPrevItem()
				display_write(MainMenu.AllItems[MainMenu.CurrentItem])

		# check the buttons thread for new input
		while len(record) > 0:
			item = record.popleft()
			if item is 0 and idle:
				print("Button RECORD pressed",item)
				idle = False
				recording = True
				rec = AudioIO.Recorder()
				rec_stream = rec.open(fname = basepath + "/recordings/" + "test.wav")
				rec_stream.start_recording()
				record_led.blink()
			if item is 1 and recording:
				print("Button RECORD released",item)
				idle = True
				recording = False
				rec_stream.stop_recording()
				rec_stream.close()
				record_led.off()
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
					display_write(MainMenu.AllItems[MainMenu.CurrentItem])
			elif item is 0 and idle:
				shutdown_bit = True
				start_time = time.time()
				shutdown_timer = time.time() - start_time
				display_write("Shutdown in:")
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
				display_write(MainMenu.AllItems[MainMenu.CurrentItem])
			elif item is 0 and menu and not MainMenu.currentItemIsAction():
				MainMenu.levelDescent()
				display_write(MainMenu.AllItems[MainMenu.CurrentItem])
			elif looping:
				player_action.append("quitLoop")
				looping = False
			elif item is 0 and menu and MainMenu.currentItemIsAction():
				if MainMenu.CurrentItem == '2.1':
					display_write("Temperature:")
					display_write(str(round(CPUTemperature().temperature))+" degC",x=5,y=1,clear=0)
				if MainMenu.CurrentItem == '2.2':
					statvfs = os.statvfs(basepath)
					fs_free = (statvfs.f_frsize * statvfs.f_bavail)/1000000000
					fs_fullpercent = fs_free/((statvfs.f_frsize * statvfs.f_blocks)/1000000000)
					display_write("FS: " +
						str(round(fs_free,2)) +
						" GB free")
					display_write(str(round(100-fs_fullpercent*100,2)) +
						" % full", x=3, y=1, clear=0)

		# special section for the shutdown timer
		if shutdown_bit:
			shutdown_timer = time.time() - start_time
			display_write(str(5 - round(shutdown_timer)) + " seconds",x=2,y=1,clear=0)
			if shutdown_timer > 5:
				os.system("sudo shutdown -h now")
			time.sleep(0.05)

		# some delay to reduce CPU
		time.sleep(0.01)



