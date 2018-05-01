# sfn_service.py
"""Implementation of a RESTful webservice to handle messages produced from the VCA framework and forward them on to
linksmart"""
import argparse
import requests
import json
import datetime
from flask import Flask, request
from pathlib import Path
import sys
import WP5.KU.SecurityFusionNodeService.loader_tools as tools
from WP5.KU.SecurityFusionNodeService.SecurityFusionNode.security_fusion_node import SecurityFusionNode
import WP5.KU.SecurityFusionNodeService.SecurityFusionNode.message_processing as mp
sys.path.append(str(Path(__file__).absolute().parents[4]))

__version__ = '0.2'
__author__ = 'RoViT (KU)'

app = Flask(__name__)
sfn_module = SecurityFusionNode('001')
urls = {'dummy_linksmart_url': 'http://127.0.0.2:3389/',
        # 'crowd_density_url': 'https://portal.monica-cloud.eu/scral/sfn/crowdmonitoring',
        'crowd_density_url': 'http://127.0.0.2:3389/crowd_density',
        'flow_analysis_url': 'http://127.0.0.2:3389/flow_analysis',
        }

headers = {'content-Type': 'application/json'}


@app.route("/")
def hello_world():
    print('REQUEST: HELLO WORLD')
    return "SECURITY FUSION NODE"


@app.route("/urls", methods=['POST'])
def update_urls():
    print('REQUEST: UPDATE URLS')
    if request.is_json:
        url_updates = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(url_updates) == str:
            url_updates = json.loads(url_updates)

        global urls
        for url in urls:
            if url in url_updates:
                urls[url] = url_updates[url]
                print('Updating Key ({}) to: {}.'.format(url, url_updates[url]))
            else:
                print('Key ({}) not found.'.format(url))
        return 'SFN urls updated', 201
    else:
        return 'No JSON.', 415


@app.route("/register")
def register_sfn():
    print('REQUEST: SEND SFN REGISTRATION')
    data = sfn_module.create_reg_message(datetime.datetime.utcnow().isoformat())
    try:
        resp = requests.post(urls['crowd_density_url'], data=data, headers=headers)
    except requests.exceptions.RequestException as e:
        print(e)
        return 'Linksmart Connection Failed: ' + str(e), 450
    else:
        print('SFN CONFIG ADDED: ' + resp.text, resp.status_code)
        return 'Registered SFN: ' + resp.text, resp.status_code


@app.route('/message', methods=['PUT'])
def add_message():
    print('REQUEST: ADD MESSAGE')
    if request.is_json:
        log_text = ''
        # GET THE JSON AND CHECK IF ITS STILL A STRING, IF SO loads JSON FORMAT
        message = request.get_json(force=True)
        if type(message) == str:
            message = json.loads(message)

        camera_id = message['camera_ids'][0]
        wp_module = message['type_module']

        # CHECK IF MESSAGE NEEDS CONVERTING TO TOP DOWN
        if wp_module == 'crowd_density_local':
            # IF SO GET THE CONFIG WITH MATCHING camera_id
            config = sfn_module.query_config_db(camera_id)
            if len(config) == 1:
                config = json.loads(config[0][1])

                # CONVERT TO TOP DOWN, AND SAVE TO THE DATABASE OF MESSAGES
                # TODO: SORT OUT THE IMAGE SIZES
                message['density_map'], heat_image = mp.generate_heat_map(
                    message['density_map'], config['image_2_ground_plane_matrix'], config['ground_plane_roi'],
                    config['ground_plane_size'], timestamp=message['timestamp_1'],
                    frame=tools.decode_image(message['frame_byte_array'], message['image_dims'], False)
                    )
                # REMOVE THE FRAME AS ITS NOT NEEDED
                message['frame_byte_array'] = ''
                log_text = log_text + ' crowd_density_local MESSAGE CONVERTED TO TOP DOWN.'

        # MESSAGE SORTING CODE: FIND THE CAMERA ID AND MODULE AND UPDATE recent_cam_messages
        log_text = log_text + sfn_module.insert_db(c_id=camera_id, m_id=wp_module, msg=json.dumps(message))

        # FILTER CODE HERE: DO SOMETHING BASED ON WHAT MODULE SENT THE MESSAGE
        new_message = None
        url = ''
        if wp_module == 'crowd_density_local':
            # MESSAGE HAS ALREADY BEEN CONVERTED TO TOP DOWN VIEW
            new_message = message
            url = urls['crowd_density_url']
        elif wp_module == 'flow_analysis':
            print('DO SOMETHING FLOW-EY')

        # DUMP THE NEW MESSAGE TO JSON AND FORWARD TO LINKSMART
        if new_message is not None:
            mp.forward_message(new_message, url)

        # UNDER AND IF STATEMENT CHECK IF WE WANT TO AMALGAMATE AND CREATE A NEW MESSAGE
        if sfn_module.length_db() > 2:
            mp.amalgamate_crowd_density_local(sfn_module, urls['crowd_density_url'])
        else:
            # NO MESSAGES HELD
            print('NOT ENOUGH MESSAGES in recent_cam_messages')

        return log_text, 205
    else:
        return 'No JSON.', 415


