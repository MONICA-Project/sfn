# sfn_service.py
"""Implementation of a RESTful webservice to handle messages produced from the VCA framework and forward them on to
linksmart"""
import argparse
import requests
import json
import arrow
import time
import datetime
import uuid
from flask import Flask, request
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
from WP5.KU.SecurityFusionNodeService.SecurityFusionNode.security_fusion_node import SecurityFusionNode
from WP5.KU.SecurityFusionNodeService.SecurityFusionNode.message_processing import crowd_density_local, flow_analysis,\
    amalgamate_crowd_density_local, fighting_detection, object_detection, action_recognition

__version__ = '0.2'
__author__ = 'RoViT (KU)'

app = Flask(__name__)
print('SFN STARTING. MODULE ID: {}'.format(uuid.uuid5(uuid.NAMESPACE_DNS, 'SFN')))
sfn_module = SecurityFusionNode(str(uuid.uuid5(uuid.NAMESPACE_DNS, 'SFN')))

headers = {'content-Type': 'application/json'}


@app.route("/")
def hello_world():
    print('REQUEST: HELLO WORLD')
    return "SECURITY FUSION NODE"


@app.route("/debug")
def debug():
    print('REQUEST: FLIP DEBUGGING MODE')
    debug_mode = sfn_module.flip_debug()
    return "DEBUGGING IS SET TO {}".format(debug_mode), 200


@app.route("/urls", methods=['POST'])
def update_urls():
    print('REQUEST: UPDATE URLS')
    if request.is_json:
        url_updates = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(url_updates) == str:
            url_updates = json.loads(url_updates)

        for url in sfn_module.urls:
            if url in url_updates:
                sfn_module.urls[url] = url_updates[url]
                print('Updating Key ({}) to: {}.'.format(url, url_updates[url]))
            else:
                print('Key ({}) not found.'.format(url))

        return 'SFN urls updated', 201
    else:
        return 'No JSON.', 415


@app.route("/settings")
def update_settings():
    print('REQUEST: UPDATE SETTINGS')
    sfn_module.load_settings(str(Path(__file__).absolute().parents[0]), 'settings', update_urls=False)
    return "SECURITY FUSION NODE SETTINGS UPDATED"


@app.route("/register")
def register_sfn():
    print('REQUEST: SEND SFN REGISTRATION')
    data = sfn_module.create_reg_message(datetime.datetime.utcnow().isoformat())
    try:
        resp = requests.post(sfn_module.urls['crowd_density_url'], data=data, headers=headers)
    except requests.exceptions.RequestException as e:
        print(e)
        return 'Linksmart Connection Failed: ' + str(e), 450
    else:
        print('SFN CONFIG ADDED: ' + resp.text, resp.status_code)
        return 'Registered SFN: ' + resp.text, resp.status_code


