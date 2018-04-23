import json
import requests
import os
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
from WP5.KU.definitions import KU_DIR
import WP5.KU.SecurityFusionNodeService.loader_tools as tools

url = 'http://127.0.0.2:3389/'

# HELLO WORLD
try:
    res = requests.get(url)
except requests.exceptions.RequestException as e:  # This is the correct syntax
    print(e)
else:
    print(res.text, res.status_code)

# # GET THE CONFIGS
# try:
#     resp = requests.get(url + 'configs')
# except requests.exceptions.RequestException as e:  # This is the correct syntax
#     print(e)
# else:
#     data = resp.json()
#     print(resp.text, resp.status_code)

# # GET A SPECIFIC CONFIG
# try:
#     r = requests.post(url + 'configs', json=json.dumps(0))
# except requests.exceptions.RequestException as e:  # This is the correct syntax
#     print(e)
# else:
#     data = r.json()
#     print(r.status_code, r.headers['content-type'], r.text)

# ADD A CONFIG
try:
    res = requests.post(url + 'add_config', data=json.dumps(tools.load_settings(
        os.path.join(KU_DIR, 'KUConfigTool/'), 'KFF_CAM_8')), headers={'content-Type': 'application/json'})
except requests.exceptions.RequestException as e:  # This is the correct syntax
    print(e)
else:
    print(res.text, res.status_code)

# # GET THE CONFIGS
# try:
#     res = requests.get(url + 'configs')
# except requests.exceptions.RequestException as e:  # This is the correct syntax
#     print(e)
# else:
#     data = res.json()
#     print(res.text, res.status_code)

# # DELETE A CONFIG
# try:
#     res = requests.delete(url + 'configs', json=json.dumps(0))
# except requests.exceptions.RequestException as e:  # This is the correct syntax
#     print(e)
# else:
#     print(res.text, res.status_code)

# GET THE MESSAGES
try:
    res = requests.get(url + 'message')
except requests.exceptions.RequestException as e:  # This is the correct syntax
    print(e)
else:
    data = res.json()
    print('Returned ' + str(len(data)) + ' message(s).', res.status_code)

# # GET A SPECIFIC MESSAGE
# try:
#     res = requests.post(url + 'message', json=json.dumps(0))
# except requests.exceptions.RequestException as e:  # This is the correct syntax
#     print(e)
# else:
#     data = res.json()
#     frame = tools.decode_image(data['frame_byte_array'], data['image_dims'], True)
#     print(res.status_code, res.headers['content-type'], res.text)

# ADD A MESSAGE
try:
    res = requests.put(url + 'add_message', json=json.dumps(tools.load_json_txt(
        os.path.join(KU_DIR, 'Algorithms/'), 'KFF_CAM_8_00000')))
except requests.exceptions.RequestException as e:  # This is the correct syntax
    print(e)
else:
    print(res.text, res.status_code)

# GET THE MESSAGES
try:
    res = requests.get(url + 'message')
except requests.exceptions.RequestException as e:  # This is the correct syntax
    print(e)
else:
    data = res.json()
    print(res.text, res.status_code)

# DELETE A MESSAGE
try:
    res = requests.delete(url + 'message', json=json.dumps(0))
except requests.exceptions.RequestException as e:  # This is the correct syntax
    print(e)
else:
    print(res.text, res.status_code)