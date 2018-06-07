# sfn_http_request/py
"""A script designed to test http request between the sfn_service and the dummy Linksmart ls_service"""
import json
import requests
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

# url = 'http://dupre.hopto.org:5000/'
url = 'http://0.0.0.0:5000/'

sfn_urls = {'dummy_linksmart_url': 'http://0.0.0.0:3389/',
            # 'crowd_density_url': 'https://portal.monica-cloud.eu/scral/sfn/crowdmonitoring',
            'crowd_density_url': 'http://0.0.0.0:3389/crowd_density',
            'object_detection_url': 'http://0.0.0.0:3389/object_detection',
            'fighting_detection_url': 'http://0.0.0.0:3389/fighting_detection',
            }

configs = [
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'KFF_CAM_2_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'KFF_CAM_4_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'KFF_CAM_8_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'RIF_CAM_1_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'RIF_CAM_2_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'RIF_CAM_3_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'RIF_CAM_4_reg', False),
]

# HELLO WORLD
try:
    resp = requests.get(url)
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)

# UPDATE URLS
try:
    resp = requests.post(url + 'urls', json=json.dumps(sfn_urls))
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)

# HELLO LINKSMART VIA SFN
try:
    resp = requests.get(url + 'linksmart')
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)


# REGISTER SFN ON LINKSMART
try:
    resp = requests.get(url + 'register')
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)

# REGISTER THE SAME SFN ON LINKSMART
try:
    resp = requests.get(url + 'register')
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)

# SEND THE CONFIGS AS IF VCA WERE UPDATING THE SFN
try:
    resp = requests.post(url + 'configs', json=json.dumps(configs))
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)

# SEND MESSAGE TO SFN
try:
    res = requests.put(url + 'message', json=json.dumps(
        tools.load_json_txt(os.path.join(KU_DIR, 'Algorithms/algorithm_output/'), 'RIF_CAM_1_00000')))
except requests.exceptions.RequestException as e:
    print(str(e))
else:
    print(res.text, res.status_code)

# SEND MESSAGE TO SFN
try:
    res = requests.put(url + 'message', json=json.dumps(
        tools.load_json_txt(os.path.join(KU_DIR, 'Algorithms/algorithm_output/'), 'RIF_CAM_1_00000')))
except requests.exceptions.RequestException as e:
    print(str(e))
else:
    print(res.text, res.status_code)

# SEND MESSAGE TO SFN
try:
    res = requests.put(url + 'message', json=json.dumps(
        tools.load_json_txt(os.path.join(KU_DIR, 'Algorithms/algorithm_output/'), 'RIF_CAM_2_00000')))
except requests.exceptions.RequestException as e:
    print(str(e))
else:
    print(res.text, res.status_code)
