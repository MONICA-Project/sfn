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
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'KFF_CAM_8_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'RIF_CAM_1_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'RIF_CAM_2_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'RIF_CAM_3_reg', False),
    tools.load_settings(os.path.join(KU_DIR, 'KUConfigTool/'), 'RIF_CAM_4_reg', False),
]
messages = []


def process_config(config):
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
    log = []
    if ind is None:
        configs.append(config)
        log = 'NEW CONFIG ADDED'
    else:
        print('EXISTING CONFIG FOUND, REPLACING')
        configs[ind] = config
        log = 'OLD CONFIG ({}) REPLACED'.format(str(ind))
    return log, 201


def process_message(mes):
    global messages
    messages.append(mes)
    try:
        if 'module_id' in mes:
            outfile = open(mes['type_module'] + '_' + mes['camera_ids'][0] + '.txt', 'w')
        else:
            outfile = open(mes['camera_ids'][0] + '.txt', 'w')
    except IOError:
        print('IOError SAVING .txt FILE')
        return 'IOError', 401
    else:
        outfile.write(json.dumps(mes))
        outfile.close()

    if len(messages) > 1000:
        messages = []
        print('TOO MANY MESSAGES RESETTING MESSAGE BUFFER.')
    else:
        print('HOLDING ' + str(len(messages)) + ' MESSAGES.')


# REPLICATED FUNCTIONS OF THE REAL SCRAL
@app.route('/scral/sfn/camera', methods=['POST'])
def add_camera():
    print('REQUEST: ADD CAMERA CONFIG')
    if request.is_json:
        config = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(config) == str:
            config = json.loads(config)
        return process_config(config)
        # return log, response_code
    else:
        return 'No JSON.', 415


@app.route('/scral/sfn/crowd_monitoring', methods=['POST'])
def add_config_crowd():
    print('REQUEST: ADD CROWD COUNTING CONFIG')
    if request.is_json:
        config = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(config) == str:
            config = json.loads(config)
        return process_config(config)
        # return log, response_code
    else:
        return 'No JSON.', 415


@app.route('/scral/sfn/crowd_monitoring', methods=['PUT'])
def add_message_crowd():
    print('REQUEST: ADD MESSAGE CD')
    if request.is_json:
        message = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(message) == str:
            message = json.loads(message)

        process_message(message)
        return 'Added Message.', 201
    else:
        return 'No JSON.', 415


@app.route('/scral/sfn/flow_analysis', methods=['POST'])
def add_config_flow():
    print('REQUEST: ADD FLOW ANALYSIS CONFIG')
    if request.is_json:
        config = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(config) == str:
            config = json.loads(config)

        log, response_code = process_config(config)
        return log, response_code
    else:
        return 'No JSON.', 415


@app.route('/scral/sfn/flow_analysis', methods=['PUT'])
def add_message_flow():
    print('REQUEST: ADD MESSAGE FA')
    if request.is_json:
        message = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(message) == str:
            message = json.loads(message)

        process_message(message)
        return 'Added Message.', 201
    else:
        return 'No JSON.', 415


@app.route('/scral/sfn/fight_detection', methods=['POST'])
def add_config_fight():
    print('REQUEST: ADD FIGHT DETECTION CONFIG')
    if request.is_json:
        config = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(config) == str:
            config = json.loads(config)

        log, response_code = process_config(config)
        return log, response_code
    else:
        return 'No JSON.', 415


@app.route('/scral/sfn/fight_detection', methods=['PUT'])
def add_message_fight():
    print('REQUEST: ADD MESSAGE FD')
    if request.is_json:
        message = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(message) == str:
            message = json.loads(message)

        process_message(message)
        return 'Added Message.', 201
    else:
        return 'No JSON.', 415


@app.route('/scral/sfn/object_detection', methods=['POST'])
def add_config_object():
    print('REQUEST: ADD OBJECT DETECTION CONFIG')
    if request.is_json:
        config = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(config) == str:
            config = json.loads(config)

        log, response_code = process_config(config)
        return log, response_code
    else:
        return 'No JSON.', 415


@app.route('/scral/sfn/object_detection', methods=['PUT'])
def add_message_object():
    print('REQUEST: ADD MESSAGE OD')
    if request.is_json:
        message = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(message) == str:
            message = json.loads(message)

        process_message(message)
        return 'Added Message.', 201
    else:
        return 'No JSON.', 415


# DEBUG FUNCTIONS
# HELLO WORLD
@app.route("/scral/sfn")
def hello_world():
    print('REQUEST: HELLO WORLD')
    return "Dummy SCRAL: Hello World!"


# CAMERA CONFIG ROUTES
@app.route("/configs")
def get_configs():
    print('REQUEST: ALL CONFIGS')
    cam_names = [i['camera_id'] for i in configs if 'camera_id' in i.keys()]
    mod_names = [i['module_id'] for i in configs if 'module_id' in i.keys()]
    cam_names.extend(mod_names)
    print(cam_names)
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
                    help="host address of server (default:%(default)s)", type=str, default="0.0.0.0")
                    # help="host address of server (default:%(default)s)", type=str, default="127.0.0.2")

cmd_args = parser.parse_args()
app_options = {"port": cmd_args.port,
               "host": cmd_args.host}

if cmd_args.debug_mode:
    app_options["debug"] = True
    app_options["use_debugger"] = False
    app_options["use_reloader"] = False

if __name__ == '__main__':
    app.run(**app_options)
