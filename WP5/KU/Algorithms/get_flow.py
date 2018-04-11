# get_flow.py
import numpy as np
import pickle
from frame_analyser import FrameAnalyser
import json


class GetFlow(FrameAnalyser):

    def __init__(self, module_id, settings_location):
        self.module_id = module_id + '_flow'
        self.type_module = 'flow'
        self.state = True
        FrameAnalyser.__init__(self, module_id)
        # CAMERA INFO
        self.roi = [0, 300, 0, 300]
        self.cam_id = ''
        self.weights_path = []
        self.load_settings(settings_location)

        # ALGORITHM VARIABLES
        self.cuda = False

    def process_frame(self, frame, camera_id):
        # USES ONLY THE REGION OF INTEREST DEFINED IN TEH SETTINGS
        frame = frame[self.roi[1]:self.roi[3], self.roi[0]:self.roi[2], :]
        # CONVERT FRAME TO WHATEVER FORMAT IS REQUIRED

        # ADD INFERENCE CODE FOR THE FRAME HERE

        # CREATE THE MESSAGE AND RETURN
        self.cam_id = camera_id
        message = self.create_message()
        return message, frame

    def create_obs_message(self):
        # ADD VARIABLES TO BE DUMPED INTO JSON
        data = {'count': int(0), 'heat_map': np.zeros([5, 5])}
        message = json.dumps(data)
        return message

    def create_reg_message(self, timestamp):
        data = {
                'module_id': self.module_id,
                'type_module': self.type_module,
                'timestamp': timestamp,
                'state': self.state,
        }
        message = json.dumps(data)
        # message = json.loads(message)
        return message

    def load_settings(self, settings_location):
        fo = open((settings_location + str(self.cam_id) + '.pk'), 'rb')
        entry = pickle.load(fo, encoding='latin1')

        self.roi = entry['roi']
        self.weights_path = './C_CNN/final_models/cmtl_shtechA_204.h5'
        self.cuda = True
        print('SETTINGS LOADED FOR CAMERA: ' + self.module_id)
