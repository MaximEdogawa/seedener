# import the necessary packages
from picamera2.encoders import H264Encoder
from picamera2 import Picamera2 
from picamera2.outputs import FileOutput
from threading import Thread
import time
import io

class PiVideoStream:
	def __init__(self, resolution=(320, 240), framerate=32, format="bgr", **kwargs):
		# initialize the camera
		self.camera = Picamera2()
		video_config = self.camera.create_video_configuration(lores={"size": (320, 240)}, display="lores")
		self.camera.configure(video_config)
		encoder = H264Encoder(bitrate=10000000)
		self.buffer = io.BytesIO(b"\x00\x01")
		output = FileOutput(self.buffer)
		self.camera.start_recording(encoder,output)
		# initialize the frame and the variable used to indicate
		# if the thread should be stopped
		self.frame = None
		self.should_stop = False
		self.is_stopped = True

	def start(self):
		# start the thread to read frames from the video stream
		t = Thread(target=self.update, args=())
		t.daemon = True
		t.start()
		self.is_stopped = False
		return self

	def update(self):
		# keep looping infinitely until the thread is stopped
		for f in self.buffer.getvalue():
			# grab the frame from the stream and clear the stream in
			# preparation for the next frame
			self.frame = f
			self.buffer.truncate(0)

			# if the thread indicator variable is set, stop the thread
			# and resource camera resources
			if self.should_stop:
				print("PiVideoStream: closing everything")
				self.camera.stop_recording()
				self.camera.close()
				self.should_stop = False
				self.is_stopped = True
				return

	def read(self):
		# return the frame most recently read
		return self.frame

	def stop(self):
		# indicate that the thread should be stopped
		self.should_stop = True

		# Block in this thread until stopped
		while not self.is_stopped:
			pass
