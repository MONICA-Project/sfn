# get_people.py
from os import path
import numpy as np
import pickle
import torch
from torch.autograd import Variable
import cv2
from frame_analyser import FrameAnalyser
from SSD.data import BaseTransform, VOC_CLASSES as LABEL_MAP
from SSD.ssd import build_ssd
import json


class GetPeople(FrameAnalyser):

    def __init__(self, camera_name, settings_location):
        self.cam_id = camera_name
        FrameAnalyser.__init__(self, self.cam_id)
        # CAMERA INFO
        self.camera_position = [0, 0]
        self.roi = [0, 300, 0, 300]
        self.refPt = [[50, 50], [300, 50], [50, 300], [300, 300], [100, 100]]
        self.ground_plane_position = [0, 0]
        self.heat_map_transform = 0
        self.ground_plane_orientation = 0
        self.ground_plane_roi = [0, 300, 0, 300]
        self.ground_plane_size = [0, 0]
        self.weights_path = []
        self.load_settings(settings_location)

        # ALGORITHM VARIABLES
        self.height = self.roi[3] - self.roi[1]
        self.width = self.roi[2] - self.roi[0]
        self.cuda = False
        self.scale = 1
        self.count = 0
        self.confidence_threshold = 0.6
        self.heat_map = np.zeros([self.ground_plane_size[0], self.ground_plane_size[1]])

        # INITIALISE SSD
        self.net = build_ssd('test', 300, 21)
        self.net.load_state_dict(torch.load(path.dirname(path.abspath(__file__)) + self.weights_path))
        self.net.cuda()
        self.net.eval()
        self.transform = BaseTransform(self.net.size, (104 / 256.0, 117 / 256.0, 123 / 256.0))

    def process_frame(self, frame):
        # EXTRACT THE ROI FROM THE FRAME
        frame = frame[self.roi[1]:self.roi[3], self.roi[0]:self.roi[2], :]
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
        if len(detections) > 0:
            self.heat_map, _ = self.generate_heat_map(detections, self.heat_map_transform, self.ground_plane_roi,
                                                      self.ground_plane_size)
                                                      # self.ground_plane_size, frame=frame)
        message = self.create_message(len(detections), self.heat_map)
        return message, frame

    def create_message(self, count, heat_map):
        data = {'count': int(count), 'heat_map': heat_map.tolist()}
        message = json.dumps(data)
        return message

    def load_settings(self, settings_location):
        fo = open((settings_location + str(self.cam_id) + '.pk'), 'rb')
        entry = pickle.load(fo, encoding='latin1')

        if entry['camera_id'] == self.cam_id:
            self.camera_position = entry['camera_position']
            self.ground_plane_orientation = entry['ground_plane_orientation']
            self.roi = entry['roi']
            self.ground_plane_position = entry['ground_plane_gps']
            self.heat_map_transform = entry['heat_map_transform']
            self.ground_plane_roi = entry['ground_plane_roi']
            self.ground_plane_size = entry['ground_plane_size']
            self.weights_path = '/SSD/weights/ssd_300_VOC0712.pth'
            print('SETTINGS LOADED FOR CAMERA: ' + self.cam_id)
        else:
            print('WRONG CAMERA ID: CONFIG FILE INCORRECT')
