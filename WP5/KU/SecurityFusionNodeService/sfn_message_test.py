# sfn_message_test.py
"""A script designed to test http request between the sfn_service and SCRAL"""
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
parser.add_argument('--scral_url', default='http://monappdwp3.monica-cloud.eu:8000/', type=str,
                    help='The URL and port the SFN is currently listening on')
parser.add_argument('--looping', default='False', type=str, help='Loop the message calls indefinitely.')
parser.add_argument('--threaded', default='False', type=str, help='sets up messages as separate threads')
parser.add_argument('--dataset_folder', default='/ocean/robdupre/PYTHON_SCRIPTS/MONICA_repo/WP5/KU/Algorithms/algorithm_output/',
                    type=str, help='Location of RiF JSON Files to send to SFN.')


def call_sfn(payload, n, module):
    # UPDATE URLS AND CHECK LINKSMART
    try:
        r = requests.put(url + 'message', json=json.dumps(payload))
    except requests.exceptions.RequestException as exception:
        print('[INFO] Thread {} MODULE {} Failed:{}.'.format(n, module, exception))
    else:
        print('[INFO] Thread {} MODULE {} OK.'.format(n, module))


_args = parser.parse_args()
if __name__ == '__main__':
    url = _args.sfn_url
    scral_url = _args.scral_url
    print('SFN URL:{}'.format(url))
    print('SCRAL URL:{}'.format(scral_url))

    num_cameras = 1
    algorithm_process_time = 1
    dataset_folder = _args.dataset_folder
    if _args.looping == 'True':
        looping = True
    else:
        looping = False
    if _args.threaded == 'True':
        threaded = True
    else:
        threaded = False

    looping = True
    sfn_urls = {'scral_url': scral_url}

    message_locations = [
        [os.path.join(dataset_folder), 'SAMPLE_fight_detection'],
        [os.path.join(dataset_folder), 'SAMPLE_crowd_density_local'],
        [os.path.join(dataset_folder), 'SAMPLE_flow'],
        [os.path.join(dataset_folder), 'SAMPLE_action_recognition'],
        [os.path.join(dataset_folder), 'SAMPLE_object_detection'],
    ]
    num_algorithms = len(message_locations)
    time_interval = (algorithm_process_time * num_cameras) / (num_algorithms * num_cameras)
    # time_interval = 5
    print('Messages will be sent every {} seconds'.format(time_interval))

    configs = [
        tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/cam_configs/'), 'TIVOLI_25'),
        tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/cam_configs/'), 'TIVOLI_27'),
        tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/cam_configs/'), 'TIVOLI_31'),
    ]

    # CHECK CONNECTION WITH SFN
    try:
        resp = requests.get(url)
    except requests.exceptions.RequestException as e:
        print('WOO THERE, Something went wrong, error:' + str(e))
    else:
        print(resp.text, resp.status_code)

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

    # SWITCH SFN TO DEBUGGING MODE
    # print('SWITCH SFN TO DEBUGGING MODE')
    # try:
    #     resp = requests.get(url + 'debug')
    # except requests.exceptions.RequestException as e:
    #     print('WOO THERE, Something went wrong, error:' + str(e))
    # else:
    #     print(resp.text, resp.status_code)

    # HELLO SCRAL VIA SFN
    print('CHECKING SFN CAN SEE SCRAL')
    try:
        resp = requests.get(url + 'scral')
    except requests.exceptions.RequestException as e:
        print('WOO THERE, Something went wrong, error:' + str(e))
    else:
        print(resp.text, resp.status_code)
        if resp.ok:
            counter = 0
            while True:
                cam = random.randint(0, len(configs)-1)

                for mess_type in message_locations:
                    mess = tools.load_json_txt(mess_type[0], mess_type[1])
                    cam_conf = configs[cam]
                    mess['camera_ids'][0] = cam_conf['camera_id']

                    # ADD IF STATEMENTS FOR EACH MODULE TYPE
                    if mess['type_module'] == 'fighting_detection':
                        mess['timestamp'] = str(arrow.utcnow())
                        mess['confidence'] = random.randint(0, 10) / 10
                    elif mess['type_module'] == 'crowd_density_local':
                        mess['timestamp1'] = str(arrow.utcnow())
                    elif mess['type_module'] == 'flow':
                        mess['timestamp'] = str(arrow.utcnow())
                    elif mess['type_module'] == 'action_recognition':
                        mess['timestamp'] = str(arrow.utcnow())
                    elif mess['type_module'] == 'object_detection':
                        mess['timestamp'] = str(arrow.utcnow())

                    if threaded:
                        t = Thread(target=call_sfn, args=(mess, counter, mess['type_module'],))
                        t.daemon = True
                        t.start()
                    else:
                        call_sfn(mess, 1, mess['type_module'])
                    counter = counter + 1
                time.sleep(time_interval)

                if not looping:
                    break
