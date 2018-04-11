# frame_streamer.py
import cv2
import os
import numpy as np


class ImageSequenceStreamer:
    def __init__(self, seq_path, start_frame=0, frame_size=[1080, 768], loop_last=True, repeat=False):
        self.folder_location = seq_path
        self.file_list = []
        self.size = (frame_size[0], frame_size[1])
        self.images = []
        self.start_frame = start_frame
        self.image_count = self.start_frame
        self.current_image = []
        self.working = False
        self.loop_last = loop_last
        self.repeat = repeat
        # [Location, Start Frame]
        # 1: [(dataset_folder + 'UCSD_Anomaly/UCSDped1/Train/Train001/'), 0],
        # GET LIST OF JPEG's AT FILE LOCATION
        valid_images = ('.jpg', '.png', '.tga', '.tif', '.jpeg')
        for f in sorted(os.listdir(self.folder_location)):
            ext = os.path.splitext(f)[1]
            if ext.lower().endswith(valid_images):
                self.file_list.append(os.path.join(self.folder_location, f))
                # self.images.append(cv2.resize(cv2.imread(os.path.join(self.folder_location, f)), self.size))

        if len(self.file_list) > 0:
            self.working = True
            print('IMAGE SEQUENCE FOUND AND LOADED.')
        else:
            self.working = False
            print('NO IMAGES FOUND.')

    def open(self):
        return self.working

    def stop(self):
        self.working = False

    def read(self):
        # LOAD THE NEXT IMAGE AS LONG AS THERE ARE STILL ENTRIES IN THE file_list,
        if self.image_count < len(self.file_list) - 1:
            self.current_image = cv2.resize(cv2.imread(self.file_list[self.image_count]), self.size)
            # self.current_image = self.images[self.image_count]
            self.image_count = self.image_count + 1
        # THIS IS NOW THE LAST IMAGE IN THE LIST
        elif self.image_count == len(self.file_list) - 1:
            self.current_image = cv2.resize(cv2.imread(self.file_list[self.image_count]), self.size)
            if self.repeat:
                self.image_count = self.start_frame
            else:
                self.image_count = self.image_count + 1
            # ELSE: IF NOT loop_last RETURN BLANK FRAME AND STOP OR LEAVE self.current_image AS THE LAST IMAGE LOADED
            if not self.loop_last:
                self.working = False
        # NOW IN INFINITE LOOP AS current_image WILL ONLY EVER HOLD THE LAST IMAGE.

        return self.current_image
