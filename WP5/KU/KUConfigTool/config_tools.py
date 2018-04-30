# config_tools.py
"""Support functionality for the KU Camera Config app abstracted away from the UI
"""
import cv2
import numpy as np
import pickle
import requests
import json
import datetime

__version__ = '0.1'
__author__ = 'Rob Dupre (KU)'

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
        self.camera_type = 'RGB'
        self.camera_position = [0, 0]
        self.camera_height = 0
        self.camera_bearing = 0
        self.camera_tilt = 0
        self.state = 1
        self.zone_id = 'TEMP'
        # PAGE TWO
        # [Xo, Yo, X1, Y1]
        self.module_types = [0, 0, 1, 0, 0, 0]
        self.frame_roi = [0, 300, 0, 300]
        # PAGE THREE
        # [XoYo [x,y], X1Yo [x,y], XoY1 [x,y], X1Y1[x,y], RefPoint [x,y]]
        self.ref_pt = [[50, 50], [300, 50], [50, 300], [300, 300], [100, 100]]
        self.ground_plane_position = [0, 0]
        self.ground_plane_orientation = 0
        self.transform = None
        # PAGE FOUR
        # [Xo, Yo, X1, Y1]
        self.ground_plane_roi = [200, 300, 200, 300]
        self.ground_plane_size = [0, 0]
        self.warped_image = np.zeros([768, 1080, 3], dtype=np.int)

        # PAGE FOUR
        self.flow_rois = []
        self.ground_plane_size = [0, 0]
        self.warped_image = np.zeros([768, 1080, 3], dtype=np.int)

    def check_inputs(self):
        print(self.camera_id, self.camera_position)
        # TODO: CREATE CHECKS TO ENSURE THESE INPUTS ARE IN A CORRECT FORMAT
        if self.transform is not None:
            return True
        else:
            print('AN ELEMENT IS NOT COMPLETE')
            return False

    def perspective_transform(self, image, pts2=np.float32([[2000, 2000], [2250, 2000], [2000, 2250], [2250, 2250]]),
                              new_image_size=(10000, 10000)):
        """Takes an input image and given the self.transform matrix, warps the image.

        Keyword arguments:
            image --            MxN RGB or BW image
            pts2 --             the arbitrary points which the self.ref_pt are mapped to
            new_image_size --   The defined size of the newly warped image, may be too large or too small.
        Returns:
            warped_image --     The source image now warped and with the size new_image_size
        """

        pts1 = np.float32(self.ref_pt[0:4])
        self.transform, mask = cv2.findHomography(pts1, pts2)

        self.warped_image = cv2.warpPerspective(image, self.transform, new_image_size)
        # cv2.imwrite('test.png', self.warped_image)
        return self.warped_image

    def shrink_image(self, image, both=False):
        """Takes an input image and removes any black borders (used to shrink warped images down)

        Keyword arguments:
            image --            MxN RGB or BW image.
            both --             [OPTIONAL] when True removes borders from both left and right, top and bottom, False
                                removes just left anf top borders.
        Returns:
            warped_image --     The newly shrunk image
        """
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
        """Takes the warped image and draws on red circles on the now transformed ref_pt.

        Keyword arguments:
            image --            MxN RGB or BW image.
        Returns:
            warped_image --     image with now drawn ref_pt on"""
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
        """Takes the current defined variables for the camera config and saves them to a .pk file in the current dir. If
        url is specified a registration message is sent containing the json payload.

        Keyword arguments:
            url --          [OPTIONAL] when speficied a requests request is sent containing a JSON payload of the
                            current config.
        """
        if self.check_inputs():
            try:
                fo = open((str(self.camera_id) + '.pk'), 'wb')
            except IOError:
                print('IOError SAVING .pk FILE')
            else:
                data = {'camera_id': self.camera_id,
                        'camera_type': self.camera_type,
                        'camera_position': self.camera_position,
                        'camera_height': self.camera_height,
                        'camera_bearing': self.camera_bearing,
                        'camera_tilt': self.camera_tilt,
                        'ground_plane_position': self.ground_plane_position,
                        'ground_plane_orientation': self.ground_plane_orientation,
                        'image_2_ground_plane_matrix': self.transform,
                        'zone_id': self.zone_id,
                        'module_types': self.module_types,
                        'frame_roi': self.frame_roi,
                        'flow_rois': self.flow_rois,
                        'timestamp': datetime.datetime.utcnow().isoformat(),
                        'state': self.state,
                        'ground_plane_roi': self.ground_plane_roi,
                        'ground_plane_size': self.ground_plane_size,
                        'ref_pt': self.ref_pt}
                pickle.dump(data, fo)
                fo.close()

            # CONVERT TRANSFORM TO A SERIALIZABLE FORMAT
            data['image_2_ground_plane_matrix'] = self.transform.tolist()
            # CONVERT module_types TO LIST OF MODULES
            modules = []
            if data['module_types'][0] == 1:
                modules.append('crowd_density_local')
            if data['module_types'][1] == 1:
                modules.append('flow_analysis')
            if data['module_types'][2] == 1:
                modules.append('fight_detection')
            if data['module_types'][3] == 1:
                modules.append('object_detection')
            data['module_types'] = modules

            # CONVERT STATE VARIABLE TO TEXT
            if self.state == 1:
                data['state'] = 'active'
            elif self.state == 0:
                data['state'] = 'inactive'

            # REMOVE ref_pts FROM THE REGISTRATION MESSSAGE
            data.pop('ref_pt')

            # WRITE THE REG MESSAGE TO txt FILE
            try:
                outfile = open(self.camera_id + '_reg.txt', 'w')
            except IOError:
                print('IOError SAVING .txt FILE')
            else:
                json.dump(data, outfile)
                outfile.close()

            # IF A URL HAS BEEN GIVEN TO A REST SERVICE TRY AND SEND THE JSON MESSAGE
            if url != 'none':
                headers = {
                    'content-Type': 'application/json',
                }
                try:
                    res = requests.post(url, data=json.dumps(data), headers=headers)
                except requests.exceptions.RequestException as e:
                    print(e)
                else:
                    print('Registration Message has been Sent. Response: ' + str(res.status_code) + '. ' + res.text)

    def load_config(self, cam_id):
        """Loads the defined variables for a .pk file with name cam_id.

        Keyword arguments:
            cam_id --       String ID for the camera that the settings are to be loaded for.
        Returns:
            A bool --       True if load is successful
            """
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
            if 'camera_bearing' in entry:
                self.camera_bearing = entry['camera_bearing']
            self.camera_tilt = entry['camera_tilt']
            if 'ground_plane_gps' in entry:
                self.ground_plane_position = entry['ground_plane_gps']
            if 'ground_plane_position' in entry:
                self.ground_plane_position = entry['ground_plane_position']
            self.ground_plane_orientation = entry['ground_plane_orientation']
            if 'heat_map_transform' in entry:
                self.transform = entry['heat_map_transform']
            if 'image_2_ground_plane_matrix' in entry:
                self.transform = entry['image_2_ground_plane_matrix']
            if 'zone_id' in entry:
                self.zone_id = entry['zone_id']
            if 'module_types' in entry:
                self.module_types = entry['module_types']
            if 'state' in entry:
                self.state = entry['state']
            if 'roi' in entry:
                self.frame_roi = entry['roi']
            if 'frame_roi' in entry:
                self.frame_roi = entry['frame_roi']
            if 'flow_rois' in entry:
                self.flow_rois = entry['flow_rois']
            self.ground_plane_roi = entry['ground_plane_roi']
            self.ground_plane_size = entry['ground_plane_size']
            self.ref_pt = entry['ref_pt']
            fo.close()
            print('SETTINGS LOADED FOR CAMERA: ' + self.camera_id)
            return True
