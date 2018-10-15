# leeds_reg.py
"""A script designed to update the registration messages for a set location"""
import json
import requests
import os
import socket
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[3]))
from WP5.KU.definitions import KU_DIR
import WP5.KU.SharedResources.loader_tools as tools

__version__ = '0.1'
__author__ = 'RoViT (KU)'

print(str(socket.gethostname()))
print(KU_DIR)

url = 'http://0.0.0.0:5000/'
# url = 'http://MPCLSGESFN01.monica-cloud.eu:5000/'
scral_url = 'http://monappdwp3.monica-cloud.eu:8000/'
# scral_url = 'http://0.0.0.0:3389/'

sfn_urls = {'scral_url': scral_url,
            'crowd_density_url': scral_url + 'sfn/camera',
            'crowd_density_global_url': scral_url + 'sfn/crowd_density_global',
            'flow_analysis_url': scral_url + 'sfn/camera',
            'object_detection_url': scral_url + 'sfn/camera',
            'fighting_detection_url': scral_url + 'sfn/camera',
            'action_recognition_url': scral_url + 'sfn/camera',
            'camera_reg_url': scral_url + 'sfn/camera',
            }

configs = [
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/cam_configs/'), 'LEEDS_1'),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/cam_configs/'), 'LEEDS_2'),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/cam_configs/'), 'LEEDS_3'),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/cam_configs/'), 'LEEDS_4'),
]

# HELLO WORLD
print('CHECKING CONNECTION TO THE SFN')
try:
    resp = requests.get(url)
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)

# RELOAD SETTINGS
print('CHECKING SETTINGS RELOAD ON SFN')
try:
    resp = requests.get(url + 'settings')
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