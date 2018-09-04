# get_flow.py
import json
import cv2
import math
import arrow
import numpy as np
import torch
from torch.autograd import Variable
from pathlib import Path
import sys
import os
sys.path.append(str(Path(__file__).absolute().parents[4]))
import WP5.KU.SharedResources.get_incrementer as incrementer
from WP5.KU.Algorithms.frame_analyser import FrameAnalyser
from WP5.KU.Algorithms.flow_analysis.FlowNet2_src import flow_to_image
from WP5.KU.Algorithms.flow_analysis.FlowNet2_src import FlowNet2

__version__ = '0.1'
__author__ = 'Hajar Sadeghi (KU)'


class GetFlow(FrameAnalyser):
    def __init__(self, module_id):  # def __init__(self, module_id, settings_location):
        """ Initialise the GetFlow object.
            Keyword arguments:
                module_id -- A unique string identifier
                settings_location -- Module settings: location
        """
        FrameAnalyser.__init__(self, module_id)
        self.module_id = module_id + '_flow'
        self.type_module = 'flow'
        self.state = True
        self.previous_frames_dictionary = {}  # a dictionary of (camera_id,frame) pair
        self.previous_frames_timestamp = {}
        self.process_interval = 1
        # CAMERA INFO
        self.roi = [0, 300, 0, 300]
        self.cam_id = ''
        self.weights_path = []

        # ALGORITHM VARIABLES
        self.scale = 0.5
        self.model = None
        self.cuda = False
        self.load_settings(str(Path(__file__).absolute().parents[0]), 'settings')
        self.scale_height = 384  # TO SCALE THE INPUT IMAGE IF IT IS TOO LARGE FOR FLOWNET
        self.scale_width = 512
        self.save_image = np.zeros((self.scale_width, self.scale_height * 2, 3), dtype=np.uint8)

        # EVALUATION
        self.counter = 0
        self.iterator = 0
        self.save_on_count = 2000

    def process_frame(self, frame, camera_id, rois, debug=False):  # rois: region of interests
        # CHECK WHETHER THIS IS THE FIRST FRAME OF THIS CAMERA ID
        if camera_id not in self.previous_frames_dictionary:
            self.previous_frames_dictionary[camera_id] = cv2.resize(frame, (self.scale_height, self.scale_width))
            self.previous_frames_timestamp[camera_id] = arrow.utcnow()
            message = self.create_obs_message([], [], arrow.utcnow())
            return message, None
        # DEBUG OPTIONS
        if debug:
            self.process_interval = 0
            self.save_on_count = 0

        # USES ONLY THE REGION OF INTEREST DEFINED IN THE SETTINGS
        time_1 = self.previous_frames_timestamp[camera_id]
        time_2 = arrow.utcnow()
        if (time_2 - time_1).seconds >= self.process_interval:
            frame2 = cv2.resize(frame, (self.scale_height, self.scale_width))

            height, width = frame.shape[:2]

            ims = np.array([[self.previous_frames_dictionary[camera_id], frame2]]).transpose((0, 4, 1, 2, 3)).astype(np.float32)
            ims = torch.from_numpy(ims)
            ims_v = Variable(ims.cuda(), requires_grad=False)

            flownet_2 = self.model
            flow_uv = flownet_2(ims_v).cpu().data
            flow_uv = flow_uv[0].numpy().transpose((1, 2, 0))

            # CONVERT BACK TO ORIGINAL SCALE
            flow_uv = cv2.resize(flow_uv, (width, height))

            ave_flow_mag = []
            ave_flow_dir = []
            for i in range(len(rois)):
                roi_current = rois[i]
                flow_uv_current = flow_uv[roi_current[1]:roi_current[3], roi_current[0]:roi_current[2], :]

                mean_u = flow_uv_current[:, :, 0].mean()
                mean_v = flow_uv_current[:, :, 1].mean()

                mag = math.sqrt(math.pow(mean_u, 2) + math.pow(mean_v, 2))

                if mean_v < 0:
                    uv_angle = 360 + math.degrees(math.atan2(mean_v, mean_u))
                else:
                    uv_angle = math.degrees(math.atan2(mean_v, mean_u))
                direction = uv_angle / 360

                ave_flow_mag.append(mag)
                ave_flow_dir.append(direction)

            # CREATE THE MESSAGE
            self.cam_id = camera_id
            message = self.create_obs_message(ave_flow_mag, ave_flow_dir, arrow.utcnow())

            flow_image = None
            if self.iterator >= self.save_on_count:
                # VISUALIZE THE OPTICAL FLOW AND SAVE IT
                flow_image = flow_to_image(flow_uv)
                save_name = incrementer.get_incrementer(self.counter, 7) + '_' + self.cam_id

                self.save_image[:, 0:self.scale_height, :] = self.previous_frames_dictionary[camera_id]
                self.save_image[:, self.scale_height:(self.scale_height * 2), :] = frame2
                cv2.imwrite(os.path.join(os.path.dirname(__file__), save_name + '_frame2.jpeg'), self.save_image)
                cv2.imwrite(os.path.join(os.path.dirname(__file__), save_name + '_flow.jpeg'), flow_image)
                try:
                    reg_file = open(os.path.join(os.path.dirname(__file__), save_name + '.txt'), 'w')
                except IOError:
                    print('IoError')
                else:
                    reg_file.write(message)
                    reg_file.close()
                self.iterator = 0
                self.counter = self.counter + 1
            else:
                self.iterator = self.iterator + 1

            self.previous_frames_dictionary[camera_id] = frame2
            self.previous_frames_timestamp[camera_id] = time_2
            return message, flow_image
        else:
            return None, None

    def create_obs_message(self, average_flow_mag, average_flow_dir, timestamp):
        """ Function to create the JSON payload containing the observation. Follows the content as defined on the WP5
        Confluence (6. JSON Message Format):
            count --        Double defining the total number of people in the frame's roi
            density_map --  The output of the algorithm
            timestamp --    the time the frame is processed
            frame --        [OPTIONAL] the input frame given to the algorithms process after the roi is applied
        Returns:
            message --      the JSON message payload
        """
        data = {
            'module_id': self.module_id,
            'type_module': self.type_module,
            'camera_ids': [self.cam_id],
            'average_flow_magnitude': average_flow_mag,
            'average_flow_direction': average_flow_dir,
            'flow_frame_byte_array': '',
            'timestamp': str(timestamp),
        }

        message = json.dumps(data)
        return message

    def create_reg_message(self, timestamp):
        data = {
                'module_id': self.module_id,
                'type_module': self.type_module,
                'timestamp': str(timestamp),
                'state': self.state,
        }
        message = json.dumps(data)
        try:
            reg_file = open(os.path.join(os.path.dirname(__file__), self.module_id + '_reg.txt'), 'w')
        except IOError:
            print('IoError')
        else:
            reg_file.write(message)
            print('{} module reg message saved to: {}'.format(
                self.module_type, os.path.join(os.path.dirname(__file__), self.module_id + '_reg.txt')))
            reg_file.close()
        return message

    def load_settings(self, location, file_name):
        try:
            json_file = open(location + '/' + file_name + '.txt')
        except IOError:
            print('IoError')
        else:
            line = json_file.readline()
            settings = json.loads(line)
            json_file.close()

            if 'model_path' in settings:
                path = os.path.join(os.path.dirname(__file__), settings['model_path'])
            if 'process_interval' in settings:
                self.process_interval = settings['process_interval']
            # Build model
            flownet2 = FlowNet2()
            pretrained_dict = torch.load(path)['state_dict']
            model_dict = flownet2.state_dict()
            pretrained_dict = {k: v for k, v in pretrained_dict.items() if k in model_dict}
            model_dict.update(pretrained_dict)
            flownet2.load_state_dict(model_dict)

            # CUDA WARNING
            if flownet2.cuda_available():
                flownet2.cuda()
            else:
                print('RUNNING WITHOUT CUDA SUPPORT')
            self.model = flownet2
