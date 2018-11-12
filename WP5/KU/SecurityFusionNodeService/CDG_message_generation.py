#leeds_mes.py
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

__version__ = '0.2'
__author__ = 'RoViT (KU)'

print(str(socket.gethostname()))

parser = argparse.ArgumentParser(description='"A simple load testing script to fire messages off to the SFN')
# parser.add_argument('--sfn_url', default='http://MPCLSGESFN01.monica-cloud.eu:5000/', type=str,
parser.add_argument('--sfn_url', default='http://0.0.0.0:5000/', type=str,
                    help='The URL and port the SFN is currently listening on')
parser.add_argument('--looping', default=True, type=bool, help='Loop the message calls indefinitely.')
parser.add_argument('--dataset_folder', default='/ocean/robdupre/PYTHON_SCRIPTS/MONICA_repo/WP5/KU/Algorithms/algorithm_output/', type=str,
                    help='Location of RiF JSON Files to send to SFN.')

_args = parser.parse_args()
if __name__ == '__main__':
    url = 'http://0.0.0.0:5000/'

    print('SFN URL:{}'.format(url))

    scral_url = 'http://BLABLA.monica-cloud.eu:8000/'

    sfn_urls = {'scral_url': scral_url,
                'crowd_density_url': scral_url + 'sfn/camera',
                'crowd_density_global_url': scral_url + 'sfn/crowd_density_global',
                'flow_analysis_url': scral_url + 'sfn/camera',
                'object_detection_url': scral_url + 'sfn/camera',
                'fighting_detection_url': scral_url + 'sfn/camera',
                'action_recognition_url': scral_url + 'sfn/camera',
                'camera_reg_url': scral_url + 'sfn/camera',
                }

    # sleep_counter = 0.9
    dataset_folder = '/ocean/datasets/MONICA/YCCC-LR/LEEDS_2018_AUG/ORIGINAL_IMAGES/'

    message_locations = [
        [os.path.join(dataset_folder), '0000014_LEEDS_2_435ae19f-0eab-5561-b11a-9ead485180d6_crowd_density_local'],
        [os.path.join(dataset_folder), '0000010_LEEDS_4_435ae19f-0eab-5561-b11a-9ead485180d6_crowd_density_local'],
        [os.path.join(dataset_folder), '0000018_LEEDS_3_435ae19f-0eab-5561-b11a-9ead485180d6_crowd_density_local'],
        [os.path.join(dataset_folder), '0000015_LEEDS_1_435ae19f-0eab-5561-b11a-9ead485180d6_crowd_density_local'],
    ]

    configs = [
        tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/cam_configs/'), 'LEEDS_1'),
        tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/cam_configs/'), 'LEEDS_2'),
        tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/cam_configs/'), 'LEEDS_3'),
        tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/cam_configs/'), 'LEEDS_4'),
    ]


def call_sfn(payload, n, module):
    # UPDATE URLS AND CHECK LINKSMART
    try:
        r = requests.put(url + 'message', json=json.dumps(payload))
    except requests.exceptions.RequestException as exception:
        print('[INFO] Thread {} MODULE {} Failed:{}.'.format(n, module, exception))
    else:
        print('[INFO] Thread {} MODULE {} OK.'.format(n, module))


# UPDATE URLS
print('CHECKING URL UPDATE SFN')
try:
    resp = requests.post(url + 'urls', json=json.dumps(sfn_urls))
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)

# SEND THE CONFIGS AS IF VCA WERE UPDATING THE SFN
print('CHECKING CONFIG UPDATE SFN')
try:
    resp = requests.post(url + 'configs', json=json.dumps(configs))
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)

# CHECK CONNECTION WITH SFN
try:
    resp = requests.get(url)
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)
    if resp.ok:

        for i in range(10):

            for mess_type in message_locations:
                mess = tools.load_json_txt(mess_type[0], mess_type[1])
                call_sfn(mess, 1, mess['type_module'])
            time.sleep(10)