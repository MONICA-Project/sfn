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

    def create_reg_message(self, timestamp):
        raise NotImplementedError

    def load_settings(self, location, file_name):
        raise NotImplementedError
