# cam_video_streamer.py
"""Implementation of a RTSP stream reader utilising OpenCV"""
import cv2
import numpy as np
from threading import Thread
import time

__version__ = '0.1'
__author__ = 'Rob Dupre (KU)'


class CamVideoStreamer:
    def __init__(self, cam_path, identifier=1):
        self.stream = cv2.VideoCapture(cam_path)
        self.id = identifier

        if self.open():
            print('CAMERA ' + str(self.id) + ' CONNECTION ESTABLISHED.')
        else:
            print('FAILED TO CONNECT TO CAMERA ' + str(self.id) + '.')

        self.stopped = False
        self.current_frame = np.zeros([800, 200, 3])
        self.grabbed = False

    def open(self):
        return self.stream.isOpened()

    def start(self):
        t = Thread(target=self.update, args=())
        t.daemon = True
        self.stopped = False
        t.start()
        # ADD DELAY TO ALLOW STREAMER TO BUFFER SOME INITIAL FRAMES
        time.sleep(0.5)
        return self

    def update(self):
        while True:
            if self.stopped:
                return

            self.grabbed, self.current_frame = self.stream.read()
            if not self.grabbed:
                self.stop()
                return

    def read(self):
        return self.current_frame

    def stop(self):
        self.stopped = True

# cap1 = CamVideoStreamer('rtsp://184.72.239.149/vod/mp4:BigBuckBunny_175k.mov')
# cap1.start()
# while True:
#     # frame1 = cap1.read()
#     frame1 = cap1.read_last()
#     # frame1 = cap1.current_frame
#     cv2.imshow('Video', frame1)
#     if cv2.waitKey(1) == ord('c'):
#         exit(0)
