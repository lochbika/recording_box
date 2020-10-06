import pyaudio
import wave
import time
from math import floor

class Recorder(object):
	'''A recorder class for recording audio to a WAV file.
	Records in mono by default.
	'''

	def __init__(self, channels=1, rate=48000, frames_per_buffer=1048, device = 0):
		self.channels = channels
		self.rate = rate
		self.frames_per_buffer = frames_per_buffer
		self.device = device

	def open(self, fname, mode='wb'):
		return RecordingFile(fname, mode, self.channels, self.rate,
		                    self.frames_per_buffer,self.device)

class RecordingFile(object):
	def __init__(self, fname, mode, channels,
		rate, frames_per_buffer, device):
		self.fname = fname
		self.mode = mode
		self.channels = channels
		self.rate = rate
		self.frames_per_buffer = frames_per_buffer
		self._pa = pyaudio.PyAudio()
		self.wavefile = self._prepare_file(self.fname, self.mode)
		self._stream = None
		self.device = device
		self.starttime = time.time()
		self.lasttimecheck = time.time()

	def __enter__(self):
		return self

	def __exit__(self, exception, value, traceback):
		self.close()

	def start_recording(self):
		# Use a stream with a callback in non-blocking mode
		self._stream = self._pa.open(format=pyaudio.paInt16,
			channels=self.channels,
			rate=self.rate,
			input=True,
			input_device_index=self.device,
			frames_per_buffer=self.frames_per_buffer,
			stream_callback=self.get_callback())
		self._stream.start_stream()
		return self

	def stop_recording(self):
		self._stream.stop_stream()
		return self

	def get_callback(self):
		def callback(in_data, frame_count, time_info, status):
			self.wavefile.writeframes(in_data)
			return(in_data, pyaudio.paContinue)
		return callback

	def get_recordingtime(self):
		if (time.time() - self.lasttimecheck) > 1:
			rec_time = time.time() - self.starttime
			minutes = floor(rec_time / 60)
			if minutes > 9:
				minutes = str(minutes)
			else:
				minutes = "0" + str(minutes)
			seconds = int( ((rec_time / 60) - floor(rec_time / 60)) * 60 )
			if seconds > 9:
				seconds = str(seconds)
			else:
				seconds = "0" + str(seconds)
			rec_time_str = minutes + ":" + seconds
			self.lasttimecheck = time.time()
			return(rec_time_str)
		else:
			return(None)

	def close(self):
		self._stream.close()
		self._pa.terminate()
		self.wavefile.close()

	def _prepare_file(self, fname, mode='wb'):
		wavefile = wave.open(fname, mode)
		wavefile.setnchannels(self.channels)
		wavefile.setsampwidth(self._pa.get_sample_size(pyaudio.paInt16))
		wavefile.setframerate(self.rate)
		return wavefile
