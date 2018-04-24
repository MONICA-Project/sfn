import pickle
import numpy as np
import cv2
import json
import base64
import math


def rotateImage(image, angle):
    """
    Rotates the given image about it's centre
    """

    image_size = (image.shape[1], image.shape[0])
    image_center = tuple(np.array(image_size) / 2)

    rot_mat = np.vstack([cv2.getRotationMatrix2D(image_center, angle, 1.0), [0, 0, 1]])
    trans_mat = np.identity(3)

    w2 = image_size[0] * 0.5
    h2 = image_size[1] * 0.5

    rot_mat_notranslate = np.matrix(rot_mat[0:2, 0:2])

    tl = (np.array([-w2, h2]) * rot_mat_notranslate).A[0]
    tr = (np.array([w2, h2]) * rot_mat_notranslate).A[0]
    bl = (np.array([-w2, -h2]) * rot_mat_notranslate).A[0]
    br = (np.array([w2, -h2]) * rot_mat_notranslate).A[0]

    x_coords = [pt[0] for pt in [tl, tr, bl, br]]
    x_pos = [x for x in x_coords if x > 0]
    x_neg = [x for x in x_coords if x < 0]

    y_coords = [pt[1] for pt in [tl, tr, bl, br]]
    y_pos = [y for y in y_coords if y > 0]
    y_neg = [y for y in y_coords if y < 0]

    right_bound = max(x_pos)
    left_bound = min(x_neg)
    top_bound = max(y_pos)
    bot_bound = min(y_neg)

    new_w = int(abs(right_bound - left_bound))
    new_h = int(abs(top_bound - bot_bound))
    new_image_size = (new_w, new_h)

    new_midx = new_w * 0.5
    new_midy = new_h * 0.5

    dx = int(new_midx - w2)
    dy = int(new_midy - h2)


    # getTranslationMatrix2d: a numpy affine transformation matrix for a 2D translation of
    trans_mat = np.matrix([[1, 0, dx], [0, 1, dy], [0, 0, 1]])
    affine_mat = (np.matrix(trans_mat) * np.matrix(rot_mat))[0:2, :]
    result = cv2.warpAffine(image, affine_mat, new_image_size, flags=cv2.INTER_LINEAR)

    return result


# Convert the distance between 2 geo point into metre
def conversionTOmeter(lat1, lon1, lat2, lon2):  # generally used geo measurement function
    R = 6378.137   # Radius of earth in KM
    dLat = lat2 * math.pi / 180 - lat1 * math.pi / 180
    dLon = lon2 * math.pi / 180 - lon1 * math.pi / 180
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(lat1 * math.pi / 180) * math.cos(lat2 * math.pi / 180) \
                                              * math.sin(dLon/2) * math.sin(dLon/2)


    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c
    return(d * 1000)  # meters


class SecurityFusionNode:

    def __init__(self, module_id):
        self.module_id = module_id + '_crowd_density_global'
        self.module_type = 'crowd_density_global'
        self.state = 'active'

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
    def generate_amalgamated_topDown_map(topDown_maps, config_for_amal):
        """
        Amalgamate N color images from a list of image paths.
        """
        x = []
        y = []
        w = []
        h = []
        all_rotated_images = []
        for i in range(len(topDown_maps)):
            # Convert from list of lists to matrix
            img = np.array(topDown_maps[i])
            rotated_img = rotateImage(img, config_for_amal[i][2])  # angle

            all_rotated_images.append(rotated_img)
            x.append(config_for_amal[i][0])  # latitude
            y.append(config_for_amal[i][1])  # longitude
            w.append(rotated_img.shape[0])
            h.append(rotated_img.shape[1])

        amal_latitude = min(x)
        amal_longitude = min(y)

        #amal_w = int(max([a + b for a, b in zip(x, w)]) - amal_latitude)
        #amal_h = int(max([a + b for a, b in zip(y, h)]) - amal_longitude)

        #x = [2, 3, 11, 4, 55, 6, 7, 8, 3, 54]
        #(m, ind) = max((v, i) for i, v in enumerate(x))
        #print(m, ind)

        d= [conversionTOmeter(f, 0, amal_latitude, 0) for f in x]  # distance
        amal_w = int(max([i + j for i, j in zip(d, w)]))

        d = [conversionTOmeter(0, f, 0, amal_longitude) for f in y]  # distance
        amal_h = int(max([i + j for i, j in zip(d, h)]))

        print("---------------------------------")
        print(x)
        print(y)
        print(w)
        print(h)

        print(amal_latitude)
        print(amal_longitude)
        print(amal_w)
        print(amal_h)

        # Generate the amalgamated image
        img_amal = np.zeros(shape=(amal_w, amal_h))

        for i in range(len(all_rotated_images)):
            # y[3:8, 1:3] = X + y[3:8, 1:3] * (X == 0)
            dis_x = int(conversionTOmeter(x[i], 0, amal_latitude, 0))
            dis_y = int(conversionTOmeter(0, y[i], 0, amal_longitude))
            img_amal[dis_x:(dis_x + w[i]), dis_y:(dis_y + h[i])] = all_rotated_images[i] + \
                                                                   img_amal[dis_x:(dis_x + w[i]),
                                                                   dis_y:(dis_y + h[i])] * (
                                                                       all_rotated_images[i] == 0)


        cv2.imshow('img_amal', cv2.resize(img_amal, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC))
        cv2.waitKey(0)
        return img_amal
