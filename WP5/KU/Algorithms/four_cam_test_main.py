# sfn_service.py
"""A test application designed to mimic (badly) the VCA framework."""
import datetime
import json
import pickle
import cv2
from random import randrange
import requests
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
from WP5.KU.definitions import KU_DIR
from WP5.KU.SharedResources.cam_video_streamer import CamVideoStreamer
from WP5.KU.SharedResources.frame_streamer import ImageSequenceStreamer
import WP5.KU.SharedResources.get_incrementer as inc
from WP5.KU.Algorithms.crowd_density_local.get_crowd import GetCrowd
from WP5.KU.Algorithms.flow_analysis.get_flow import GetFlow
from WP5.KU.Algorithms.object_detection.get_people import GetPeople

__version__ = '0.1'
__author__ = 'Rob Dupre (KU)'


def dataset(index):
    dataset_folder = 'C:/Users/Rob/Desktop/CROWD_DATASETS/'
    dataset_folder = '/ocean/datasets/'

    return {
        # [Address, Stream, Settings File
        19: [(dataset_folder + '/MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_1/'), 0, 'RIF_CAM_1'],
        20: [(dataset_folder + '/MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_2/'), 0, 'RIF_CAM_2'],
        21: [(dataset_folder + '/MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_3/'), 0, 'RIF_CAM_3'],
        22: [(dataset_folder + '/MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_4/'), 0, 'RIF_CAM_4'],
        23: [(dataset_folder + '/MONICA/BONN/Rein in Flammen 2018/20180505_233000_camera_1/'), 0, 'RIF_CAM_1'],
        24: [(dataset_folder + '/MONICA/BONN/Rein in Flammen 2018/20180505_233000_camera_2/'), 0, 'RIF_CAM_2'],
        25: [(dataset_folder + '/MONICA/BONN/Rein in Flammen 2018/20180505_233000_camera_3/'), 0, 'RIF_CAM_3'],
        26: [(dataset_folder + '/MONICA/BONN/Rein in Flammen 2018/20180505_233000_camera_4/'), 0, 'RIF_CAM_4'],
    }.get(index, -1)  # -1 is default if id not found


def load_settings(location):
    fo = open((location + '.pk'), 'rb')
    entry = pickle.load(fo, encoding='latin1')
    return entry


display = True

# LOAD THE SETTINGS AND PASS THEN WHEN PROCESSING A FRAME
info1 = dataset(19)
settings1 = load_settings(KU_DIR + '/KUConfigTool/' + '/' + info1[2])
info2 = dataset(20)
settings2 = load_settings(KU_DIR + '/KUConfigTool/' + '/' + info2[2])
info3 = dataset(21)
settings3 = load_settings(KU_DIR + '/KUConfigTool/' + '/' + info3[2])
info4 = dataset(22)
settings4 = load_settings(KU_DIR + '/KUConfigTool/' + '/' + info4[2])

settings = [settings1, settings2, settings3, settings4]
info = [info1, info2, info3, info4]

# CREATE AN analyser OBJECT AND CREATE THE REGISTRATION MESSAGE
# analyser = GetCrowd('001')
# analyser = GetPeople('001')
analyser = GetFlow('001')

linksmart_url = 'http://127.0.0.2:3389/add_config'
# linksmart_url = 'https://portal.monica-cloud.eu/scral/sfn/crowdmonitoring'
reg_message = analyser.create_reg_message(datetime.datetime.utcnow().isoformat())
with open(KU_DIR + '/Algorithms/registration_messages/' + analyser.module_id + '_' + analyser.type_module + '_reg.txt',
          'w') as outfile:
    outfile.write(reg_message)
reg_message = json.loads(reg_message)

try:
    res = requests.post(linksmart_url, data=reg_message, headers={'content-Type': 'application/json'})
except requests.exceptions.RequestException as e:
    print(e)
else:
    print('Registration Message has been Sent. Response: ' + str(res.status_code) + '. ' + res.text)


sfn_url = 'http://127.0.0.1:5000/message'
cam1 = ImageSequenceStreamer(info1[0], info1[1], (1080, 768), loop_last=False, repeat=True)
cam2 = ImageSequenceStreamer(info2[0], info2[1], (1080, 768), loop_last=False, repeat=True)
cam3 = ImageSequenceStreamer(info3[0], info3[1], (1080, 768), loop_last=False, repeat=True)
cam4 = ImageSequenceStreamer(info4[0], info4[1], (1080, 768), loop_last=False, repeat=True)
cam = [cam1, cam2, cam3, cam4]

count = 0
while cam1.open() & cam2.open() & cam3.open() & cam4.open():

    # choose random camera
    random_index = randrange(0, len(cam))
    frame = cam[random_index].read()

    setting = settings[random_index]

    if analyser.type_module == 'flow':
        message, result = analyser.process_frame(frame, setting['camera_id'], setting['frame_roi'], setting['flow_rois'])
    elif analyser.type_module == 'crowd_density_local':
        message, result = analyser.process_frame(frame, setting['camera_id'], setting['frame_roi'],
                                                 setting['image_2_ground_plane_matrix'],
                                                 setting['ground_plane_roi'], setting['ground_plane_size'])

    # SEND A HTTP REQUEST OFF
    # try:
    #     res = requests.post(sfn_url, json=message)
    # except requests.exceptions.RequestException as e:
    #     print(e)
    # else:
    #     print('Obs Message Sent. Response: ' + str(res.status_code) + '. ' + res.text)

    # WRITE FILES FOR USE LATER
    save_folder = str(Path(__file__).absolute().parents[0]) + '/algorithm_output/'
    # cv2.putText(result, 'Number of People: {}'.format(json.loads(message)['density_count']), (10, 70),
    #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    if result != []:
        cv2.imwrite(save_folder + info[random_index][2] + '_' + reg_message['type_module'] + '_Result_' +
                    str(inc.get_incrementer(count, 5)) + '.jpeg', result)

        with open(save_folder + info[random_index][2] + '_' + reg_message['type_module'] + '_' +
                      str(inc.get_incrementer(count, 5)) + '.txt', 'w') as outfile:
            outfile.write(message)
        count = count + 1
        if display:
            key = cv2.waitKey(1) & 0xFF
            # KEYBINDINGS FOR DISPLAY
            cv2.imshow('frame', frame)
            if key == 27:  # exit
                break