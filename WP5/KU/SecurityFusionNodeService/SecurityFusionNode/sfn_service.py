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

app = Flask(__name__)
sfn = SecurityFusionNode('001')
linksmart_url = 'http://127.0.0.1:5000/'
cam_configs = []
recent_cam_messages = [
    tools.load_json_txt(os.path.join(KU_DIR, 'Algorithms/'), 'KFF_CAM_8_00004')]


@app.route("/")
def hello_world():
    print('REQUEST: HELLO WORLD')
    return "SECURITY FUSION NODE"


@app.route("/linksmart")
def hello_linksmart():
    print('REQUEST: HELLO LINKSMART')
    try:
        resp = requests.get(linksmart_url)
    except requests.exceptions.RequestException as e:
        print(e)
        return e, 299
    else:
        print(resp.text, resp.status_code)
        return resp.text + ' VIA SECURITY FUSION NODE', 205


@app.route("/linksmart/get_configs")
def get_configs_linksmart():
    print('REQUEST: GET THE CONFIGS FROM LINKSMART')
    try:
        resp = requests.get(linksmart_url + 'configs')
    except requests.exceptions.RequestException as e:
        print(e)
        return e, 299
    else:
        global cam_configs
        cam_configs = resp.json()
        print(cam_configs, resp.status_code)
        return 'OBTAINED CONFIGS VIA SECURITY FUSION NODE: ' + str(cam_configs), 205


@app.route("/register")
def register_sfn():
    print('REQUEST: SEND SFN REGISTRATION TO LINKSMART')
    data = sfn.create_reg_message(datetime.datetime.utcnow().isoformat())
    try:
        resp = requests.post(linksmart_url + 'add_configs', json=data)
    except requests.exceptions.RequestException as e:
        print(e)
        return e, 299
    else:
        print(resp.status_code, resp.headers['content-type'], resp.text)
        return 'Registered SFN on LINKSMART: ' + resp.text, resp.status_code


@app.route('/message', methods=['POST'])
def add_message():
    print('REQUEST: MESSAGE')
    if request.is_json:

        message = json.loads(request.get_json(force=True))
        # FILTER CODE HERE: FIND THE CAMERA ID AND MODULE AND UPDATE recent_cam_messages
        # TODO: DATABASE HERE?
        camera_id = message['camera_ids'][0]
        module = message['type_module']

        global recent_cam_messages
        if len(recent_cam_messages) > 0:
            ind = None
            # FIND THE ENTRY FROM THIS CAM_ID FROM THIS MODULE AND REPLACE
            for i, item in enumerate(recent_cam_messages):
                if (item['camera_ids'][0] == camera_id) and (item['type_module'] == module):
                    ind = i
            if ind is not None:
                recent_cam_messages[ind] = message
            else:
                # THIS IS THE FIRST INSTANCE OF THIS camera_id AND module PAIR
                recent_cam_messages.append(message)
        else:
            # NO MESSAGES HELD SO ADD THE FIRST ONE
            recent_cam_messages.append(message)

        # message = next((item for item in recent_cam_messages
        #                if item['camera_id'] == camera_id and item['type_module'] == module))

        # FILTER CODE HERE

        if module == 'crowd_density_local':
            # CONVERT TO TOP DOWN, GET THE CONFIG FOR THIS CAMERA
            frame = tools.decode_image(message['frame_byte_array'], message['image_dims'], False)
            config = next((item for item in cam_configs if item['camera_id'] == camera_id))
            # TODO: SORT OUT THE IMAGE SIZES
            heat_map, heat_image = sfn.generate_heat_map(message['density_map'], config['heat_map_transform'],
                                                         config['ground_plane_roi'], config['ground_plane_size'],
                                                         # frame=frame)
                                                         frame=None)
            new_message = sfn.create_obs_message([camera_id], message['density_count'], heat_map,
                                                 message['timestamp_1'], message['timestamp_2'], frame)
            try:
                resp = requests.post(linksmart_url + 'add_message', json=new_message)
            except requests.exceptions.RequestException as e:
                print(e)
                return e, 299
            else:
                print(resp.text)

            # SHOULD WE RUN AMALAGAMTION

            # RUN THE AMALGAMATION

            # SEND THE AMALGAMATION MESSSAGE


            return 'Crowd Density (local) message from ' + camera_id + \
                   ', converted to top down view and forwarded to linksmart', 205
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
               "host": "127.0.0.2"}

if cmd_args.debug_mode:
    app_options["debug"] = True
    app_options["use_debugger"] = False
    app_options["use_reloader"] = False

app.run(**app_options)
