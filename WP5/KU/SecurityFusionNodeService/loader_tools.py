# loader_tools.py
""" A set of functions to load JSON messages from text file, decode base64 encoded images and read configs from .pk
files"""
import pickle
import numpy as np
import json
import base64

__version__ = '0.1'
__author__ = 'RoViT (KU)'


def load_settings(settings_location, cam_id, pickel_file=True):
    try:
        if pickel_file:
            fo = open((settings_location + str(cam_id) + '.pk'), 'rb')
        else:
            json_file = open((settings_location + str(cam_id) + '.txt'))
    except IOError:
        print('IoError')
        return None
    else:
        if pickel_file:
            entry = pickle.load(fo, encoding='latin1')
            fo.close()
            if entry['camera_id'] == cam_id:
                entry['image_2_ground_plane_matrix'] = entry['image_2_ground_plane_matrix'].tolist()
                print('SETTINGS LOADED FOR CAMERA: ' + cam_id)
                return entry
            else:
                print('WRONG CAMERA ID: CONFIG FILE INCORRECT')
                return None
        else:
            line = json_file.readline()
            # TODO: CHECK THIS IMPORT STILL WORKS
            data = json.loads(line)
            json_file.close()
            return data


def load_json_txt(location, file_name):
    try:
        json_file = open(location + file_name + '.txt')
    except IOError:
        print('IoError')
    else:
        line = json_file.readline()
        data = json.loads(line)
        json_file.close()
        print('MESSAGE LOADED: ' + file_name)
        return data


def save_json_txt(data, location, file_name):
    message = json.dumps(data)
    try:
        txt_file = open(location + '/' + file_name + '.txt', 'w')
    except IOError:
        print('IoError')
    else:
        txt_file.write(message)
        txt_file.close()
        print('MESSAGE SAVED: ' + file_name)


def decode_image(string, image_dims, print_flag):
    d = base64.b64decode(string)
    rebuilt_frame = np.frombuffer(d, dtype=np.uint8)
    frame = np.reshape(rebuilt_frame, (image_dims[0], image_dims[1]))
    if print_flag:
        import cv2
        cv2.imshow('RECONSTRUCTED_FRAME', frame)
        cv2.waitKey(0)
    return frame
