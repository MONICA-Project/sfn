# sfn_http_request/py
"""A script designed to test http request between the sfn_service and the dummy Linksmart ls_service"""
import json
import requests
import os
import socket
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
from WP5.KU.definitions import KU_DIR
import WP5.KU.SecurityFusionNodeService.loader_tools as tools

__version__ = '0.1'
__author__ = 'RoViT (KU)'

print(str(socket.gethostname()))

url = 'http://0.0.0.0:5000/'
# url = 'http://MPCLSGESFN01.monica-cloud.eu:5000/'
scral_url = 'http://monappdwp3.monica-cloud.eu:8000/'
# scral_url = 'http://0.0.0.0:3389/'

sfn_urls = {'scral_url': scral_url,
            'crowd_density_url': scral_url + 'scral/sfn/crowd_monitoring',
            'flow_analysis_url': scral_url + 'scral/sfn/flow_analysis',
            'object_detection_url': scral_url + 'scral/sfn/object_detection',
            'fighting_detection_url': scral_url + 'scral/sfn/fight_detection',
            'camera_reg_url': scral_url + 'scral/sfn/camera',
            }

configs = [
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'KFF_CAM_2_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'KFF_CAM_4_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'KFF_CAM_8_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'RIF_CAM_1_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'RIF_CAM_2_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'RIF_CAM_3_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'RIF_CAM_4_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'Algorithms/registration_messages/'), '002_crowd_density_local_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'Algorithms/registration_messages/'), '001_flow_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'Algorithms/registration_messages/'), '6506F977-6868-4E78-B02D-8C516B8469F3_object_detection_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'Algorithms/registration_messages/'), '6789pwrl123dc_fighting_detection_reg', False),
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

# configs = [tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'KFF_CAM_2_reg', False)]
# SEND THE CONFIGS AS IF VCA WERE UPDATING THE SFN
print('CHECKING CONFIG UPDATE SFN')
try:
    resp = requests.post(url + 'configs', json=json.dumps(configs))
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)

# HELLO LINKSMART VIA SFN
print('CHECKING SFN CAN SEE SCRAL')
try:
    resp = requests.get(url + 'scral')
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)
    if resp.ok:

        # SEND MESSAGE TO SFN
        print('CHECKING SAMPLE MESSAGES ARE SENT')
        try:
            res = requests.put(url + 'message', json=json.dumps(
                tools.load_json_txt(os.path.join(KU_DIR, 'Algorithms/algorithm_output/'), 'RIF_CAM_1_crowd_density_local_00000')))
        except requests.exceptions.RequestException as e:
            print(str(e))
        else:
            print(res.text, res.status_code)

        # SEND MESSAGE TO SFN
        try:
            res = requests.put(url + 'message', json=json.dumps(
                tools.load_json_txt(os.path.join(KU_DIR, 'Algorithms/algorithm_output/'), 'RIF_CAM_1_crowd_density_local_00001')))
        except requests.exceptions.RequestException as e:
            print(str(e))
        else:
            print(res.text, res.status_code)

        # SEND MESSAGE TO SFN
        try:
            res = requests.put(url + 'message', json=json.dumps(
                tools.load_json_txt(os.path.join(KU_DIR, 'Algorithms/algorithm_output/'), 'RIF_CAM_1_crowd_density_local_00002')))
        except requests.exceptions.RequestException as e:
            print(str(e))
        else:
            print(res.text, res.status_code)
    else:
        print('SFN HAD ISSUES SEEING THE SCRAL')
