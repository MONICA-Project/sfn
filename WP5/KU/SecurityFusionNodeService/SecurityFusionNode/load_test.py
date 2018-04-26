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
sfn_urls = {'dummy_linksmart_url': 'http://127.0.0.2:3389/',
            # 'crowd_density_url': 'https://portal.monica-cloud.eu/scral/sfn/crowdmonitoring',
            'crowd_density_url': 'http://127.0.0.2:3389/crowd_density',
            }

responses = []


# CHECK CONNECTION WITH SFN AND UPDATE URLS CHECK LINKSMART CONNECTION
try:
    resp = requests.get(url)
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)
    if resp.ok:
        # UPDATE URLS AND CHECK LINKSMART
        try:
            resp = requests.post(url + 'urls', json=json.dumps(sfn_urls))
        except requests.exceptions.RequestException as e:
            print('WOO THERE, Something went wrong, error:' + str(e))
        else:
            print(resp.text, resp.status_code)
        try:
            resp = requests.get(url + 'linksmart')
        except requests.exceptions.RequestException as e:
            print('WOO THERE, Something went wrong, error:' + str(e))
        else:
            if resp.ok:
                # GET THE CONFIGS FROM LINKSMART VIA SFN
                resp = requests.get(url + 'linksmart/get_configs')

# LOAD TEST WITH LOTS OF MESSAGES
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
