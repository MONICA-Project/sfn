# get_objects.py
from os import path
import numpy as np
import pickle
import torch
from torch.autograd import Variable
import cv2
from WP5.KU.Algorithms.frame_analyser import FrameAnalyser
from WP5.KU.Algorithms.object_detection.SSD.data import BaseTransform, VOC_CLASSES as LABEL_MAP
from WP5.KU.Algorithms.object_detection.SSD.ssd import build_ssd
import json


class GetObjects(FrameAnalyser):

    def __init__(self, module_id):
        FrameAnalyser.__init__(self, module_id)
        self.module_id = module_id + '_object_detection'
        self.type_module = 'object_detection'
        self.state = True

        # CAMERA INFO
        self.cam_id = ''
        self.weights_path = []
        self.load_settings()

        # ALGORITHM VARIABLES
        self.cuda = False
        self.scale = 1
        self.count = 0
        self.confidence_threshold = 0.6

        # INITIALISE SSD
        self.net = build_ssd('test', 300, 21)
        self.net.load_state_dict(torch.load(path.dirname(path.abspath(__file__)) + self.weights_path))
        self.net.cuda()
        self.net.eval()
        self.transform = BaseTransform(self.net.size, (104 / 256.0, 117 / 256.0, 123 / 256.0))

    def process_frame(self, frame, camera_id):
        # EXTRACT THE ROI FROM THE FRAME
        self.cam_id = camera_id
        height, width = frame.shape[:2]
        x = torch.from_numpy(self.transform(frame)[0]).permute(2, 0, 1)
        x = Variable(x.unsqueeze(0)).cuda()
        # PASS FORWARD
        y = self.net(x)
        # scale each detection back up to the image
        scale = torch.Tensor([width, height, width, height])
        data = y.data
        detections = []
        for i in range(data.size(1)):
            j = 0
            while data[0, i, j, 0] >= self.confidence_threshold:
                pt = (data[0, i, j, 1:] * scale).cpu().numpy()
                t = [int(pt[0] + ((pt[2] - pt[0]) / 2)), int(pt[3])]
                # cv2.rectangle(frame, (int(pt[0]), int(pt[1])), (int(pt[2]), int(pt[3])), self.BLUE, 2)
                # cv2.circle(frame, (t[0], t[1]), 10, (255, 0, 0), -1)
                cv2.putText(frame, LABEL_MAP[i - 1], (int(pt[0]), int(pt[1])), self.FONT, 2, (255, 255, 255), 2,
                            cv2.LINE_AA)
                detections.append(t)
                j += 1

        detection_text = 'Total Detections : ' + str(len(detections))
        cv2.putText(frame, detection_text, (10, 20), self.FONT, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        message = self.create_obs_message(len(detections), detections)
        return message, frame

    def create_obs_message(self, count, detections):
        data = {'count': int(count), 'density_map': detections}
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

    def load_settings(self):
        self.weights_path = '/SSD/weights/ssd_300_VOC0712.pth'
        print('SETTINGS LOADED FOR MODULE: ' + self.module_id)
