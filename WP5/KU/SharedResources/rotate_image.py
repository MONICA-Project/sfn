# rotate_image.py
"""Helper function to rotate an image by an angle."""
__version__ = '0.1'
__author__ = 'Hajar Sadeghi (KU)'

import numpy as np
import cv2


def rotate_image(image, angle):
    """
    Rotates the given image about it's centre
    """

    image_size = (image.shape[1], image.shape[0])
    image_center = tuple(np.array(image_size) / 2)

    rot_mat = np.vstack([cv2.getRotationMatrix2D(image_center, angle, 1.0), [0, 0, 1]])
    trans_mat = np.identity(3)

    w2 = image_size[0] * 0.5
    h2 = image_size[1] * 0.5

    rot_mat_no_translate = np.matrix(rot_mat[0:2, 0:2])

    tl = (np.array([-w2, h2]) * rot_mat_no_translate).A[0]
    tr = (np.array([w2, h2]) * rot_mat_no_translate).A[0]
    bl = (np.array([-w2, -h2]) * rot_mat_no_translate).A[0]
    br = (np.array([w2, -h2]) * rot_mat_no_translate).A[0]

    x_coordinate = [pt[0] for pt in [tl, tr, bl, br]]
    x_pos = [x for x in x_coordinate if x > 0]
    x_neg = [x for x in x_coordinate if x < 0]

    y_coordinate = [pt[1] for pt in [tl, tr, bl, br]]
    y_pos = [y for y in y_coordinate if y > 0]
    y_neg = [y for y in y_coordinate if y < 0]

    right_bound = max(x_pos)
    left_bound = min(x_neg)
    top_bound = max(y_pos)
    bot_bound = min(y_neg)

    new_w = int(abs(right_bound - left_bound))
    new_h = int(abs(top_bound - bot_bound))
    new_image_size = (new_w, new_h)

    new_mid_x = new_w * 0.5
    new_mid_y = new_h * 0.5

    dx = int(new_mid_x - w2)
    dy = int(new_mid_y - h2)

    # getTranslationMatrix2d: a numpy affine transformation matrix for a 2D translation of
    trans_mat = np.matrix([[1, 0, dx], [0, 1, dy], [0, 0, 1]])
    affine_mat = (np.matrix(trans_mat) * np.matrix(rot_mat))[0:2, :]
    result = cv2.warpAffine(image, affine_mat, new_image_size, flags=cv2.INTER_LINEAR)

    return result


