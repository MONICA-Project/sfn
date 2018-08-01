# frame_streamer.py
""" Loads a Image sequence and returns each frame sequentially when called. Provides options for looping the stream or
repeating the last frame"""
import cv2
import os

__version__ = '0.2'
__author__ = 'Rob Dupre (KU)'


class ImageSequenceStreamer:
    def __init__(self, seq_path, start_frame=0, frame_size=[1080, 768], loop_last=True, repeat=False):
        """ Initialisation.
        Keyword arguments:
            seq_path --     String identifying the folder location of the images.
            start_frame --  [OPTIONAL] Allows for the image sequence to start at a specific point
            frame_size --   [OPTIONAL] Allows for loaded frames to be resized
            loop_last --    [OPTIONAL] if True last frame is repeated until stop is called
            repeat --       [OPTIONAL] if True repeats all frames until stop is called
        Returns:
            message --      the JSON message produced by create_obs_message
            density_map --  the output of the algorithm in a viewable image
        """
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

        # GET LIST OF IMAGES AT FILE LOCATION
        valid_images = ('.jpg', '.png', '.tga', '.tif', '.jpeg')
        for f in sorted(os.listdir(self.folder_location)):
            ext = os.path.splitext(f)[1]
            if ext.lower().endswith(valid_images):
                self.file_list.append(os.path.join(self.folder_location, f))

        # IF WORKING THE STREAMER WILL ALLOW THE RETURN OF THE NEXT IMAGE. IF NOT THE STREAM IS CONSIDERED stopped
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
            if not self.loop_last and not self.repeat:
                self.working = False
        # NOW IN INFINITE LOOP AS current_image WILL ONLY EVER HOLD THE LAST IMAGE.

        return self.current_image

    def save(self, filename):
        print('Screen shot Saved')
        cv2.imwrite(filename + '.png', self.current_image)
