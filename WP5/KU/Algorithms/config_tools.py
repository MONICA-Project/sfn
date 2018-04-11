import cv2
import numpy as np
import pickle
import requests
import json
import datetime

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
FONT = cv2.FONT_HERSHEY_SIMPLEX


class ConfigTools:
    # SET UP THE INITIAL POINTS AND CONTROL VARIABLES
    def __init__(self):

        # PAGE ONE
        self.camera_id = 'TEMP'
        self.camera_position = [0, 0]
        self.camera_tilt = 0
        self.camera_height = 0
        self.camera_type = 'RGB'
        self.state = 'active'
        # PAGE TWO
        # [Xo, Yo, X1, Y1]
        self.roi = [0, 300, 0, 300]
        # PAGE THREE
        # [XoYo [x,y], X1Yo [x,y], XoY1 [x,y], X1Y1[x,y], RefPoint [x,y]]
        self.ref_pt = [[50, 50], [300, 50], [50, 300], [300, 300], [100, 100]]
        self.ground_plane_position = [0, 0]
        self.ground_plane_orientation = 0
        self.transform = 0
        # PAGE FOUR
        # [Xo, Yo, X1, Y1]
        self.ground_plane_roi = [200, 300, 200, 300]
        self.ground_plane_size = [0, 0]
        self.warped_image = np.zeros([768, 1080, 3], dtype=np.int)

    def check_inputs(self):
        print(self.camera_id, self.camera_position)
        # TODO: CREATE CHECKS TO ENSURE THESE INPUTS ARE IN A CORRECT FORMAT
        return True

    def perspective_transform(self, image, pts2=np.float32([[2000, 2000], [2250, 2000], [2000, 2250], [2250, 2250]]),
                              new_image_size=(10000, 10000)):

        pts1 = np.float32(self.ref_pt[0:4])
        self.transform, mask = cv2.findHomography(pts1, pts2)

        self.warped_image = cv2.warpPerspective(image, self.transform, new_image_size)
        return self.warped_image

    def shrink_image(self, image, both=False):
        # SHRINK THE IMAGE TO REMOVE ANY BLACK BORDERS
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cols = np.max(gray, axis=0)
        c1 = np.argmax(cols > 0)
        c2 = np.argmax(np.flip(cols, axis=0) > 0)
        rows = np.max(gray, axis=1)
        r1 = np.argmax(rows > 0)
        r2 = np.argmax(np.flip(rows, axis=0) > 0)
        # IF BOTH TRIP THE IMAGE BOTH SIDES
        if both:
            self.warped_image = image[r1:-r2, c1:-c2, :]
        #     ELSE JUST TRIM THE BACK EDGES.
        else:
            self.warped_image = image[:-r2, :-c2, :]
        # cv2.imshow('t', cv2.resize(t_image, (1000, 1000))); cv2.waitKey(0)
        return self.warped_image

    def transform_points(self, warped_image):
        pts = np.array(self.ref_pt)
        if pts.shape[1] == 2:
            q = np.dot(self.transform, np.transpose(np.hstack([pts, np.ones([len(pts), 1])])))
            p = np.array(q[2, :])
            transformed_pts = np.int32(np.round(np.vstack([(q[0, :] / p), (q[1, :] / p)])))

            for i in range(len(pts)):
                cv2.circle(warped_image, (transformed_pts[0, i], transformed_pts[1, i]), 20, (255, 0, 0), -1)

            return warped_image
        else:
            print("WRONG INPUT SIZE")

    def save_config(self, url=None):
        if self.check_inputs():
            fo = open((str(self.camera_id) + '.pk'), 'wb')
            data = {'camera_id': self.camera_id,
                    'camera_type': self.camera_type,
                    'camera_position': self.camera_position,
                    'camera_height': self.camera_height,
                    # 'camera_bearing': self.camera_bearing,
                    'camera_tilt': self.camera_tilt,
                    'ground_plane_position': self.ground_plane_position,
                    'ground_plane_orientation': self.ground_plane_orientation,
                    'image_2_ground_plane_matrix': self.transform,
                    'timestamp': datetime.datetime.utcnow().isoformat(),
                    'state': 'active',
                    'roi': self.roi,
                    'ground_plane_roi': self.ground_plane_roi,
                    'ground_plane_size': self.ground_plane_size,
                    'ref_pt': self.ref_pt}
            pickle.dump(data, fo)
            fo.close()
            # WRITE THE REG MESSAGE TO txt FILE
            try:
                outfile = open(self.camera_id + '.txt', 'w')
            except IOError:
                print('IOError')
            else:
                json.dump(data, outfile)

            # IF A URL HAS BEEN GIVEN TO A REST SERVICE TRY AND SEND THE JSON MESSAGE
            if url != 'none':
                try:
                    req = requests.get(url, json=json.dumps(data))
                except requests.exceptions.RequestException as e:
                    print(e)
                else:
                    print('Registration Message has been Sent')

    def load_config(self, cam_id):
        try:
            fo = open((str(cam_id) + '.pk'), 'rb')
        except IOError:
            print('IoError')
            return False
        else:
            entry = pickle.load(fo, encoding='latin1')
            self.camera_id = entry['camera_id']
            self.camera_type = entry['camera_type']
            self.camera_position = entry['camera_position']
            self.camera_height = entry['camera_height']
            # self.camera_bearing = entry['camera_bearing']
            self.camera_tilt = entry['camera_tilt']
            self.ground_plane_position = entry['ground_plane_gps']
            # self.ground_plane_position = entry['ground_plane_position']
            self.ground_plane_orientation = entry['ground_plane_orientation']
            self.transform = entry['heat_map_transform']
            # self.transform = entry['image_2_ground_plane_matrix']
            # self.state = entry['state']
            self.roi = entry['roi']
            self.ground_plane_roi = entry['ground_plane_roi']
            self.ground_plane_size = entry['ground_plane_size']
            self.ref_pt = entry['ref_pt']
            fo.close()
            print('SETTINGS LOADED FOR CAMERA: ' + self.camera_id)
            return True
