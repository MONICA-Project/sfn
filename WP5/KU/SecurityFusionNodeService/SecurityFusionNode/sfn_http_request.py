import json
import requests
import os
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
from WP5.KU.definitions import KU_DIR
import WP5.KU.SecurityFusionNodeService.loader_tools as tools

url = 'dupre.hopto.org:1000/'
message = tools.load_json_txt(os.path.join(KU_DIR, 'Algorithms/'), 'KFF_CAM_8_00006')

# HELLO WORLD
try:
    resp = requests.get(url)
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + e)
else:
    print(resp.text, resp.status_code)

# HELLO LINKSMART VIA SFN
try:
    resp = requests.get(url + 'linksmart')
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + e)
else:
    print(resp.text, resp.status_code)

# REGISTER SFN ON LINKSMART
try:
    resp = requests.get(url + 'register')
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + e)
else:
    print(resp.text, resp.status_code)

# REGISTER THE SAME SFN ON LINKSMART
try:
    resp = requests.get(url + 'register')
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + e)
else:
    print(resp.text, resp.status_code)

# GET THE CONFIGS FROM LINKSMART VIA SFN
try:
    resp = requests.get(url + 'linksmart/get_configs')
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + e)
else:
    print(resp.text, resp.status_code)

# SEND MESSAGE TO SFN
try:
    res = requests.post(url + 'message', json=json.dumps(tools.load_json_txt(os.path.join(KU_DIR, 'Algorithms/'),
                                                                             'KFF_CAM_8_00008')))
except requests.exceptions.RequestException as e:  # This is the correct syntax
    print(e)
else:
    print(res.text, res.status_code)
#
# try:
#     req = requests.delete(url)
# except requests.exceptions.RequestException as e:
#     print('WOO THERE, Something went wrong, error:' + e)
# else:
#     print(req.text, req.status_code)