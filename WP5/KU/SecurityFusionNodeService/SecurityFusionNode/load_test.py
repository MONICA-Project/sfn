import json
import requests
import os
import socket
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
from WP5.KU.definitions import KU_DIR
import WP5.KU.SecurityFusionNodeService.loader_tools as tools

print(str(socket.gethostname()))

# url = 'http://dupre.hopto.org:5000/'
url = 'http://127.0.0.1:5000/'
responses = []


# UPDATE LINKSMART URL
try:
    resp = requests.post(url + 'linksmart', json='http://127.0.0.2:3389/')
    # resp = requests.post(url + 'linksmart', json='dupre.hopto.org:3389/')
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
    if resp.ok:
        # GET THE CONFIGS FROM LINKSMART VIA SFN
        resp = requests.get(url + 'linksmart/get_configs')

# HELLO WORLD
try:
    resp = requests.get(url)
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)
    if resp.ok:
        # FIND ALL TXT FILES
        for f in sorted(os.listdir(os.path.join(KU_DIR, 'Algorithms/'))):
            ext = os.path.splitext(f)[1]
            if f[:3] == 'KFF' and ext.lower().endswith('.txt'):
                responses.append(requests.post(url + 'message', json=json.dumps(tools.load_json_txt(os.path.join(
                    KU_DIR, 'Algorithms/'), f[:-4]))))
