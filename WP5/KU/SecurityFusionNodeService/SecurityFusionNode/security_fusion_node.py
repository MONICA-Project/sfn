# security_fusion_node.py
"""The class that handles the storage of current messages on the sfn_service and contains the functions to process those
messages"""
import numpy as np
import cv2
import json
import sqlite3
from WP5.KU.SharedResources.convert_to_meter import convert_to_meter
from WP5.KU.SharedResources.rotate_image import rotate_image

__version__ = '0.1'
__author__ = 'RoViT (KU)'


class SecurityFusionNode:

    def __init__(self, module_id):
        self.module_id = module_id + '_crowd_density_global'
        self.module_type = 'crowd_density_global'
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

        self.c.execute('''INSERT INTO messages(cam_id, module_id, msg) VALUES(?,?,?)''', (c_id, m_id, msg))
        return log_text

    def insert_config_db(self, c_id, msg):
        """Insert for configs"""
        self.c.execute('''INSERT INTO configs(conf_id, msg) VALUES(?,?)''', (c_id, msg))

    def delete_db(self, c_id, m_id):
        """Delete for recent camera messages"""
        self.c.execute("DELETE FROM messages WHERE cam_id=? AND module_id=?", (c_id, m_id))

    def delete_db(self, c_id):
        """Delete for configs"""
        self.c.execute("DELETE FROM configs WHERE conf_id=?", c_id)

    def length_db(self):
        return len(self.query_db())

    def query_db(self, *args):
        """Query the recent camera messages database"""
        try:
            if len(args) == 0:  # No input
                self.c.execute("select * from messages")
            elif len(args) == 2:
                if args[0] is None:
                    self.c.execute("SELECT * FROM messages WHERE module_id=?", (args[1],))
                elif args[1] is None:
                    self.c.execute("SELECT * FROM messages WHERE cam_id=?", (args[0],))
                else:
                    self.c.execute("SELECT * FROM messages WHERE cam_id=? AND module_id=?", (args[0],args[1]))

            rows = self.c.fetchall()
            return rows
        except Exception as error:
            print('error executing query, error: {}'.format(error))
            return None

    def query_config_db(self, *args):
        """Query the configs database"""
        try:
            if len(args) == 0:  # No input
                self.c.execute("select * from configs")
            elif len(args) == 1:
                    self.c.execute("SELECT * FROM configs WHERE conf_id=?", (args[0],))

            rows = self.c.fetchall()
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

    def create_obs_message(self, camera_ids, count, heat_map, timestamp_oldest, timestamp_newest):
        data = {
                'module_id': self.module_id,
                'type_module': self.module_type,
                'camera_ids': camera_ids,
                'density_count': int(count),
                'density_map': heat_map.tolist(),
                'frame_byte_array': '',
                'image_dims': '',
                'timestamp_1': timestamp_oldest,
                'timestamp_2': timestamp_newest,
        }
        message = json.dumps(data)
        return message

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
        cv2.imwrite('Global_density.png',
                    cv2.resize(img_amalgamation * 255, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC))
        return img_amalgamation
