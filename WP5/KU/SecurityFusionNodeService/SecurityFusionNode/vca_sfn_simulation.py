# vca_sfn_simulation.py
"""A simple load testing script to fire messages off to the SFN"""
import json
import requests
from threading import Thread
import time
import os
import socket
from pathlib import Path
import sys
from WP5.KU.definitions import KU_DIR
import WP5.KU.SecurityFusionNodeService.loader_tools as tools
sys.path.append(str(Path(__file__).absolute().parents[4]))

__version__ = '0.1'
__author__ = 'RoViT (KU)'

print(str(socket.gethostname()))

url = 'http://0.0.0.0:5000/'
sleep_counter = 0.8


dataset_folder = '/ocean/datasets'
message_locations = [
    os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_1_crowd_density_JSON/'),
    os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/20180505_233000_camera_1_crowd_density_JSON/'),
    os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_2_crowd_density_JSON/'),
    os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/20180505_233000_camera_2_crowd_density_JSON/'),
    os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_3_crowd_density_JSON/'),
    os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/20180505_233000_camera_3_crowd_density_JSON/'),
    os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_4_crowd_density_JSON/'),
    os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/20180505_233000_camera_4_crowd_density_JSON/'),
    os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_1_flow_analysis_JSON/'),
    os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/20180505_233000_camera_1_flow_analysis_JSON/'),
    os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_2_flow_analysis_JSON/'),
    os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/20180505_233000_camera_2_flow_analysis_JSON/'),
    os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_3_flow_analysis_JSON/'),
    os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/20180505_233000_camera_3_flow_analysis_JSON/'),
    os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_4_flow_analysis_JSON/'),
    os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/20180505_233000_camera_4_flow_analysis_JSON/'),
    [os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/'), 'RIF_CAM_3_fight_detection_00000'],
    [os.path.join(dataset_folder, 'MONICA/BONN/Rein in Flammen 2018/'), 'RIF_CAM_4_object_detection_00000'],
]


def get_file_names(locations):
    file_names = []
    for f in sorted(os.listdir(locations[0])):
        file_names.append([locations[0], os.path.splitext(f)[0]])
    for f in sorted(os.listdir(locations[1])):
        file_names.append([locations[1], os.path.splitext(f)[0]])
    return file_names


cam_1_crowd_density = get_file_names(message_locations[0:2])
cam_2_crowd_density = get_file_names(message_locations[2:4])
cam_3_crowd_density = get_file_names(message_locations[4:6])
cam_4_crowd_density = get_file_names(message_locations[6:8])
cam_1_flow_analysis = get_file_names(message_locations[8:10])
cam_2_flow_analysis = get_file_names(message_locations[10:12])
cam_3_flow_analysis = get_file_names(message_locations[12:14])
cam_4_flow_analysis = get_file_names(message_locations[14:16])


def call_sfn(payload, n, module):
    # UPDATE URLS AND CHECK LINKSMART
    try:
        r = requests.put(url + 'message', json=json.dumps(payload))
    except requests.exceptions.RequestException as exception:
        print('[INFO] Thread {} MODULE {} Failed:{}.'.format(n, module, exception))
    else:
        print('[INFO] Thread {} MODULE {} OK.'.format(n, module))


# CHECK CONNECTION WITH SFN
try:
    resp = requests.get(url)
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)
    if resp.ok:

        # LOAD TEST WITH LOTS OF MESSAGES
        for i in range(0, len(cam_1_crowd_density)):
            cam_1_cd_mess = tools.load_json_txt(cam_1_crowd_density[i][0], cam_1_crowd_density[i][1])
            cam_2_cd_mess = tools.load_json_txt(cam_2_crowd_density[i][0], cam_2_crowd_density[i][1])
            cam_3_cd_mess = tools.load_json_txt(cam_3_crowd_density[i][0], cam_3_crowd_density[i][1])
            cam_4_cd_mess = tools.load_json_txt(cam_4_crowd_density[i][0], cam_4_crowd_density[i][1])
            cam_1_fa_mess = tools.load_json_txt(cam_1_flow_analysis[i][0], cam_1_flow_analysis[i][1])
            cam_2_fa_mess = tools.load_json_txt(cam_2_flow_analysis[i][0], cam_2_flow_analysis[i][1])
            cam_3_fa_mess = tools.load_json_txt(cam_3_flow_analysis[i][0], cam_3_flow_analysis[i][1])
            cam_4_fa_mess = tools.load_json_txt(cam_4_flow_analysis[i][0], cam_4_flow_analysis[i][1])
            cam_1_od_mess = tools.load_json_txt(message_locations[-1][0], message_locations[-1][1])
            cam_2_od_mess = tools.load_json_txt(message_locations[-1][0], message_locations[-1][1])
            cam_3_od_mess = tools.load_json_txt(message_locations[-1][0], message_locations[-1][1])
            cam_4_od_mess = tools.load_json_txt(message_locations[-1][0], message_locations[-1][1])
            # call_sfn(cam_1_cd_mess, i, 'CD')
            # call_sfn(cam_2_cd_mess, i, 'CD')
            # call_sfn(cam_3_cd_mess, i, 'CD')
            # call_sfn(cam_4_cd_mess, i, 'CD')
            # call_sfn(cam_1_fa_mess, i, 'FA')
            # call_sfn(cam_2_fa_mess, i, 'FA')
            # call_sfn(cam_3_fa_mess, i, 'FA')
            # call_sfn(cam_4_fa_mess, i, 'FA')
            # call_sfn(cam_1_od_mess, i, 'OD')
            # call_sfn(cam_2_od_mess, i, 'OD')
            # call_sfn(cam_3_od_mess, i, 'OD')
            # call_sfn(cam_4_od_mess, i, 'OD')

            if i % 60 == 0:
                cam_3_fd_mess = tools.load_json_txt(message_locations[-2][0], message_locations[-2][1])
                # call_sfn(cam_3_fd_mess, i, 'FD')
                t = Thread(target=call_sfn, args=(cam_3_fd_mess, i, 'FD',))
                t.daemon = True
                t.start()

            t = Thread(target=call_sfn, args=(cam_1_cd_mess, i, 'CD',))
            t.daemon = True
            t.start()
            t = Thread(target=call_sfn, args=(cam_2_cd_mess, i, 'CD',))
            t.daemon = True
            t.start()
            t = Thread(target=call_sfn, args=(cam_3_cd_mess, i, 'CD',))
            t.daemon = True
            t.start()
            t = Thread(target=call_sfn, args=(cam_4_cd_mess, i, 'CD',))
            t.daemon = True
            t.start()
            t = Thread(target=call_sfn, args=(cam_1_fa_mess, i, 'FA',))
            t.daemon = True
            t.start()
            t = Thread(target=call_sfn, args=(cam_2_fa_mess, i, 'FA',))
            t.daemon = True
            t.start()
            t = Thread(target=call_sfn, args=(cam_3_fa_mess, i, 'FA',))
            t.daemon = True
            t.start()
            t = Thread(target=call_sfn, args=(cam_4_fa_mess, i, 'FA',))
            t.daemon = True
            t.start()
            t = Thread(target=call_sfn, args=(cam_1_od_mess, i, 'OD',))
            t.daemon = True
            t.start()
            t = Thread(target=call_sfn, args=(cam_2_od_mess, i, 'OD',))
            t.daemon = True
            t.start()
            t = Thread(target=call_sfn, args=(cam_3_od_mess, i, 'OD',))
            t.daemon = True
            t.start()
            t = Thread(target=call_sfn, args=(cam_4_od_mess, i, 'OD',))
            t.daemon = True
            t.start()
            time.sleep(sleep_counter)





