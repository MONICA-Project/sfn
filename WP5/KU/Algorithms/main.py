# sfn_service.py
"""A test application designed to mimic (badly) the VCA framework."""
import datetime
import arrow
import json
import pickle
import cv2
import requests
import uuid
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
        # [Address, Stream, Settings File]
        0: ['rtsp://root:pass@10.144.129.107/axis-media/media.amp', 'Live', 'CAMERA_KU'],
        # [Location, Start Frame, Settings File]
        1: [(dataset_folder + 'UCSD_Anomaly/UCSDped1/Train/Train001/'), 0],
        2: [(dataset_folder + 'Mall_Dataset/frames/'), 0],
        3: [(dataset_folder + 'EWAP_Dataset/seq_eth/'), 0],
        4: [(dataset_folder + 'EWAP_Dataset/seq_hotel/'), 0],
        5: [(dataset_folder + 'YOUTUBE/TIMES_SQUARE/'), 0],
        6: [(dataset_folder + 'YOUTUBE/DELHI_CROWD/'), 0],
        7: [(dataset_folder + 'KU_Courtyard_Dataset/20130805_140532_52EB_00408CDCC71E/'), 50],
        8: [(dataset_folder + 'KU_LAB/Output_1/'), 15],
        9: [(dataset_folder + 'OXFORD_TOWNCENTRE/TownCentreXVID/'), 1, 2000],
        10: [(dataset_folder + 'MONICA/TO/KFF 2017/channel 2/2017-07-09 19-40-00~19-50-00/'), 0, 'KFF_CAM_2'],
        11: [(dataset_folder + 'MONICA/TO/KFF 2017/channel 4/2017-07-08 14-00-00~14-10-00/'), 0, 'KFF_CAM_4'],
        12: [(dataset_folder + 'MONICA/TO/KFF 2017/channel 8/2017-07-08 20-40-00~20-50-00/'), 0, 'KFF_CAM_8'],
        13: [(dataset_folder + '/MONICA/SAMPLE_VIDEOS/KFF/'), 0],
        14: [(dataset_folder + '/MONICA/SAMPLE_VIDEOS/LED/'), 0],
        15: [(dataset_folder + '/MONICA/SAMPLE_VIDEOS/DOM/'), 0],
        16: [(dataset_folder + '/MONICA/SAMPLE_VIDEOS/MRK_1/'), 0],
        17: [(dataset_folder + '/MONICA/SAMPLE_VIDEOS/MRK_2/'), 0],
        18: [(dataset_folder + '/Temp/'), 0, 'KFF_CAM_8'],
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
info = dataset(12)
# info = dataset(0)
print(info)

# LOAD THE SETTINGS AND PASS THEN WHEN PROCESSING A FRAME
settings = load_settings(KU_DIR + '/KUConfigTool/' + '/' + info[2])

# CREATE AN analyser OBJECT AND CREATE THE REGISTRATION MESSAGE
# analyser = GetCrowd(str(uuid.uuid5(uuid.NAMESPACE_DNS, 'crowd_density_local')))
# analyser = GetFlow('001')
analyser = GetFlow(str(uuid.uuid5(uuid.NAMESPACE_DNS, 'flow')))

reg_message = analyser.create_reg_message(arrow.utcnow())
with open(KU_DIR + '/Algorithms/registration_messages/' + analyser.module_id + '_' + analyser.type_module + '_reg.txt',
          'w') as outfile:
    outfile.write(reg_message)
outfile.close()
reg_message = json.loads(reg_message)

sfn_url = 'http://127.0.0.1:5000/message'
if info == -1:
    print('NO DATA SET SELECTED')
else:
    if info[1] == 'Live':
        cap = CamVideoStreamer(info[0])
        cap.start()
        if cap.open():
            print("CAMERA CONNECTION IS ESTABLISHED.")
        else:
            print("FAILED TO CONNECT TO CAMERA.")
            exit(-1)

        count = 0
        while cap.open():
            frame = cap.read()
            if analyser.type_module == 'flow':
                message, result = analyser.process_frame(frame, settings['camera_id'], settings['frame_roi'],
                                                         settings['flow_rois'])
            elif analyser.type_module == 'crowd_density_local':
                message, result = analyser.process_frame(frame, settings['camera_id'], settings['frame_roi'],
                                                         settings['image_2_ground_plane_matrix'],
                                                         settings['ground_plane_roi'], settings['ground_plane_size'])

            # SEND A HTTP REQUEST OFF
            try:
                res = requests.post(sfn_url, json=message)
            except requests.exceptions.RequestException as e:
                print(e)
            else:
                print('Obs Message Sent. Response: ' + str(res.status_code) + '. ' + res.text)

            save_folder = str(Path(__file__).absolute().parents[0]) + '/algorithm_output/'
            # cv2.putText(frame, json.dumps(message, indent=4), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            #             (255, 255, 255), 1, cv2.LINE_AA)
            # cv2.imwrite(save_folder + info[2] + '_' + reg_message['type_module'] + '_Result_' +
            #             str(inc.get_incrementer(count, 5)) + '.jpeg', frame)
            with open(save_folder + info[2] + '_' + reg_message['type_module'] + '_' +
                      str(inc.get_incrementer(count, 5)) + '.txt', 'w') as outfile:
                outfile.write(message)
            count = count + 1
            if display:
                key = cv2.waitKey(1) & 0xFF
                # KEYBINDINGS FOR DISPLAY
                cv2.imshow('frame', frame)
                if key == 27:  # exit
                    break
    else:
        cam = ImageSequenceStreamer(info[0], info[1], (1080, 768), loop_last=False, repeat=True)
        count = 0
        while cam.open():
            frame = cam.read()
            if analyser.type_module == 'flow':
                message, result = analyser.process_frame(frame, settings['camera_id'], settings['frame_roi'],
                                                         settings['flow_rois'])
            elif analyser.type_module == 'crowd_density_local':
                message, result = analyser.process_frame(frame, settings['camera_id'], settings['frame_roi'],
                                                         settings['image_2_ground_plane_matrix'],
                                                         settings['ground_plane_roi'], settings['ground_plane_size'])

            # SEND A HTTP REQUEST OFF
            # try:
            #     res = requests.post(sfn_url, json=message)
            # except requests.exceptions.RequestException as e:
            #     print(e)
            # else:
            #     print('Obs Message Sent. Response: ' + str(res.status_code) + '. ' + res.text)

            # WRITE FILES FOR USE LATER
            save_folder = str(Path(__file__).absolute().parents[0]) + '/algorithm_output/'
            if result != []:  # result == [], IF WE ARE IN THE FIRST FRAME OF THE CURRENT CAMERA
                if result is not None:  # result is None, IF WE DO NOT NEED TO VISUALIZE
                    cv2.imwrite(save_folder + info[2] + '_' + reg_message['type_module'] + '_Result_' +
                                str(inc.get_incrementer(count, 5)) + '.jpeg', result)

                with open(save_folder + info[2] + '_' + reg_message['type_module'] + '_' +
                      str(inc.get_incrementer(count, 5)) + '.txt', 'w') as outfile:
                    outfile.write(message)
                count = count + 1
                if display:
                    key = cv2.waitKey(1) & 0xFF
                    # KEYBINDINGS FOR DISPLAY
                    cv2.imshow('frame', frame)
                    if key == 27:  # exit
                        break
