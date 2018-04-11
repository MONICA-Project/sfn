import json
import requests
import loader_tools as tools

url = 'http://127.0.0.2:5000/'
linksmart_url = 'http://127.0.0.1:5000/'
message = tools.load_json_txt('/ocean/robdupre/PYTHON_SCRIPTS/MONICA/', 'KFF_CAM_8_00006')

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
    res = requests.post(url + 'message', json=json.dumps(tools.load_json_txt('/ocean/robdupre/PYTHON_SCRIPTS/MONICA/',
                                                                             'KFF_CAM_8_00008')))
except requests.exceptions.RequestException as e:  # This is the correct syntax
    print(e)
else:
    print(res.status_code, res.headers['content-type'], res.text)
#
# try:
#     req = requests.delete(url)
# except requests.exceptions.RequestException as e:
#     print('WOO THERE, Something went wrong, error:' + e)
# else:
#     print(req.text, req.status_code)