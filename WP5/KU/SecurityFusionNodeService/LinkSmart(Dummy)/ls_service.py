import json
import argparse
from flask import Flask, request
import loader_tools as tools

app = Flask(__name__)
configs = [
    tools.load_settings('/ocean/robdupre/PYTHON_SCRIPTS/MONICA/', 'KFF_CAM_2', True),
    tools.load_settings('/ocean/robdupre/PYTHON_SCRIPTS/MONICA/', 'KFF_CAM_4', True),
    tools.load_settings('/ocean/robdupre/PYTHON_SCRIPTS/MONICA/', 'KFF_CAM_8', True)
]
messages = [
    tools.load_json_txt(
        '/ocean/robdupre/PYTHON_SCRIPTS/MONICA/', 'KFF_CAM_8_00004')
]


# HELLO WORLD
@app.route("/")
def hello_world():
    print('REQUEST: HELLO WORLD')
    return "LinkSmart: Hello World!"


# CAMERA CONFIG ROUTES
@app.route("/configs")
def get_configs():
    print('REQUEST: ALL CONFIGS')
    return json.dumps(configs), 200


@app.route("/configs", methods=['POST'])
def search_config():
    print('REQUEST: SPECIFIC CONFIG')
    if request.is_json:
        config_id = json.loads(request.get_json())
        print('RETURN CONFIG ' + str(config_id) + '. ' + 'REQUEST IS OF TYPE: ' + str(type(config_id)))
        return json.dumps(configs[config_id])
    else:
        return 'Aint no JSON.', 299


@app.route('/add_configs', methods=['POST'])
def add_config():
    print('REQUEST: ADD CONFIG')
    if request.is_json:
        message = json.loads(request.get_json(force=True))
        # LOOP THROUGH CURRENT CONFIGS
        ind = None
        for i, item in enumerate(configs):
            # CHECK IF THE CURRENT CONFIG item AND THE message HAS EITHER camera_id OR A module_id KEYS
            if 'camera_id' in message and 'camera_id' in item:
                # CHECK IF IT MATCHES ONE IN configs
                if item['camera_id'] == message['camera_id']:
                    ind = i
                    break
            elif 'module_id' in message and 'module_id' in item:
                if item['module_id'] == message['module_id']:
                    ind = i
                    break

        if ind is None:
            configs.append(message)
            return 'NEW CONFIG ADDED', 205
        else:
            configs[ind] = message
            return 'OLD CONFIG (' + str(ind) + ') REPLACED', 205

    else:
        return 'Aint no JSON.', 299


@app.route('/configs', methods=['DELETE'])
def del_config():
    print('We be deleting')
    if request.is_json:
        config_id = json.loads(request.get_json())
        del configs[config_id]
        return 'Deleted', 205
    else:
        return 'Aint no JSON.', 299


# MESSAGE ROUTES
@app.route("/message")
def get_messages():
    print('REQUEST: ALL MESSAGES')
    return json.dumps(messages), 200


@app.route("/message", methods=['POST'])
def search_message():
    print('REQUEST: SPECIFIC MESSAGE')
    if request.is_json:
        message_id = json.loads(request.get_json())
        print('RETURN CONFIG ' + str(message_id) + '. ' + 'REQUEST IS OF TYPE: ' + str(type(message_id)))
        return json.dumps(messages[message_id])
    else:
        return 'Aint no JSON.', 299


@app.route('/add_message', methods=['POST'])
def add_message():
    print('REQUEST: ADD MESSAGE')
    if request.is_json:
        message = json.loads(request.get_json(force=True))
        messages.append(message)
        return 'Added Message.', 205
    else:
        return 'Aint no JSON.', 299


@app.route('/message', methods=['DELETE'])
def del_message():
    print('REQUEST: DELETE MESSAGE')
    if request.is_json:
        message_id = json.loads(request.get_json())
        del messages[message_id]
        return 'Deleted Message', 205
    else:
        return 'Aint no JSON.', 299


# RUN THE SERVICE
parser = argparse.ArgumentParser(description='Development Server Help')
parser.add_argument("-d", "--debug", action="store_true", dest="debug_mode",
                    help="run in debug mode (for use with PyCharm)", default=False)
parser.add_argument("-p", "--port", dest="port",
                    help="port of server (default:%(default)s)", type=int, default=5000)

cmd_args = parser.parse_args()
app_options = {"port": cmd_args.port,
               "host": "127.0.0.1"}

if cmd_args.debug_mode:
    app_options["debug"] = True
    app_options["use_debugger"] = False
    app_options["use_reloader"] = False

app.run(**app_options)