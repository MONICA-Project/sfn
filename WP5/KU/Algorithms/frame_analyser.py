# frame_analyser.py
import cv2
import numpy as np


class FrameAnalyser:

    def __init__(self, module_id):
        # VARIABLES REQUIRED FOR THE FINAL MESSAGE CREATION
        self.module_id = module_id
        self.module_type = 'analyser'
        self.state = True

        # CONSTANTS
        self.FONT = cv2.FONT_HERSHEY_SIMPLEX
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.WHITE = (255, 255, 255)

    def process_frame(self, frame, camera_id):
        raise NotImplementedError

    def create_obs_message(self):
        raise NotImplementedError

    def create_reg_message(self):
        raise NotImplementedError

    def load_settings(self):
        raise NotImplementedError

    @staticmethod
    def generate_heat_map(detections, transform, gp_roi, ground_plane_size, frame=None):
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
            warped_image = cv2.warpPerspective(frame, transform, (10000, 10000))
            # USE cv2 TO DRAW CIRCLES FOR EACH POINT IN transformed_pts. SLOW
            # for i in range(len(detections)):
            #     cv2.circle(warped_image, (int(transformed_pts[0, i]), int(transformed_pts[1, i])), 3, (255, 0, 0), -1)

            # CHANGE TO GRAY SCALE AND GET ONLY THE roi FOR THE WARPED IMAGE
            warped_image = cv2.cvtColor(warped_image[gp_roi[1]: gp_roi[3], gp_roi[0]: gp_roi[2]], cv2.COLOR_RGB2GRAY)
            # SCALE UP THE heat_map TO ENCOMPASS THE WHOLE WARPED roi
            heat_image = cv2.resize(heat_map, (gp_roi[2] - gp_roi[0], gp_roi[3] - gp_roi[1]))
            heat_image = ((warped_image / 255) / 3) + heat_image
            cv2.imshow('frame', heat_image)
            cv2.waitKey(0)

        return heat_map, heat_image
