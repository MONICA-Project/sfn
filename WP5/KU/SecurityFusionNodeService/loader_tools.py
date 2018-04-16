import pickle
import numpy as np
import cv2
import json
import base64


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
                entry['heat_map_transform'] = entry['heat_map_transform'].tolist()
                print('SETTINGS LOADED FOR CAMERA: ' + cam_id)
                return entry
            else:
                print('WRONG CAMERA ID: CONFIG FILE INCORRECT')
                return None
        else:
            line = json_file.readline()
            data = json.loads(json.loads(line))
            json_file.close()
            data['heat_map_transform'] = data['heat_map_transform'].tolist()
            return data


def load_json_txt(location, file_name):
    try:
        json_file = open(location + file_name + '.txt')
    except IOError:
        print('IoError')
    else:
        line = json_file.readline()
        data = json.loads(json.loads(line))
        json_file.close()
        print('MESSAGE LOADED: ' + file_name)
        return data


def decode_image(string, image_dims, print_flag):
    d = base64.b64decode(string)
    rebuilt_frame = np.frombuffer(d, dtype=np.uint8)
    frame = np.reshape(rebuilt_frame, (image_dims[0], image_dims[1]))
    if print_flag:
        cv2.imshow('RECONSTRUCTED_FRAME', frame)
        cv2.waitKey(0)
    # TODO: THIS IS TO RESCALE THE IMAGE BACK UP TO ORIGINAL SIZE
    frame = cv2.resize(frame, (0, 0), fx=4, fy=4)
    return frame
