# get_top_down_heat_map.py
"""Helper function to convert a list of detections in the image plane to a top down perspective."""
import numpy as np
import cv2

__version__ = '0.2'
__author__ = 'Rob Dupre (KU)'


def generate_heat_map(detections, transform, gp_roi, ground_plane_size, frame=None, timestamp=None):
    """ Converts a heat map or list of detections from the image plane to a top down view, through the use of a pre-
    defined transformation
        Keyword arguments:
            detections --       Either a list of X, Y locations or an 1-D image where each pixel intensity correlates to
                                to the number of detections in that region
            transform --        Pre defined transformation matrix used to convert from image plane to top down
            gp_roi --           List[x1, y1, x2, y2] integers, defining 2 points used to specify a section of the top
                                down image that will be returned.
            ground_plane_size --List[size_X, size_Y] in meters represented by the gp_roi
            frame --            [OPTIONAL] the original frame on which the detections are based, used for debugging
            timestamp --        [OPTIONAL/required if frame is present] Time stamp of when the original detections were
                                made, used to label the saved debugging image.
        Returns:
            heat_map --         The top down heatmap, of size ground_plane_size, representing the 2-D histogram of
                                detection volume
            heat_image --       Overlay of the heat_map over the warped frame
        """
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
        transform = np.array(transform)
        warped_image = cv2.warpPerspective(frame, transform, (10000, 10000))

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
    return heat_map.tolist(), heat_image