@app.route('/message', methods=['PUT'])
def add_message():
    log_text = 'REQUEST: ADD MESSAGE. '
    start = time.time()
    if request.is_json:
        resp_code = 0
        # GET THE JSON AND CHECK IF ITS STILL A STRING, IF SO loads JSON FORMAT
        message = request.get_json(force=True)
        if type(message) == str:
            message = json.loads(message)

        if message is not None and 'type_module' in message:
            wp_module = message['type_module']
            log_text = wp_module + ' '
            # BASED ON wp_module PERFORM PROCESSING ON MODULE
            text = ''
            if wp_module == 'crowd_density_local':
                cam_id = message['camera_ids'][0]
                text, resp_code = crowd_density_local(sfn_module, cam_id, sfn_module.urls['crowd_density_url'], message)
            elif wp_module == 'flow':
                cam_id = message['camera_ids'][0]
                text, resp_code = flow_analysis(sfn_module, cam_id, sfn_module.urls['flow_analysis_url'], message)
            elif wp_module == 'fighting_detection':
                cam_id = message['camera_ids'][0]
                text, resp_code = fighting_detection(sfn_module, cam_id, sfn_module.urls['fighting_detection_url'], message)
            elif wp_module == 'object_detection':
                cam_id = message['camera_ids'][0]
                text, resp_code = object_detection(sfn_module, cam_id, sfn_module.urls['object_detection_url'], message)
            elif wp_module == 'action_recognition':
                cam_id = message['camera_ids'][0]
                text, resp_code = action_recognition(sfn_module, cam_id, sfn_module.urls['action_recognition_url'], message)
            # print('Function has taken: {}s'.format(time.time() - start))
            log_text = log_text + text

            # UNDER AND IF STATEMENT CHECK IF WE WANT TO AMALGAMATE AND CREATE A NEW MESSAGE
            sfn_module.timer = time.time() - sfn_module.last_amalgamation
            if sfn_module.length_db(module_id='crowd_density_local') > 2 and sfn_module.timer > sfn_module.amal_interval:
                sfn_module.last_amalgamation = time.time()
                text, resp_code = amalgamate_crowd_density_local(sfn_module, sfn_module.urls['crowd_density_url'])
            else:
                # NO MESSAGES HELD
                text = 'TIME SINCE LAST AMALGAMATION: {}. '.format(sfn_module.timer)

            log_text = log_text + text
            print(log_text)
            print('Function has taken: {}s'.format(time.time() - start))
            return log_text, resp_code
        else:
            log_text = log_text + 'NO type_module FOUND IN THE MESSAGE'
            print(log_text)
            return 'NO type_module FOUND IN THE MESSAGE.', 415
    else:
        log_text = log_text + 'No JSON'
        print(log_text)
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

        # UPDATE THE SFN REG MESSAGE
        config = json.loads(sfn_module.create_reg_message(arrow.utcnow()))
        log_text = sfn_module.insert_config_db(c_id=config['module_id'], msg=json.dumps(config))
        print(log_text)
        for config in new_configs:
            if 'camera_id' in config:
                log_text = sfn_module.insert_config_db(c_id=config['camera_id'], msg=json.dumps(config))
            elif 'module_id' in config:
                log_text = sfn_module.insert_config_db(c_id=config['module_id'], msg=json.dumps(config))
            print(log_text)

        configs = sfn_module.query_config_db(None)
        configs = [json.loads(item.msg) for item in configs]
        for config in configs:
            if 'camera_id' in config:
                sfn_module.send_reg_message(json.dumps(config), sfn_module.urls['camera_reg_url'])
            elif 'module_id' in config:
                if config['type_module'] == 'crowd_density_local':
                    print('SENDING CONFIG crowd_density_local')
                    sfn_module.send_reg_message(json.dumps(config), sfn_module.urls['crowd_density_url'])
                elif config['type_module'] == 'crowd_density_global':
                    print('SENDING CONFIG crowd_density_global')
                    sfn_module.send_reg_message(json.dumps(config), sfn_module.urls['crowd_density_url'])
                elif config['type_module'] == 'flow':
                    print('SENDING CONFIG flow')
                    sfn_module.send_reg_message(json.dumps(config), sfn_module.urls['flow_analysis_url'])
                elif config['type_module'] == 'fighting_detection':
                    print('SENDING CONFIG fighting_detection')
                    sfn_module.send_reg_message(json.dumps(config), sfn_module.urls['fighting_detection_url'])
                elif config['type_module'] == 'object_detection':
                    print('SENDING CONFIG object_detection')
                    sfn_module.send_reg_message(json.dumps(config), sfn_module.urls['object_detection_url'])
                elif config['type_module'] == 'action_recognition':
                    print('SENDING CONFIG action_recognition')
                    sfn_module.send_reg_message(json.dumps(config), sfn_module.urls['action_recognition_url'])

        return log_text, 200
    else:
        return 'No JSON.', 415


@app.route("/scral")
def hello_linksmart():
    print('REQUEST: HELLO SCRAL')
    try:
        resp = requests.get(sfn_module.urls['scral_url'] + 'scral/sfn')
    except requests.exceptions.RequestException as e:
        print(e)
        return 'SCRAL Connection Failed: ' + str(e), 502
    else:
        print(resp.text, resp.status_code)
        return resp.text + ' VIA SECURITY FUSION NODE', 200


# RUN THE SERVICE
parser = argparse.ArgumentParser(description='Development Server Help')
parser.add_argument("-d", "--debug", action="store_true", dest="debug_mode",
                    help="run in debug mode (for use with PyCharm)", default=False)
parser.add_argument("-p", "--port", dest="port",
                    help="port of server (default:%(default)s)", type=int, default=5000)
parser.add_argument("-a", "--address", dest="host",
                    help="host address of server (default:%(default)s)", type=str, default="0.0.0.0")

cmd_args = parser.parse_args()
app_options = {"port": cmd_args.port,
               "host": cmd_args.host}

if cmd_args.debug_mode:
    app_options["debug"] = True
    app_options["use_debugger"] = False
    app_options["use_reloader"] = False

app.run(**app_options)

# TODO: ADD ON EXIT FUNCTIONALITY, CLOSE DBS etc
