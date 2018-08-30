import requests
import json
import arrow
import WP5.KU.SharedResources.loader_tools as tools
from WP5.KU.definitions import KU_DIR
import os

# scral_url = "http://monappdwp3.monica-cloud.eu:8001/"
sfn_url = "http://192.168.99.211:5000/"
# sfn_url = "http://0.0.0.0:5000/"
# scral_url = "https://portal.monica-cloud.eu/scral/"
# scral_url = "http://monappdwp3.monica-cloud.eu:8000/"
# wearables_url = "http://monappdwp3.monica-cloud.eu:8001/scral/wearables"
# wearables_url = "https://portal.monica-cloud.eu/scral/scral/wearables"
# wearables_url = "http://monappdwp3.monica-cloud.eu:8000/scral/sfn/camera"

# CHECK SCRAL IS THERE...
print('REQUEST: HELLO SFN')
try:
    resp = requests.get(sfn_url)
except requests.exceptions.RequestException as e:
    print(e)
else:
    # SHOULD SAY Hi, SCRAL is ready for SFN intergration
    print(resp.text, resp.status_code)

# NEXT REGISTER THE MODULE/DEVICE THAT IS WILL BE GENERATING MESSAGES.
# message WILL HOLD THE REGISTRATION DATA FOR THE DEVICE
message = [{"module_id": "1234sdfv234jk",
           "type_module": "action_recognition",
           "timestamp": str(arrow.utcnow()),
           "unitOfMeasurements": "meters",
           "observationType": "propietary",
           "state": "active",
           }]

# SEND THE CONFIGS
print('CHECKING CONFIG UPDATE SFN')
try:
    resp = requests.post(sfn_url + 'configs', json=json.dumps(message))
except requests.exceptions.RequestException as e:
    print('WOO THERE, Something went wrong, error:' + str(e))
else:
    print(resp.text, resp.status_code)

# ONCE REGISTERED THEN YOU CAN SEND MESSAGES
# message SHOULD NOW HOLD THE OBSERVATION MESSAGE
message = {"module_id": "1234sdfv234jk",
           "type_module": "action_recognition",
           "device": "wearable",
           "sensor": "tag",
           "type": "uwb",
           "tag_id": "0x0644",
           "timestamp": str(arrow.utcnow()),
           "action": "Lying"}
message = json.dumps(message)
try:
    resp = requests.put(sfn_url + 'message', data=message, headers={'content-Type': 'application/json'})
except requests.exceptions.RequestException as e:
    print(e)
else:
    print('RESPONSE: ' + resp.text + str(resp.status_code))