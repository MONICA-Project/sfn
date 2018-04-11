# get_crowd.py
from os import path
import numpy as np
import base64
import pickle
import torch
from torch.autograd import Variable
import cv2
from frame_analyser import FrameAnalyser
import json
from SSD.data import BaseTransform
from C_CNN.src.crowd_count import CrowdCounter
import C_CNN.src.network as nw
import datetime


class GetCrowd(FrameAnalyser):

    def __init__(self, module_id, settings_location):
        self.module_id = module_id + '_crowd_density_local'
        self.type_module = 'crowd_density_local'
        self.state = True
        FrameAnalyser.__init__(self, module_id)
        # CAMERA INFO
        self.roi = [0, 300, 0, 300]
        self.cam_id = ''
        self.model_path = []
        self.load_settings(settings_location)

        # ALGORITHM VARIABLES
        self.height = self.roi[3] - self.roi[1]
        self.width = self.roi[2] - self.roi[0]
        self.cuda = True
        self.scale = 0.5
        self.count = 0

        self.net = CrowdCounter()
        # TODO: FUTURE WARNING HERE
        nw.load_net(path.join(self.model_path), self.net)
        self.net.cuda()
        self.net.eval()
        # RE-SIZES THE IMAGE AND REMOVES THE DATASET MEAN.
        self.transform = BaseTransform(500, (104 / 256.0, 117 / 256.0, 123 / 256.0))

    def process_frame(self, frame, camera_id):
        # x = torch.from_numpy(self.transform(frame)[0]).permute(2, 0, 1)
        # x = Variable(x.unsqueeze(0)).cuda()
        # EXTRACT THE ROI FROM THE FRAME
        frame = frame[self.roi[1]:self.roi[3], self.roi[0]:self.roi[2], :]

        # DO SOME SCALE TO OPTIMAL MODEL INPUT, MAYBE SPLIT IMAGE IF ITS TOO LARGE?
        x = cv2.resize(frame, (0, 0), fx=self.scale, fy=self.scale)
        x = cv2.cvtColor(x, cv2.COLOR_RGB2GRAY)

        # INFERENCE
        x = x.astype(np.float32, copy=False)
        x = np.expand_dims(x, axis=0)
        x = np.expand_dims(x, axis=0)
        density_map = self.net(x)
        density_map = density_map.data.cpu().numpy()[0][0]

        # GET THE NUMERIC OUTPUT (COUNT)
        count = np.sum(density_map)

        # CONVERT BACK TO ORIGINAL SCALE AND GET THE HEAT MAP
        ratio = 4
        density_map = cv2.resize(density_map, (self.width, self.height)) / ratio

        # CREATE THE MESSAGE
        self.cam_id = camera_id
        message = self.create_obs_message(count, density_map, datetime.datetime.utcnow().isoformat(), frame)

        # CONVERT TO IMAGE THAT CAN BE DISPLAYED
        density_map = 255 * density_map / np.max(density_map)
        detection_text = 'Total Detections : {:.0f}'.format(count)
        cv2.putText(density_map, detection_text, (10, 20), self.FONT, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        return message, density_map

    def create_obs_message(self, count, heat_map, timestamp, frame):
        # RESIZE THE IMAGE AND MAKE IT BLACK AND WHITE
        frame = cv2.cvtColor(cv2.resize(frame, (0, 0), fx=0.25, fy=0.25), cv2.COLOR_RGB2GRAY)
        data = {
                'module_id': self.module_id,
                'type_module': self.type_module,
                'camera_ids': [self.cam_id],
                'density_count': int(count),
                'density_map': heat_map.tolist(),
                # ENCODE THE IMAGE INTO A STRING ARRAY
                'frame_byte_array': base64.b64encode(frame.copy(order='C')).decode('utf-8'),
                'image_dims': frame.shape,
                'timestamp_1': timestamp,
                'timestamp_2': timestamp,
        }
        message = json.dumps(data)
        # CODE TO REBUILD AND SHOW THE IMAGE FORM THE JSON MESSAGE
        # rebuilt_data = json.loads(message)
        # d = base64.b64decode(rebuilt_data['frame_byte_array'])
        # rebuilt_frame = np.frombuffer(d, dtype=np.uint8)
        # rebuilt_frame = np.reshape(rebuilt_frame, (rebuilt_data['image_dims'][0], rebuilt_data['image_dims'][1]))
        # cv2.imshow('c', rebuilt_frame); cv2.waitKey(0)
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

    # TODO REMOVE THE LOADING OF roi AS THIS IS NOT MODULE SPECIFIC
    def load_settings(self, settings_location):
        fo = open((settings_location + '.pk'), 'rb')
        entry = pickle.load(fo, encoding='latin1')

        self.roi = entry['roi']
        self.model_path = './C_CNN/final_models/cmtl_shtechA_204.h5'
        print('SETTINGS LOADED FOR MODULE: ' + self.module_id)
