# get_crowd.py
"""This is a crowd density estimation module utilising the work of Sindagi2017 'CNN-based Cascaded Multi-task Learning of
High-level Prior and Density Estimation for Crowd Counting
This module is intended for use within the VCA framework within PyVCA interface
"""
from os import path
import numpy as np
import base64
import cv2
import json
import datetime
from WP5.KU.definitions import KU_DIR
from WP5.KU.Algorithms.frame_analyser import FrameAnalyser
from WP5.KU.Algorithms.crowd_density_local.C_CNN.src.crowd_count import CrowdCounter
import WP5.KU.Algorithms.crowd_density_local.C_CNN.src.network as nw

__version__ = '0.1'
__author__ = 'Rob Dupre (KU)'


class GetCrowd(FrameAnalyser):
    def __init__(self, module_id):
        """ Initialise the GetCrowd object.
        Keyword arguments:
            module_id -- A unique string identifier
        """
        self.type_module = 'crowd_density_local'
        self.module_id = module_id
        self.state = 'active'
        self.zone_id = 'N/A'
        FrameAnalyser.__init__(self, module_id)
        # CAMERA INFO
        self.cam_id = ''

        # ALGORITHM VARIABLES
        self.scale = 0.5
        self.count = 0
        self.model_path = []
        self.load_settings()

        self.net = CrowdCounter()
        # TODO: FUTURE WARNING HERE
        nw.load_net(path.join(self.model_path), self.net)
        # CUDA WARNING
        if self.net.cuda_available():
            self.net.cuda()
        else:
            print('RUNNING WITHOUT CUDA SUPPORT')
        self.net.eval()

    def process_frame(self, frame, camera_id, roi):
        """ Process a given frame using the crowd density analysis algorithm.
        Keyword arguments:
            frame --        MxNx3 RGB image
            camera_id --    The unique string identifier where the frame is sourced
            roi --          List[x1, y1, x2, y2] integers, defining 2 points used to speficiy a section of the image
                            which will passed to the algorithm.
        Returns:
            message --      the JSON message produced by create_obs_message
            density_map --  the output of the algorithm in a viewable image
        """
        # EXTRACT THE ROI FROM THE FRAME
        frame = frame[roi[1]:roi[3], roi[0]:roi[2], :]

        height = roi[3] - roi[1]
        width = roi[2] - roi[0]

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
        density_map = cv2.resize(density_map, (width, height)) / ratio

        # CREATE THE MESSAGE
        self.cam_id = camera_id
        # message = self.create_obs_message(count, density_map, datetime.datetime.utcnow().isoformat(), frame=None)
        message = self.create_obs_message(count, density_map, datetime.datetime.utcnow().isoformat(), frame=frame)

        # CONVERT TO IMAGE THAT CAN BE DISPLAYED
        density_map = 255 * density_map / np.max(density_map)

        return message, density_map

    def create_obs_message(self, count, density_map, timestamp, frame=None):
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
                'density_count': int(count),
                'density_map': density_map.tolist(),
                'frame_byte_array': '',
                'image_dims': '',
                'ground_plane_position': '',
                'timestamp_1': timestamp,
                'timestamp_2': timestamp,
        }
        if frame is not None:
            # RESIZE THE IMAGE AND MAKE IT BLACK AND WHITE
            frame = cv2.cvtColor(cv2.resize(frame, (0, 0), fx=0.25, fy=0.25), cv2.COLOR_RGB2GRAY)
            data['frame_byte_array'] = base64.b64encode(frame.copy(order='C')).decode('utf-8')
            data['image_dims'] = frame.shape

        message = json.dumps(data)
        # CODE TO REBUILD AND SHOW THE IMAGE FORM THE JSON MESSAGE
        # rebuilt_data = json.loads(message)
        # d = base64.b64decode(rebuilt_data['frame_byte_array'])
        # rebuilt_frame = np.frombuffer(d, dtype=np.uint8)
        # rebuilt_frame = np.reshape(rebuilt_frame, (rebuilt_data['image_dims'][0], rebuilt_data['image_dims'][1]))
        # cv2.imshow('c', rebuilt_frame); cv2.waitKey(0)
        return message

    def create_reg_message(self, timestamp):
        """ Function to create the JSON payload for the registration message of this module. Follows the content as
        defined on the WP5 Confluence (6. JSON Message Format):
            timestamp --    the time the module is initialised
        Returns:
            message --      the JSON message payload
        """
        data = {
                'module_id': self.module_id,
                'type_module': self.type_module,
                'timestamp': timestamp,
                'zone_id': self.zone_id,
                'state': self.state,
        }
        message = json.dumps(data)
        return message

    # TODO: ADD MODULE SETTINGS FILE
    def load_settings(self):
        self.model_path = path.join(KU_DIR, 'Algorithms/crowd_density_local/C_CNN/final_models/cmtl_shtechA_204.h5')
        print('SETTINGS LOADED FOR MODULE: ' + self.module_id)
