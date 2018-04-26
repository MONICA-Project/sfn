import json
import requests
import os
import socket
from pathlib import Path
import sys
import time
sys.path.append(str(Path(__file__).absolute().parents[4]))
from WP5.KU.definitions import KU_DIR
import WP5.KU.SecurityFusionNodeService.loader_tools as tools

print(str(socket.gethostname()))

# url = 'http://dupre.hopto.org:5000/'
url = 'http://127.0.0.1:5000/'

# HELLO WORLD
try:
    resp = requests.get(url)
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)

# SEND MESSAGE TO SFN
job_key1 = []
try:
    res = requests.post(url + 'message', json=json.dumps({'time': 20}))
except requests.exceptions.RequestException as e:  # This is the correct syntax
    print(str(e))
else:
    job_key1 = res.text
    print(res.text, res.status_code)

# CHECK QUEUE STATUS
try:
    res = requests.get(url + 'queue')
except requests.exceptions.RequestException as e:  # This is the correct syntax
    print(str(e))
else:
    print(res.text, res.status_code)

# CHECK QUEUE STATUS
try:
    res = requests.get(url + 'queue')
except requests.exceptions.RequestException as e:  # This is the correct syntax
    print(str(e))
else:
    print(res.text, res.status_code)

# CHECK QUEUE STATUS
try:
    res = requests.get(url + 'queue')
except requests.exceptions.RequestException as e:  # This is the correct syntax
    print(str(e))
else:
    print(res.text, res.status_code)

time.sleep(10)

# CHECK STATUS OF JOB
try:
    res = requests.post(url + 'result', json=json.dumps({'job_key': job_key1}))
except requests.exceptions.RequestException as e:
    print(str(e))
else:
    print('Job {}: {}. {}'.format(job_key1, res.text, res.status_code))

