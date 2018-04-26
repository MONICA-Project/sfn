# security_fusion_node.py
"""The class that handles the storage of current messages on the sfn_service and contains the functions to process those
messages"""
import pickle
import numpy as np
import cv2
import json
import base64
import sqlite3
from WP5.KU.SharedResources.convert_to_meter import convert_to_meter
from WP5.KU.SharedResources.rotate_image import rotate_image
import math
import time

__version__ = '0.1'
__author__ = 'RoViT (KU)'


def waste_time(time_amount):
    print('started')
    time.sleep(time_amount)
    print('finished')
    return 'Done'


class SecurityFusionNode:

    def __init__(self, module_id):
        self.module_id = module_id + '_crowd_density_global'
        self.module_type = 'crowd_density_global'
        self.state = 'active'

        # Create a data structure
        self.conn = sqlite3.connect('recent_camera_messages.db')
        self.c = self.conn.cursor()

        # Create table
        self.c.execute(
            '''Create TABLE IF NOT EXISTS messages(cam_id TEXT, module_id TEXT, msg TEXT)''')
        self.conn.commit()

    def insert_db(self, c_id, m_id, msg):
        self.c.execute('''INSERT INTO messages(cam_id, module_id, msg) VALUES(?,?,?)''', (c_id, m_id, msg))

    def delete_db(self, c_id, m_id):
        self.c.execute("DELETE FROM messages WHERE cam_id=? AND module_id=?", (c_id, m_id))

    def length_db(self):
        return len(self.query_db())

    def query_db(self,*args):
        try:
            if len(args)==0:  # No input
                self.c.execute("select * from messages")
            elif (len(args)==1):  # only camera_id
                self.c.execute("SELECT * FROM messages WHERE cam_id=?", args[0])
            elif (len(args)==2):  # both camera_id and
                self.c.execute("SELECT * FROM messages WHERE cam_id=? AND module_id=?", (args[0],args[1]))

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
    def generate_heat_map(detections, transform, gp_roi, ground_plane_size, frame=None, timestamp=None):
        detections = np.array(detections)
        # detections IS EITHER AN (MxN) IMAGE OR A (Mx2) LIST OF X Y COORDINATES
        if detections.shape[1] > 2:
            # CONVERT TO LIST OF POINTS
            detections_image = detections.copy()
            values = detections_image[detections_image > 0]
            detections = np.array(np.nonzero(detections_image > 0))
            detections = np.transpose(np.vstack([detections[1, :], detections[0, :]]))
        else:
            # ELSE CREATE VALUES FOR INDIVIDUAL DETECTIONS
            values = np.ones(len(detections))

        # TRANSFORM THE LIST OF DETECTIONS
        q = np.dot(transform, np.transpose(np.hstack([detections, np.ones([len(detections), 1])])))
        p = np.array(q[2, :])
        transformed_pts = np.int32(np.round(np.vstack([(q[0, :] / p), (q[1, :] / p)])))
        transformed_pts = np.vstack([transformed_pts, values])

        # import datetime
        # start = datetime.datetime.now()

        # FOR EACH DETECTION CHECK IT IS WITHIN THE gp_roi AND BIN
        x = transformed_pts[0, :]
        transformed_pts = transformed_pts[:, (gp_roi[0] < x) & (x < gp_roi[2])]
        y = transformed_pts[1, :]
        transformed_pts = transformed_pts[:, (gp_roi[1] < y) & (y < gp_roi[3])]

        # print(datetime.datetime.now() - start)
        # CREATE THE HEAT MAP, USING THE transformed_pts, USING THE NUMBER OF BINS DEFINED IN ground_plane_size,
        # WHERE WEIGHTS ARE THE AMOUNT ADDED TO EACH BIN FOR EACH POINT AND APPLYING THE RANGE GIVEN BY gp_roi
        heat_map, _, _ = np.histogram2d(transformed_pts[1, :], transformed_pts[0, :], bins=ground_plane_size[::-1],
                                        weights=transformed_pts[2, :],
                                        range=[[gp_roi[1], gp_roi[3]], [gp_roi[0], gp_roi[2]]])

        heat_image = None
        # IF A FRAME IS PROVIDED GET THE HEAT MAP OVERLAID
        if frame is not None:
            # heat_image = cv2.resize(heat_map, (0, 0), fx=10, fy=10)
            transform = np.array(transform)
            warped_image = cv2.warpPerspective(frame, transform, (10000, 10000))
            # USE cv2 TO DRAW CIRCLES FOR EACH POINT IN transformed_pts. SLOW
            # for i in range(len(detections)):
            #     cv2.circle(warped_image, (int(transformed_pts[0, i]), int(transformed_pts[1, i])), 3, (255, 0, 0), -1)

            # CHANGE TO GRAY SCALE AND GET ONLY THE roi FOR THE WARPED IMAGE
            if np.ndim(frame) > 2:
                warped_image = cv2.cvtColor(warped_image[gp_roi[1]: gp_roi[3], gp_roi[0]: gp_roi[2]],
                                            cv2.COLOR_RGB2GRAY)
            else:
                warped_image = warped_image[gp_roi[1]: gp_roi[3], gp_roi[0]: gp_roi[2]]
            # SCALE UP THE heat_map TO ENCOMPASS THE WHOLE WARPED roi
            heat_image = cv2.resize(heat_map, (gp_roi[2] - gp_roi[0], gp_roi[3] - gp_roi[1]))
            heat_image = ((warped_image / 255) / 3) + heat_image
            # SAVE THE IMAGE (NORMALISE UP TO 255)
            cv2.imwrite('Detections_' + str(timestamp) + '.jpeg', heat_image*255)
            # cv2.imshow('frame', heat_image)
            # cv2.waitKey(0)
        # TODO: THIS WILL LIKELY NEED CHANGING IN ORDER TO COMPRESS THESE IMAGES
        return heat_map.tolist(), heat_image

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

        cv2.imshow('img_amalgamation', cv2.resize(img_amalgamation, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC))
        cv2.waitKey(0)
        return img_amalgamation
