import json
import requests
import os
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
from WP5.KU.definitions import KU_DIR
import WP5.KU.SharedResources.loader_tools as tools

url = 'http://0.0.0.0:3389/'

# HELLO WORLD
try:
    res = requests.get(url)
except requests.exceptions.RequestException as e:  # This is the correct syntax
    print(e)
else:
    print(res.text, res.status_code)


# TEST REPLICATED SCRAL FUNCTIONALITY
# REGISTER A MODULE
try:
    res = requests.post(url + 'crowd_density', data=json.dumps(tools.load_settings(
        os.path.join(KU_DIR, 'KUConfigTool/'), 'KFF_CAM_8')), headers={'content-Type': 'application/json'})
except requests.exceptions.RequestException as e:  # This is the correct syntax
    print(e)
else:
    print(res.text, res.status_code)

# ADD AN OBSERVATION
try:
    res = requests.put(url + 'crowd_density', data=json.dumps(tools.load_json_txt(
        os.path.join(KU_DIR, 'Algorithms/algorithm_output/'), 'KFF_CAM_8_00000')), headers={'content-Type': 'application/json'})
except requests.exceptions.RequestException as e:  # This is the correct syntax
    print(e)
else:
    print(res.text, res.status_code)

# GET THE CONFIGS
try:
    resp = requests.get(url + 'configs')
except requests.exceptions.RequestException as e:
    print(e)
else:
    data = resp.json()
    print(resp.text, resp.status_code)

# DELETE A CONFIG
try:
    res = requests.delete(url + 'configs', json=json.dumps(0))
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
    print('Returned ' + str(len(data)) + ' message(s).', res.status_code)
