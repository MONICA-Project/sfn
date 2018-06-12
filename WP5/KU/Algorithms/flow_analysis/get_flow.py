# get_flow.py
import pickle
from WP5.KU.Algorithms.frame_analyser import FrameAnalyser
from WP5.KU.Algorithms.flow_analysis.FlowNet2_src.flow_2img import flow_2img
import json
import cv2
import math
import arrow
from WP5.KU.Algorithms.flow_analysis.FlowNet2_src import flow_to_image

__version__ = '0.1'
__author__ = 'Hajar Sadeghi (KU)'


class GetFlow(FrameAnalyser):
    def __init__(self, module_id):  # def __init__(self, module_id, settings_location):
        """ Initialise the GetFlow object.
            Keyword arguments:
                module_id -- A unique string identifier
                settings_location -- Module settings: location
        """
        self.module_id = module_id + '_flow'
        self.type_module = 'flow'
        self.state = True
        self.previous_frames_dictionary = {}  # a dictionary of (camera_id,frame) pair
        FrameAnalyser.__init__(self, module_id)
        # CAMERA INFO
        self.roi = [0, 300, 0, 300]
        self.cam_id = ''
        self.weights_path = []
        # self.load_settings(settings_location)

        # ALGORITHM VARIABLES
        self.cuda = False
        self.scale_height = 384  # TO SCALE THE INPUT IMAGE IF IT IS TOO LARGE FOR FLOWNET
        self.scale_width = 512

    def process_frame(self, frame, camera_id, roi, rois):  # rois: region of interests
        # CHECK WHETHER THIS IS THE FIRST FRAME OF THIS CAMERA ID
        if camera_id not in self.previous_frames_dictionary:
            self.previous_frames_dictionary[camera_id] = frame
            message = self.create_obs_message([], [], arrow.utcnow())
            return message, []

        # USES ONLY THE REGION OF INTEREST DEFINED IN THE SETTINGS
        frame1 = self.previous_frames_dictionary[camera_id]
        frame2 = frame
        self.previous_frames_dictionary[camera_id] = frame2

        frame1 = frame1[roi[1]:roi[3], roi[0]:roi[2], :]
        frame2 = frame2[roi[1]:roi[3], roi[0]:roi[2], :]

        height, width = frame1.shape[:2]

        # DO SOME SCALE TO OPTIMAL MODEL INPUT, MAYBE SPLIT IMAGE IF ITS TOO LARGE?
        fr1 = cv2.resize(frame1, (self.scale_height, self.scale_width))
        # cv2.resize(frame1, (0, 0), fx=self.scale, fy=self.scale)
        fr2 = cv2.resize(frame2, (self.scale_height, self.scale_width))
        # cv2.resize(frame2, (0, 0), fx=self.scale, fy=self.scale)

        flow_uv = flow_2img(fr1, fr2)

        # CONVERT BACK TO ORIGINAL SCALE
        flow_uv = cv2.resize(flow_uv, (width, height))

        # VISUALIZE THE OPTICAL FLOW AND SAVE IT
        # flow_image = None
        flow_image = flow_to_image(flow_uv)

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

        return message, flow_image

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
        return message

    def load_settings(self, settings_location):
        fo = open((settings_location + str(self.cam_id) + '.pk'), 'rb')
        entry = pickle.load(fo, encoding='latin1')

        self.roi = entry['roi']
        self.weights_path = './C_CNN/final_models/cmtl_shtechA_204.h5'
        self.cuda = True
        print('SETTINGS LOADED FOR CAMERA: ' + self.module_id)
