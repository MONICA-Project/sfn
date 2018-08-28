#tivoli_mes.py
"""Test script to send messages from non-running modules to SFN"""
import json
import requests
from threading import Thread
import time
import argparse
import arrow
import os
import socket
from pathlib import Path
import random
import sys
sys.path.append(str(Path(__file__).absolute().parents[3]))
from WP5.KU.definitions import KU_DIR
import WP5.KU.SharedResources.loader_tools as tools

__version__ = '0.1'
__author__ = 'RoViT (KU)'

print(str(socket.gethostname()))

parser = argparse.ArgumentParser(description='"A simple load testing script to fire messages off to the SFN')
# parser.add_argument('--sfn_url', default='http://MPCLSGESFN01.monica-cloud.eu:5000/', type=str,
parser.add_argument('--sfn_url', default='http://0.0.0.0:5000/', type=str,
                    help='The URL and port the SFN is currently listening on')
parser.add_argument('--scral_url', default='http://monappdwp3.monica-cloud.eu:8000/', type=str,
# parser.add_argument('--scral_url', default='http://0.0.0.0:3389/', type=str,
                    help='The URL and port the SCRAL is currently listening on.')
parser.add_argument('--looping', default=True, type=bool, help='Loop the message calls indefinitely.')
parser.add_argument('--dataset_folder', default='/home/monicaadmin/monica/WP5/KU/Algorithms/algorithm_output/', type=str,
                    help='Location of RiF JSON Files to send to SFN.')

_args = parser.parse_args()
if __name__ == '__main__':
    url = _args.sfn_url
    scral_url = _args.scral_url

    print('SFN URL:{}. SCRAL URL:{}'.format(url, scral_url))
    sfn_urls = {'scral_url': scral_url,
                'crowd_density_url': scral_url + 'sfn/crowd_monitoring',
                'flow_analysis_url': scral_url + 'sfn/flow_analysis',
                'object_detection_url': scral_url + 'sfn/object_detection',
                'fighting_detection_url': scral_url + 'sfn/fight_detection',
                'action_recognition_url': scral_url + 'sfn/action_recognition',
                'camera_reg_url': scral_url + 'sfn/camera',
                }

    # sleep_counter = 0.9
    num_algorithms = 2
    num_cameras = 4
    algorithm_process_time = 1
    time_interval = (algorithm_process_time * num_cameras) / (num_algorithms * num_cameras)
    time_interval = 5
    print('Messages will be sent every {} seconds'.format(time_interval))
    looping = _args.looping
    dataset_folder = _args.dataset_folder

message_locations = [
    [os.path.join(dataset_folder), 'TIVOLI_25_fight_detection'],
    [os.path.join(dataset_folder), 'TIVOLI_26_fight_detection'],
    [os.path.join(dataset_folder), 'TIVOLI_27_fight_detection'],
    [os.path.join(dataset_folder), 'TIVOLI_28_fight_detection'],
    [os.path.join(dataset_folder), 'TIVOLI_29_fight_detection'],
    # [os.path.join(dataset_folder), '0x0644_action_recognition_00000'],
]


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

        while True:
            cam = random.randint(0, 4)
            cam_fd_mess = tools.load_json_txt(message_locations[cam][0], message_locations[cam][1])
            cam_fd_mess['timestamp'] = str(arrow.utcnow())
            call_sfn(cam_fd_mess, 1, 'FD')

            # cam_X_ar_mess = tools.load_json_txt(message_locations[-1][0], message_locations[-1][1])
            # cam_X_ar_mess['timestamp'] = str(arrow.utcnow())

            # call_sfn(cam_X_ar_mess, 2, 'AR')
            time.sleep(time_interval)

            if not looping:
                break
