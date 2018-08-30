# frame_analyser.py
"""Super class that forms the foundation for the python modules to be created and utilised within the VCA framework
and the PyVCA interface
"""
import cv2

__version__ = '0.1'
__author__ = 'Rob Dupre (KU)'


class FrameAnalyser:

    def __init__(self, module_id):
        # VARIABLES REQUIRED FOR THE FINAL MESSAGE CREATION
        self.module_id = module_id
        self.type_module = ''
        self.state = 'inactive'
        self.previous_frames_timestamp = {}

        # CONSTANTS
        self.FONT = cv2.FONT_HERSHEY_SIMPLEX
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.WHITE = (255, 255, 255)

    def process_frame(self, frame, camera_id):
        raise NotImplementedError

    def create_obs_message(self):
        raise NotImplementedError

    def create_reg_message(self):
        raise NotImplementedError

    def load_settings(self):
        raise NotImplementedError
