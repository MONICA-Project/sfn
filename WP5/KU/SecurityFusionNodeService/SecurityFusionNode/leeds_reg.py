# leeds_reg.py
"""A script designed to update the registration messages for a set location"""
import json
import requests
import os
import socket
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
from WP5.KU.definitions import KU_DIR
import WP5.KU.SharedResources.loader_tools as tools

__version__ = '0.1'
__author__ = 'RoViT (KU)'

print(str(socket.gethostname()))

url = 'http://0.0.0.0:5000/'
# url = 'http://MPCLSGESFN01.monica-cloud.eu:5000/'
scral_url = 'http://monappdwp3.monica-cloud.eu:8000/'
# scral_url = 'http://0.0.0.0:3389/'

sfn_urls = {'scral_url': scral_url,
            'crowd_density_url': scral_url + 'sfn/crowd_monitoring',
            'flow_analysis_url': scral_url + 'sfn/flow_analysis',
            'object_detection_url': scral_url + 'sfn/object_detection',
            'fighting_detection_url': scral_url + 'sfn/fight_detection',
            'action_recognition_url': scral_url + 'sfn/action_recognition',
            'camera_reg_url': scral_url + 'sfn/camera',
            }

configs = [
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/cam_configs/'), 'LEEDS_1'),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/cam_configs/'), 'LEEDS_2'),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/cam_configs/'), 'LEEDS_3'),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/cam_configs/'), 'LEEDS_4'),
    tools.load_settings(os.path.join(KU_DIR, 'Algorithms/crowd_density_local/'), '0ce70402-6147-5507-a135-42f6c26d2213_crowd_density_local_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'Algorithms/flow_analysis/'), '06144a3d-bb41-5c87-be0d-9ed7be234101_flow_reg', False),
    # tools.load_settings(os.path.join(KU_DIR, 'Algorithms/registration_messages/'), '6506F977-6868-4E78-B02D-8C516B8469F3_object_detection_reg', False),
    # tools.load_settings(os.path.join(KU_DIR, 'Algorithms/registration_messages/'), '6789pwrl123dc_fighting_detection_reg', False),
    # tools.load_settings(os.path.join(KU_DIR, 'Algorithms/registration_messages/'), '1234sdfv234jk_action_recognition_reg', False),
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
