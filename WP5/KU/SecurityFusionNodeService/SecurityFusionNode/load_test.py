# load_test.py
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

__version__ = '0.2'
__author__ = 'RoViT (KU)'

print(str(socket.gethostname()))

url = 'http://127.0.0.1:5000/'
num_requests = 500
sleep_counter = 0.01


def call_sfn(payload, n):
    # UPDATE URLS AND CHECK LINKSMART
    try:
        r = requests.put(url + 'message', json=json.dumps(payload))
    except requests.exceptions.RequestException as exception:
        print('[INFO] Thread {} Failed:{}.'.format(n, exception))
    else:
        print('[INFO] Thread {} OK.'.format(n))


dummy_payload = tools.load_json_txt(os.path.join(KU_DIR, 'Algorithms/algorithm_output/'), 'KFF_CAM_2_00008')
# CHECK CONNECTION WITH SFN
try:
    resp = requests.get(url)
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)
    if resp.ok:
        # LOAD TEST WITH LOTS OF MESSAGES
        for i in range(0, num_requests):
            t = Thread(target=call_sfn, args=(dummy_payload, i,))
            t.daemon = True
            t.start()
            time.sleep(sleep_counter)

