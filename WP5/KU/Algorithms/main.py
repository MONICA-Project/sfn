# sfn_service.py
"""A test application designed to mimic (badly) the VCA framework."""
import arrow
import json
import pickle
import cv2
import requests
import uuid
from pathlib import Path
import sys
import argparse
import socket
sys.path.append(str(Path(__file__).absolute().parents[3]))
from WP5.KU.definitions import KU_DIR
from WP5.KU.SharedResources.cam_video_streamer import CamVideoStreamer
from WP5.KU.SharedResources.frame_streamer import ImageSequenceStreamer
import WP5.KU.SharedResources.get_incrementer as inc
import WP5.KU.SharedResources.loader_tools as loader
from WP5.KU.Algorithms.crowd_density_local.get_crowd import GetCrowd
# from WP5.KU.Algorithms.flow_analysis.get_flow import GetFlow
# from WP5.KU.Algorithms.object_detection.get_people import GetPeople

__version__ = '0.3'
__author__ = 'Rob Dupre (KU)'


def dataset(index):
    # dataset_folder = 'C:/Users/Rob/Desktop/CROWD_DATASETS/'
    dataset_folder = '/ocean/datasets/'

    return {
        # [Address, Stream, Settings File]
        0: ['rtsp://root:pass@10.144.129.107/axis-media/media.amp', 'Live', 'CAMERA_KU'],
        # [Location, Start Frame, Settings File]
        1: [(KU_DIR + '/Algorithms/sample_sequence/'), 0, 'OXFORD'],
        2: [(dataset_folder + 'Mall_Dataset/frames/'), 0],
        3: [(dataset_folder + 'EWAP_Dataset/seq_eth/'), 0],
        4: [(dataset_folder + 'EWAP_Dataset/seq_hotel/'), 0],
        5: [(dataset_folder + 'YOUTUBE/TIMES_SQUARE/'), 0],
        6: [(dataset_folder + 'YOUTUBE/DELHI_CROWD/'), 0],
        7: [(dataset_folder + 'KU_Courtyard_Dataset/20130805_140532_52EB_00408CDCC71E/'), 50],
        8: [(dataset_folder + 'KU_LAB/Output_1/'), 15],
        9: [(dataset_folder + 'OXFORD_TOWNCENTRE/TownCentreXVID/'), 1, 2000],
        10: [(dataset_folder + 'MONICA/TO/KFF_2017/channel 2/2017-07-09 19-40-00~19-50-00/'), 0, 'KFF_CAM_2'],
        11: [(dataset_folder + 'MONICA/TO/KFF_2017/channel 4/2017-07-08 14-00-00~14-10-00/'), 0, 'KFF_CAM_4'],
        12: [(dataset_folder + 'MONICA/TO/KFF_2017/channel 8/2017-07-08 20-40-00~20-50-00/'), 0, 'KFF_CAM_8'],
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
        27: [(dataset_folder + '/MONICA/YCCC-LR/LEEDS_2018_AUG/LEEDS_1/'), 0, 'LEEDS_1'],
        28: [(dataset_folder + '/MONICA/YCCC-LR/LEEDS_2018_AUG/LEEDS_2/'), 0, 'LEEDS_2'],
        29: [(dataset_folder + '/MONICA/YCCC-LR/LEEDS_2018_AUG/LEEDS_3/'), 0, 'LEEDS_3'],
        30: [(dataset_folder + '/MONICA/YCCC-LR/LEEDS_2018_AUG/LEEDS_4/'), 0, 'LEEDS_4'],
    }.get(index, -1)  # -1 is default if id not found


parser = argparse.ArgumentParser(description='A test application designed to mimic (badly) the VCA framework.')
parser.add_argument('--sequence', default=None, type=str, help='Folder location of image sequence')
parser.add_argument('--rtsp', default=None, type=str, help='RTSP stream address')
parser.add_argument('--config', default='OXFORD', type=str, help='Config file Name in KUConfigTool folder to be used')
parser.add_argument('--display', default=True, type=bool, help='Bool to control displaying output')
# parser.add_argument('--algorithm', default='flow', type=str, help='Either flow or density')
parser.add_argument('--algorithm', default='density', type=str, help='Either flow or density')
_args = parser.parse_args()

if __name__ == '__main__':
    # CREATE AN INFO VAR TO BE DEFINE SOURCE OF INPUTS CONFIGS ETC
    if _args.rtsp is not None:
        info = [_args.rtsp, 'Live', _args.config, _args.algorithm]
        display = _args.display

    elif _args.sequence is not None:
        info = [_args.sequence, 0, _args.config, _args.algorithm]
        display = _args.display

    # IF BOTH sequence AND rtsp ARE None THEN WE USE CODED VALUES FOR TESTING
    else:
        info = dataset(0)
        # info = dataset(19)
        # info.append('flow')
        info.append('density')
        display = True

    # CREATE AN analyser OBJECT AND CREATE THE REGISTRATION MESSAGE
    if info[3] is 'flow':
        analyser = GetFlow(str(uuid.uuid5(uuid.NAMESPACE_DNS, socket.gethostname() + 'flow')))
    else:
        analyser = GetCrowd(str(uuid.uuid5(uuid.NAMESPACE_DNS, socket.gethostname() + 'crowd_density_local')))

    print(info)

    # LOAD THE SETTINGS AND PASS THEN WHEN PROCESSING A FRAME
    settings = loader.load_settings(KU_DIR + '/KUConfigTool/cam_configs/' + '/', info[2])

    if info[1] == 'Live':
        cam = CamVideoStreamer(info[0])
        cam.start()
        if cam.open():
            print("CAMERA CONNECTION IS ESTABLISHED.")
        else:
            print("FAILED TO CONNECT TO CAMERA.")
            exit(-1)
    else:
        cam = ImageSequenceStreamer(info[0], info[1], (1080, 768), loop_last=False, repeat=True)

    count = 0
    while cam.open():
        frame = cam.read()
        message = None
        result = None
        if analyser.type_module == 'flow':
            message, result = analyser.process_frame(frame, settings['camera_id'], settings['flow_rois'])
        elif analyser.type_module == 'crowd_density_local':
            message, result = analyser.process_frame(frame, settings['camera_id'], settings['crowd_mask'],
                                                     settings['image_2_ground_plane_matrix'],
                                                     settings['ground_plane_roi'],
                                                     settings['ground_plane_size'])

        # SEND A HTTP REQUEST OFF
        # sfn_url = 'http://127.0.0.1:5000/message'
        # try:
        #     res = requests.post(sfn_url, json=message)
        # except requests.exceptions.RequestException as e:
        #     print(e)
        # else:
        #     print('Obs Message Sent. Response: ' + str(res.status_code) + '. ' + res.text)

        # WRITE FILES FOR USE LATER
        save_folder = str(Path(__file__).absolute().parents[0]) + '/algorithm_output/'
        save_name = inc.get_incrementer(count, 7) + '_' + settings['camera_id'] + '_' + analyser.module_id
        if message:
            if result is not None:  # result is None, IF WE DO NOT NEED TO VISUALIZE
                cv2.imwrite(save_folder + save_name + '_result.jpeg', result)

            with open(save_folder + save_name + '.txt', 'w') as outfile:
                outfile.write(message)
            count = count + 1
            if display:
                key = cv2.waitKey(1) & 0xFF
                # KEYBINDINGS FOR DISPLAY
                cv2.imshow('frame', frame)
                if key == 27:  # exit
                    break
