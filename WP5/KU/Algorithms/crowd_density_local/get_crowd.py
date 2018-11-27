# get_crowd.py
"""This is a crowd density estimation module utilising the work of Sindagi2017 'CNN-based Cascaded Multi-task Learning of
High-level Prior and Density Estimation for Crowd Counting
This module is intended for use within the VCA framework within PyVCA interface
"""
import os
import numpy as np
import base64
import cv2
import json
import arrow
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
import WP5.KU.SharedResources.get_top_down_heat_map as heat_map_gen
import WP5.KU.SharedResources.get_incrementer as incrementer
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
        FrameAnalyser.__init__(self, module_id)
        self.type_module = 'crowd_density_local'
        self.module_id = module_id + '_crowd_density_local'
        self.state = 'active'
        self.zone_id = 'N/A'
        # CAMERA INFO
        self.cam_id = ''
        self.previous_frames_timestamp = {}
        self.process_interval = 1

        # ALGORITHM VARIABLES
        self.scale = 0.5
        self.count = 0
        self.model_path = []

        # EVALUATION
        self.save_image_flag = True
        self.iterator = 0
        self.save_on_count = 2000

        self.load_settings(str(Path(__file__).absolute().parents[0]), 'settings')

        self.net = CrowdCounter()
        # TODO: FUTURE WARNING HERE
        nw.load_net(os.path.join(self.model_path), self.net)
        # CUDA WARNING
        if self.net.cuda_available():
            self.net.cuda()
        else:
            print('RUNNING WITHOUT CUDA SUPPORT')
        self.net.eval()

    def process_frame(self, frame, camera_id, mask, image_2_ground_plane_matrix, ground_plane_roi, ground_plane_size,
                      debug=False):
        """ Process a given frame using the crowd density analysis algorithm.
        Keyword arguments:
            frame --        MxNx3 RGB image
            camera_id --    The unique string identifier where the frame is sourced
            roi --          List[x1, y1, x2, y2] integers, defining 2 points used to specify a section of the image
                            which will passed to the algorithm.
        Returns:
            message --      the JSON message produced by create_obs_message
            density_map --  the output of the algorithm in a viewable image
        """
        # CHECK WHETHER THIS IS THE FIRST FRAME OF THIS CAMERA ID
        if camera_id not in self.previous_frames_timestamp:
            self.previous_frames_timestamp[camera_id] = arrow.utcnow()

        time_1 = self.previous_frames_timestamp[camera_id]
        time_2 = arrow.utcnow()
        # DEBUG OPTIONS
        if debug:
            self.process_interval = 0
            self.save_on_count = 0
            self.save_image_flag = True
        if (time_2 - time_1).seconds >= self.process_interval:
            self.previous_frames_timestamp[camera_id] = time_2

            height = frame.shape[0]
            width = frame.shape[1]
            # roi = [int(np.floor(i * self.scale)) for i in roi]

            # DO SOME SCALE TO OPTIMAL MODEL INPUT, MAYBE SPLIT IMAGE IF ITS TOO LARGE?
            x = cv2.resize(frame, (0, 0), fx=self.scale, fy=self.scale)
            x = cv2.cvtColor(x, cv2.COLOR_RGB2GRAY)

            # INFERENCE
            x = x.astype(np.float32, copy=False)
            x = np.expand_dims(x, axis=0)
            x = np.expand_dims(x, axis=0)
            density_map = self.net(x)
            density_map = density_map.data.cpu().numpy()[0][0]

            # EXTRACT THE ROI FROM THE FRAME AND COUNT WITHIN THAT AREA
            # count = np.sum(density_map)
            # count = np.sum(density_map[roi[1]:roi[3], roi[0]:roi[2]])
            mask = cv2.resize(np.array(mask), (density_map.shape[1], density_map.shape[0]))
            density_map[mask < 1] = 0
            count = np.sum(density_map)

            # CONVERT BACK TO ORIGINAL SCALE
            density_map = cv2.resize(density_map, (width, height))

            # CREATE THE MESSAGE
            self.cam_id = camera_id
            timestamp = arrow.utcnow()

            # CONVERT TO TOP DOWN
            top_down_density_map, heat_image = heat_map_gen.generate_heat_map(density_map,
                                                                              image_2_ground_plane_matrix,
                                                                              ground_plane_roi,
                                                                              ground_plane_size,
                                                                              # timestamp=timestamp,
                                                                              # frame=frame,
                                                                              )
            message = self.create_obs_message(count, top_down_density_map, timestamp)
            # message = self.create_obs_message(count, top_down_density_map, timestamp, frame=frame)

            # CONVERT TO IMAGE THAT CAN BE DISPLAYED
            density_map = 255 * density_map / (np.max(density_map) + np.finfo(float).eps)
            if self.save_image_flag:
                if self.iterator >= self.save_on_count:
                    save_name = '{}_{}_{}'.format(arrow.utcnow().to('GMT').timestamp, self.cam_id, self.type_module)
                    cv2.imwrite(os.path.join(os.path.dirname(__file__), save_name + '_frame.jpeg'),
                                cv2.resize(frame, (0, 0), fx=self.scale, fy=self.scale))
                    cv2.imwrite(os.path.join(os.path.dirname(__file__), save_name + '_density.jpeg'),
                                cv2.resize(density_map, (0, 0), fx=self.scale, fy=self.scale))
                    try:
                        output_message = open(os.path.join(os.path.dirname(__file__), save_name + '.txt'), 'w')
                    except IOError:
                        print('IoError')
                    else:
                        output_message.write(message)
                        output_message.close()
                    self.iterator = 0
                else:
                    self.iterator = self.iterator + 1

            return message, density_map
        else:
            return None, None

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
                'density_map': density_map,
                'frame_byte_array': '',
                'image_dims': '',
                'ground_plane_position': '',
                'timestamp_1': str(timestamp),
                'timestamp_2': str(timestamp),
        }
        if frame is not None:
            # RESIZE THE IMAGE AND MAKE IT BLACK AND WHITE
            # frame = cv2.cvtColor(cv2.resize(frame, (0, 0), fx=0.25, fy=0.25), cv2.COLOR_RGB2GRAY)
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
                'timestamp': str(timestamp),
                'zone_id': self.zone_id,
                'state': self.state,
        }
        message = json.dumps(data)
        try:
            reg_file = open(os.path.join(os.path.dirname(__file__), self.module_id + '_reg.txt'), 'w')
        except IOError:
            print('IoError')
        else:
            reg_file.write(message)
            reg_file.close()
            print('{} module reg message saved to: {}'.format(
                self.type_module, os.path.join(os.path.dirname(__file__), self.module_id + '_reg.txt')))
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
                self.model_path = os.path.join(os.path.dirname(__file__), settings['model_path'])
            if 'scale' in settings:
                self.scale = settings['scale']
            if 'process_interval' in settings:
                self.process_interval = settings['process_interval']
            if 'save_on_count' in settings:
                self.save_on_count = settings['save_on_count']
            if 'save_image_flag' in settings:
                self.save_image_flag = settings['save_image_flag']
        print('SETTINGS LOADED FOR MODULE: ' + self.module_id)

    @staticmethod
    def display_density(frame, density):
        density = 255 * density / np.max(density)
        density = np.dstack((density, density, density))
        disp_frame = np.zeros((frame.shape[0], frame.shape[1] * 2, 3))
        disp_frame[:, 0:frame.shape[1], :] = frame
        disp_frame[:, frame.shape[1]:, :] = density
        disp_frame = disp_frame.astype(np.uint8)
        cv2.imshow('Density', disp_frame)
        cv2.waitKey(0)