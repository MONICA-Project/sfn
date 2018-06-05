# security_fusion_node.py
"""The class that handles the storage of current messages on the sfn_service and contains the functions to process those
messages"""
import numpy as np
import cv2
import json
import time
import sqlite3
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
from WP5.KU.SharedResources.convert_to_meter import convert_to_meter
from WP5.KU.SharedResources.rotate_image import rotate_image
# from ...SharedResources.convert_to_meter import convert_to_meter
# from ...SharedResources.rotate_image import rotate_image

__version__ = '0.1'
__author__ = 'RoViT (KU)'


class SecurityFusionNode:

    def __init__(self, module_id):
        self.module_id = module_id + '_crowd_density_global'
        self.module_type = 'crowd_density_global'
        self.last_amalgamation = time.time()
        self.timer = 0
        self.state = 'active'

        # Create a data structure
        self.conn = sqlite3.connect('sfn_database.db')
        self.c = self.conn.cursor()

        # Create table
        self.c.execute(
            '''Create TABLE IF NOT EXISTS messages(cam_id TEXT, module_id TEXT, msg TEXT)''')
        self.conn.commit()
        self.c.execute(
            '''Create TABLE IF NOT EXISTS configs(conf_id TEXT, msg TEXT)''')
        self.conn.commit()
        self.c.execute(
            '''Create TABLE IF NOT EXISTS logs(job_id TEXT, time TEXT, log TEXT)''')
        self.conn.commit()
        self.c.close()
        self.conn.close()

    def insert_db(self, c_id, m_id, msg):
        """Insert for recent camera messages"""

        # MESSAGE SORTING CODE: FIND THE CAMERA ID AND MODULE AND UPDATE recent_cam_messages
        log_text = ''
        # row: the index of previous message for this camera and module
        row = self.query_db(c_id, m_id)

        # IF AN ENTRY IS FOUND:
        if len(row) != 0:
            log_text = log_text + 'PREVIOUS MESSAGE FROM {}, FROM {}, ALREADY STORED, REPLACING. '.format(m_id, c_id)
            self.delete_db(c_id, m_id)  # Delete the previous message from the database
        else:
            # THIS IS THE FIRST INSTANCE OF THIS camera_id AND wp_module PAIR
            log_text = log_text + 'THIS IS A NEW MESSAGE FROM {}, ({}). '.format(m_id, c_id)

        self.conn = sqlite3.connect('sfn_database.db')
        self.c = self.conn.cursor()
        self.c.execute('''INSERT INTO messages(cam_id, module_id, msg) VALUES(?,?,?)''', (c_id, m_id, msg))
        self.conn.commit()
        self.c.close()
        self.conn.close()
        return log_text

    def insert_config_db(self, c_id, msg):
        """Insert for configs"""
        # MESSAGE SORTING CODE: FIND THE CAMERA ID AND MODULE AND UPDATE recent_cam_messages
        log_text = ''
        # row: the index of previous message for this camera and module
        row = self.query_config_db(c_id)

        # IF AN ENTRY IS FOUND:
        if len(row) != 0:
            log_text = log_text + 'PREVIOUS CONFIG FOUND ({}), REPLACING. '.format(c_id)
            self.delete_db(c_id)  # Delete the previous message from the database
        else:
            # THIS IS THE FIRST INSTANCE OF THIS camera_id AND wp_module PAIR
            log_text = log_text + 'THIS IS A NEW CONFIG ({}). '.format(c_id)
        self.conn = sqlite3.connect('sfn_database.db')
        self.c = self.conn.cursor()
        self.c.execute('''INSERT INTO configs(conf_id, msg) VALUES(?,?)''', (c_id, msg))
        self.conn.commit()
        self.c.close()
        self.conn.close()
        return log_text

    def insert_log(self, j_id, timestamp, log):
        """Insert log message"""
        self.conn = sqlite3.connect('sfn_database.db')
        self.c = self.conn.cursor()
        self.c.execute('''INSERT INTO logs(job_id, time, log) VALUES(?,?,?)''', (j_id, timestamp, log))
        self.conn.commit()
        self.c.close()
        self.conn.close()

    @staticmethod
    def delete_db(*args):
        try:
            conn = sqlite3.connect('sfn_database.db')
            c = conn.cursor()
            if len(args) == 1:  # """Delete for configs""" # c_id
                c.execute("DELETE FROM configs WHERE conf_id=?", (args[0],))
                conn.commit()
            elif len(args) == 2:  # """Delete for recent camera messages"""  # c_id, m_id
                c.execute("DELETE FROM messages WHERE cam_id=? AND module_id=?", (args[0], args[1]))
                conn.commit()

            c.close()
            conn.close()
        except Exception as error:
            print('error executing deleting from db, error: {}'.format(error))
            return None

    def length_db(self):
        return len(self.query_db())

    @staticmethod
    def query_db(*args):
        """Query the recent camera messages database"""
        try:
            conn = sqlite3.connect('sfn_database.db', check_same_thread=False)
            c = conn.cursor()
            if len(args) == 0:  # No input
                c.execute("select * from messages")
                conn.commit()
            elif len(args) == 2:
                if args[0] is None:
                    c.execute("SELECT * FROM messages WHERE module_id=?", (args[1],))
                    conn.commit()
                elif args[1] is None:
                    c.execute("SELECT * FROM messages WHERE cam_id=?", (args[0],))
                    conn.commit()
                else:
                    c.execute("SELECT * FROM messages WHERE cam_id=? AND module_id=?", (args[0], args[1]))
                    conn.commit()

            rows = c.fetchall()
            c.close()
            conn.close()
            return rows
        except Exception as error:
            print('error executing query, error: {}'.format(error))
            return None

    @staticmethod
    def query_config_db(*args):
        """Query the configs database"""
        conn = sqlite3.connect('sfn_database.db', check_same_thread=False)
        c = conn.cursor()
        try:
            if len(args) == 0:  # No input
                c.execute("select * from configs")
                conn.commit()
            elif len(args) == 1:
                c.execute("SELECT * FROM configs WHERE conf_id=?", (args[0],))
                conn.commit()

            rows = c.fetchall()
            c.close()
            conn.close()
            return rows
        except Exception as error:
            print('error executing query, error: {}'.format(error))
            return None

    def __del__(self):
        self.conn.close()
        # self.c.close()

    def create_reg_message(self, timestamp):
        data = {
                'module_id': self.module_id,
                'module_type': self.module_type,
                'timestamp': timestamp,
                'state': self.state,
        }
        message = json.dumps(data)
        # message = json.loads(message)
        return message

    def create_obs_message(self, camera_ids, count, heat_map, timestamp_oldest, timestamp_newest, ground_plane_pos):
        data = {
                'module_id': self.module_id,
                'type_module': self.module_type,
                'camera_ids': camera_ids,
                'density_count': int(count),
                'density_map': heat_map.tolist(),
                'frame_byte_array': '',
                'image_dims': '',
                'ground_plane_position': ground_plane_pos,
                'timestamp_1': timestamp_oldest,
                'timestamp_2': timestamp_newest,
        }
        message = json.dumps(data)
        return message

    @staticmethod
    def load_urls(location, file_name):
        try:
            json_file = open(location + '/' + file_name + '.txt')
        except IOError:
            print('IoError')
        else:
            line = json_file.readline()
            urls = json.loads(line)
            json_file.close()
            print('URLS LOADED: ' + file_name)
            return urls

    @staticmethod
    def generate_amalgamated_top_down_map(top_down_maps, config_for_amalgamation):
        """
        Amalgamate N color images from a list of image paths.
        """
        x = []
        y = []
        w = []
        h = []
        all_rotated_images = []
        for i in range(len(top_down_maps)):
            # Convert from list of lists to matrix
            img = np.array(top_down_maps[i])
            rotated_img = rotate_image(img, config_for_amalgamation[i][2])  # angle

            all_rotated_images.append(rotated_img)
            x.append(config_for_amalgamation[i][0])  # latitude
            y.append(config_for_amalgamation[i][1])  # longitude
            w.append(rotated_img.shape[0])
            h.append(rotated_img.shape[1])

        amalgamation_latitude = min(x)
        amalgamation_longitude = min(y)

        d = [convert_to_meter(f, 0, amalgamation_latitude, 0) for f in x]  # distance
        amalgamation_w = int(max([i + j for i, j in zip(d, w)]))

        d = [convert_to_meter(0, f, 0, amalgamation_longitude) for f in y]  # distance
        amalgamation_h = int(max([i + j for i, j in zip(d, h)]))

        # Generate the amalgamated image
        img_amalgamation = np.zeros(shape=(amalgamation_w, amalgamation_h))

        for i in range(len(all_rotated_images)):
            dis_x = int(convert_to_meter(x[i], 0, amalgamation_latitude, 0))
            dis_y = int(convert_to_meter(0, y[i], 0, amalgamation_longitude))
            img_amalgamation[dis_x:(dis_x + w[i]), dis_y:(dis_y + h[i])] = all_rotated_images[i] + \
                img_amalgamation[dis_x:(dis_x + w[i]), dis_y:(dis_y + h[i])] * (all_rotated_images[i] == 0)

        # cv2.imshow('img_amalgamation', cv2.resize(img_amalgamation, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC))
        # cv2.waitKey(0)
        # cv2.imwrite('Global_density.png',
        #             cv2.resize(img_amalgamation * 255, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC))
        amalgamation_ground_plane_position = [amalgamation_latitude, amalgamation_longitude]
        return img_amalgamation, amalgamation_ground_plane_position