# ROUTE FOR VCA TO UPDATE CONFIGS
@app.route("/configs", methods=['POST'])
def update_configs():
    print('REQUEST: UPDATE THE CONFIG DB')
    if request.is_json:
        new_configs = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(new_configs) == str:
            new_configs = json.loads(new_configs)
        # TODO: ADD CHECKS TO THE AMOUNT OF CONFIGS BEING UPDATED WITH THE AMOUNT IN THE DB
        # TODO: RETURN USEFUL INFO ON TEH UPDATES
        # TODO: CHECK THE DB FOR EXISTING VERSION OF THE CONFIG
        # GET A LIST OF CONFIG DICTS, LOOP THROUGH AND ADD TO DB
        for config in new_configs:
            # CHECK IF CONFIG ALREADY EXISTS
            if new_configs:

                sfn_module.insert_config_db(c_id=config['camera_id'], msg=config)
            else:
                print('THIS IS A NEW CONFIG... WHY?')
                sfn_module.insert_config_db(c_id=config['camera_id'], msg=config)
        return 'UPDATED THE CONFIGS ON THE DB:', 200
    else:
        return 'No JSON.', 415


# ROUTES FOR THE DUMMY LINKSMART ONLY
@app.route("/linksmart")
def hello_linksmart():
    print('REQUEST: HELLO LINKSMART')
    try:
        resp = requests.get(urls['dummy_linksmart_url'])
    except requests.exceptions.RequestException as e:
        print(e)
        return 'Dummy Linksmart Connection Failed: ' + str(e), 502
    else:
        print(resp.text, resp.status_code)
        return resp.text + ' VIA SECURITY FUSION NODE', 200


@app.route("/linksmart/get_configs")
def get_configs_linksmart():
    print('REQUEST: GET THE CONFIGS FROM LINKSMART')
    try:
        resp = requests.get(urls['dummy_linksmart_url'] + 'configs')
    except requests.exceptions.RequestException as e:
        print(e)
        return 'Dummy Linksmart Connection Failed: ' + str(e), 502
    else:
        global cam_configs
        cam_configs = resp.json()
        # GET A LIST OF CONFIG DICTS, LOOP THROUGH AND ADD TO DB
        for config in cam_configs:
            if 'camera_id' in config:
                sfn_module.insert_config_db(c_id=config['camera_id'], msg=json.dumps(config))
            elif 'module_id' in config:
                sfn_module.insert_config_db(c_id=config['module_id'], msg=json.dumps(config))

        print('NUMBER OF CONFIGS RETURNED = ' + str(len(sfn_module.query_config_db())), resp.status_code)
        return 'OBTAINED CONFIGS VIA SECURITY FUSION NODE: ' + str(sfn_module.query_config_db()), 200


# RUN THE SERVICE
parser = argparse.ArgumentParser(description='Development Server Help')
parser.add_argument("-d", "--debug", action="store_true", dest="debug_mode",
                    help="run in debug mode (for use with PyCharm)", default=False)
parser.add_argument("-p", "--port", dest="port",
                    help="port of server (default:%(default)s)", type=int, default=5000)
parser.add_argument("-a", "--address", dest="host",
                    # help="host address of server (default:%(default)s)", type=str, default="0.0.0.0")
                    help="host address of server (default:%(default)s)", type=str, default="127.0.0.1")

cmd_args = parser.parse_args()
app_options = {"port": cmd_args.port,
               "host": cmd_args.host}

if cmd_args.debug_mode:
    app_options["debug"] = True
    app_options["use_debugger"] = False
    app_options["use_reloader"] = False

app.run(**app_options)

# TODO: ADD ON EXIT FUNCTIONALITY, CLOSE DBS etc
