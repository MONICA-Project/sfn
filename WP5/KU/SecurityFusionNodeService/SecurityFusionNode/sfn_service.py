# sfn_service.py
"""Implementation of a RESTful webservice to handle messages produced from the VCA framework and forward them on to
linksmart"""
import argparse
import requests
import json
import datetime
import os
from flask import Flask, request
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
from WP5.KU.definitions import KU_DIR
import WP5.KU.SecurityFusionNodeService.loader_tools as tools
from WP5.KU.SecurityFusionNodeService.SecurityFusionNode.security_fusion_node import SecurityFusionNode
import WP5.KU.SecurityFusionNodeService.SecurityFusionNode.security_fusion_node as sfn

__version__ = '0.2'
__author__ = 'RoViT (KU)'

app = Flask(__name__)
sfn_module = SecurityFusionNode('001')
urls = {'dummy_linksmart_url': 'http://127.0.0.2:3389/',
        # 'crowd_density_url': 'https://portal.monica-cloud.eu/scral/sfn/crowdmonitoring',
        'crowd_density_url': 'http://127.0.0.2:3389/crowd_density',
        'flow_analysis_url': 'http://127.0.0.2:3389/flow_analysis',
        }

cam_configs = []

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

        # CHECK THAT THERE ARE CONFIGS TO LOOK THROUGH
        global cam_configs
        if len(cam_configs) > 0:
            config = next((item for item in cam_configs if item['camera_id'] == camera_id))

            if wp_module == 'crowd_density_local':
                # CONVERT TO TOP DOWN, GET THE CONFIG FOR THIS CAMERA
                # TODO: SORT OUT THE IMAGE SIZES
                message['density_map'], heat_image = sfn.generate_heat_map(
                    message['density_map'], config['image_2_ground_plane_matrix'], config['ground_plane_roi'],
                    config['ground_plane_size'], timestamp=message['timestamp_1'],
                    frame=tools.decode_image(message['frame_byte_array'], message['image_dims'], False)
                    )
                # REMOVE THE FRAME AS ITS NOT NEEDED
                message['frame_byte_array'] = ''
                log_text = log_text + ' crowd_density_local MESSAGE CONVERTED TO TOP DOWN.'

        # MESSAGE SORTING CODE: FIND THE CAMERA ID AND MODULE AND UPDATE recent_cam_messages
        if sfn_module.length_db() > 0:  # if len(recent_cam_messages) > 0:
            # FIND THE ENTRY FROM THIS CAM_ID FROM THIS MODULE AND REPLACE
            # row: the index of previous message for this camera and module
            row = sfn_module.query_db(camera_id, wp_module)

            # IF AN ENTRY IS FOUND:
            if len(row) != 0:
                print('THE MESSAGE FROM ' + wp_module + ' MODULE, FROM ' + camera_id + ', IS ALREADY STORED, REPLACING')
                log_text = log_text + 'PREVIOUS MESSAGE FROM ' + wp_module + ' MODULE, FROM ' + camera_id\
                    + ', ALREADY STORED, REPLACING.'
                sfn_module.delete_db(camera_id, wp_module)  # Delete the previous message from the database
                sfn_module.insert_db(camera_id, wp_module, json.dumps(message))  # Insert new message to the database
            else:
                # THIS IS THE FIRST INSTANCE OF THIS camera_id AND wp_module PAIR
                print('THIS IS A NEW MESSAGE FROM ' + wp_module + ' MODULE, FROM ' + camera_id)
                log_text = log_text + 'THIS IS A NEW MESSAGE FROM ' + wp_module + ' MODULE, FROM ' + camera_id + '.'
                sfn_module.insert_db(camera_id, wp_module, json.dumps(message))  # Insert new message to the database
        else:
            # NO MESSAGES HELD SO ADD THE FIRST ONE
            print('FIRST EVER MESSAGE')
            log_text = log_text + 'FIRST EVER MESSAGE.'
            sfn_module.insert_db(camera_id, wp_module, json.dumps(message))  # Insert new message to the database

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
            try:
                resp = requests.put(url, data=json.dumps(new_message), headers=headers)
                # resp = requests.put(linksmart_url + 'add_message', data=json.dumps(new_message), headers=headers)
            except requests.exceptions.RequestException as e:
                print(e)
                return 'Linksmart Connection Failed: ' + str(e), 450
            else:
                print(resp.text)
                log_text = log_text + ' MESSAGE HAS BEEN FORWARDED TO LINKSMART(' + resp.text + ').'

        # UNDER AND IF STATEMENT CHECK IF WE WANT TO AMALGAMATE AND CREATE A NEW MESSAGE
        # TODO: CHANGE THIS SO ITS NOT RUN EVERY TIME A MESSAGE IS SENT
        if sfn_module.length_db() > 2:  # len(recent_cam_messages) > 2:
            top_down_maps = []
            config_for_amalgamation = []
            amalgamation_cam_ids = []
            amalgamation_density_count = 0
            amalgamation_timestamp_1 = 0
            amalgamation_timestamp_2 = 0
            # FIND THE ENTRY FROM THIS CAM_ID FROM THIS MODULE AND REPLACE
            recent_cam_messages = sfn_module.query_db(None, 'crowd_density_local')  # Search for a specific module_id
            recent_cam_messages = [json.loads(item[2]) for item in recent_cam_messages]

            for i, item in enumerate(recent_cam_messages):

                if i == 0:
                    amalgamation_timestamp_1 = recent_cam_messages[i]['timestamp_1']
                    amalgamation_timestamp_2 = recent_cam_messages[i]['timestamp_2']
                else:
                    amalgamation_timestamp_1 = min(amalgamation_timestamp_1, recent_cam_messages[i]['timestamp_1'])
                    amalgamation_timestamp_2 = max(amalgamation_timestamp_2, recent_cam_messages[i]['timestamp_2'])
                amalgamation_cam_ids.append(recent_cam_messages[i]['camera_ids'])
                amalgamation_density_count += recent_cam_messages[i]['density_count']
                top_down_maps.append(recent_cam_messages[i]['density_map'])
                conf = next((item for item in cam_configs if item['camera_id'] ==
                             recent_cam_messages[i]['camera_ids'][0]))
                config_for_amalgamation.append(conf['ground_plane_position'] + [conf['camera_tilt']])

            # RUN THE AMALGAMATION
            amalgamated_top_down_map = sfn_module.generate_amalgamated_top_down_map(top_down_maps,
                                                                                    config_for_amalgamation)

            # Create new message
            crowd_density_global = sfn_module.create_obs_message(amalgamation_cam_ids, amalgamation_density_count,
                                                                 amalgamated_top_down_map, amalgamation_timestamp_1,
                                                                 amalgamation_timestamp_2)

            log_text = log_text + ' CURRENTLY HELD MESSAGES HAVE BEEN AMALGAMATED INTO THE crowd_density_global VIEW. '

            # SEND crowd_density_global MESSAGE TO LINKSMART
            try:
                resp = requests.put(urls['crowd_density_url'], json=crowd_density_global,
                                    headers={'content-Type': 'application/json'})
            except requests.exceptions.RequestException as e:
                print(e)
                return 'Linksmart Connection Failed: ' + str(e), 450
            else:
                print(resp.text)
                log_text = log_text + ' crowd_density_global MESSAGE CREATED AND SENT(' + resp.text + ').'
        else:
            # NO MESSAGES HELD
            print('NOT ENOUGH MESSAGES in recent_cam_messages')

        return log_text, 205
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
        print('NUMBER OF CONFIGS RETURNED = ' + str(len(cam_configs)), resp.status_code)
        return 'OBTAINED CONFIGS VIA SECURITY FUSION NODE: ' + str(cam_configs), 200


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
