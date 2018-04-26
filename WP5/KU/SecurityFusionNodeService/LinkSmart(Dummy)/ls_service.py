# ls_service.py
"""Dummy webservice created to test the sfn_service in the absence of a actual Linksmart instance"""
import json
import os
import argparse
from flask import Flask, request
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
from WP5.KU.definitions import KU_DIR
import WP5.KU.SecurityFusionNodeService.loader_tools as tools

__version__ = '0.1'
__author__ = 'RoViT (KU)'

app = Flask(__name__)
print(str(Path(__file__).absolute().parents[4]))
configs = [
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'KFF_CAM_2_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'KFF_CAM_4_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'KFF_CAM_8_reg', False)
]
messages = []


# REPLICATED FUNCTIONS OF THE REAL SCRAL
@app.route('/crowd_density', methods=['POST'])
def add_config():
    print('REQUEST: ADD CONFIG')
    if request.is_json:
        config = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(config) == str:
            config = json.loads(config)
        # LOOP THROUGH CURRENT CONFIGS
        ind = None
        # WRITE THE NEW CONFIG TO FILE (DEBUGGING)
        try:
            if 'module_id' in config:
                outfile = open(config['module_id'] + '_reg.txt', 'w')
            else:
                outfile = open(config['camera_id'] + '_reg.txt', 'w')
        except IOError:
            print('IOError SAVING .txt FILE')
            return 'IOError', 511
        else:
            outfile.write(json.dumps(config))
            outfile.close()
        for i, item in enumerate(configs):
            # CHECK IF THE CURRENT CONFIG item AND THE config HAS EITHER camera_id OR A module_id KEYS
            if 'camera_id' in config and 'camera_id' in item:
                # CHECK IF IT MATCHES ONE IN configs
                if item['camera_id'] == config['camera_id']:
                    ind = i
                    break
            elif 'module_id' in config and 'module_id' in item:
                if item['module_id'] == config['module_id']:
                    ind = i
                    break

        if ind is None:
            configs.append(config)
            return 'NEW CONFIG ADDED', 201
        else:
            print('EXISTING CONFIG FOUND, REPLACING')
            configs[ind] = config
            return 'OLD CONFIG (' + str(ind) + ') REPLACED', 201

    else:
        return 'No JSON.', 415


@app.route('/crowd_density', methods=['PUT'])
def add_message():
    print('REQUEST: ADD MESSAGE')
    if request.is_json:
        message = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(message) == str:
            message = json.loads(message)

        messages.append(message)
        try:
            if 'module_id' in message:
                outfile = open(message['module_id'] + '.txt', 'w')
            else:
                outfile = open(message['camera_ids'][0] + '.txt', 'w')
        except IOError:
            print('IOError SAVING .txt FILE')
            return 'IOError', 401
        else:
            outfile.write(json.dumps(message))
            outfile.close()
        print('HOLDING ' + str(len(messages)) + ' MESSAGES.')
        return 'Added Message.', 201
    else:
        return 'No JSON.', 415


# DEBUG FUNCTIONS
# HELLO WORLD
@app.route("/")
def hello_world():
    print('REQUEST: HELLO WORLD')
    return "Dummy LinkSmart: Hello World!"


# CAMERA CONFIG ROUTES
@app.route("/configs")
def get_configs():
    print('REQUEST: ALL CONFIGS')
    return json.dumps(configs), 200


@app.route('/configs', methods=['DELETE'])
def del_config():
    print('REQUEST: DELETE A CONFIG')
    if request.is_json:
        config_id = request.get_json()
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(config_id) == str:
            config_id = json.loads(config_id)
        print('DELETING CONFIG:'.format(configs[config_id]))
        del configs[config_id]
        return 'Deleted', 200
    else:
        return 'No JSON.', 415


# MESSAGE ROUTES
@app.route("/message")
def get_messages():
    print('REQUEST: ALL MESSAGES')
    return json.dumps(messages), 200


@app.route("/message", methods=['POST'])
def search_message():
    print('REQUEST: SPECIFIC MESSAGE')
    if request.is_json:
        message_id = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(message_id) == str:
            message_id = json.loads(message_id)
        print('RETURN CONFIG ' + str(message_id) + '. ' + 'REQUEST IS OF TYPE: ' + str(type(message_id)))
        return json.dumps(messages[message_id]), 200
    else:
        return 'No JSON.', 415


@app.route('/message', methods=['DELETE'])
def del_message():
    print('REQUEST: DELETE MESSAGE')
    if request.is_json:
        message_id = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(message_id) == str:
            message_id = json.loads(message_id)
        del messages[message_id]
        print('HOLDING ' + str(len(messages)) + ' MESSAGES.')
        return 'Deleted Message', 200
    else:
        return 'No JSON.', 415


# RUN THE SERVICE
parser = argparse.ArgumentParser(description='Development Server Help')
parser.add_argument("-d", "--debug", action="store_true", dest="debug_mode",
                    help="run in debug mode (for use with PyCharm)", default=False)
parser.add_argument("-p", "--port", dest="port",
                    help="port of server (default:%(default)s)", type=int, default=3389)
parser.add_argument("-a", "--address", dest="host",
                    # help="host address of server (default:%(default)s)", type=str, default="0.0.0.0")
                    help="host address of server (default:%(default)s)", type=str, default="127.0.0.2")

cmd_args = parser.parse_args()
app_options = {"port": cmd_args.port,
               "host": cmd_args.host}

if cmd_args.debug_mode:
    app_options["debug"] = True
    app_options["use_debugger"] = False
    app_options["use_reloader"] = False

app.run(**app_options)
