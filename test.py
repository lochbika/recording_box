# initialize
from gpiozero import CPUTemperature
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


# Welcome message
lcd.write_string('Hey Kai, how are you doing?')
time.sleep(2)

def display_write(message=" ", x=0, y=0):
	lcd.clear()
	lcd.cursor_pos = (y, x)
	lcd.write_string(message)

def exit():
	lcd.clear()
	lcd.write_string('Bye Bye')

def rotary_status(increment):
	# init rotary encoder
	clk = 17
	dt  = 18
	sw  = 27
	inc = 0
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(sw, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	clkLastState = GPIO.input(clk)
	# the main daemon loop
	while True:
		clkState = GPIO.input(clk)
		dtState = GPIO.input(dt)
		switch = GPIO.input(sw)
		if clkState != clkLastState:
			print("rotary turned")
			if dtState != clkState:
				inc = 1
			else:
				inc = -1
			rot.append(inc)
		clkLastState = clkState
		time.sleep(0.01)

def signal_handler(sig, frame):
	exit()
	time.sleep(1)
	sys.exit(0)

# start the rotary switch daemon
#rotary_queue = Queue(maxsize = 5)
rot = deque([0,0,0,0,0],5)
rotary = threading.Thread(target=rotary_status, args = (rot, ), daemon = True)
rotary.start()
time.sleep(1)

# main program loop
if __name__ == "__main__":
	print("entering main part")
	while True:
		# check the rotary thread for new input
		#print("\nFull: ", rotary_queue.full())
		#print("\nEmpty: ", rotary_queue.empty())
		#print("epmty deque")
		while len(rot) > 1:
			item = rot.popleft()
			counter += item
			if counter > counter_max:
				counter = counter_min
			if counter < counter_min:
				counter = counter_max
			print(counter)
		if counter != inc_old:
			display_write(testset[counter],2,0)
			inc_old = counter

		# check for exit condition
		#signal.signal(signal.SIGINT, signal_handler)
		#signal.pause()

		# some delay to reduce CPU
		time.sleep(0.01)



