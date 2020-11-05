import AudioIO
import display_helper as dsphlp
import numpy as np
import time

def app_input_volsetting(lcd, device, nchannels, rate, btn):
	# global variables; LCD identifier, etc
	#global lcd

	# private variables
	running = True

	# open and start the stream
	rec = AudioIO.InputLeveller(channels=nchannels, rate=rate, device=device)
	rec_stream = rec.open()
	rec_stream.start_recording()
	# main loop of this app
	while running:
		# check the exit button for input
		while len(btn) > 0:
			item = btn.popleft()
			if item == 0:
				running = False
		# write the level to the LCD display
		dsphlp.dspwrite(lcd,'#'*int(round(rec_stream.get_level()*20,0)),x=0,y=1)
		time.sleep(0.2)

	rec_stream.stop_recording()
	rec_stream.close()

	return
	# reset the LCD to the previously shown menu item
	#dsphlp.dspwrite(lcd, MainMenu.AllItems[MainMenu.CurrentItem])

