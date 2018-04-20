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
linksmart_url = 'http://127.0.0.2:3389/'
cam_configs = []
recent_cam_messages = [
    # tools.load_json_txt(os.path.join(KU_DIR, 'Algorithms/'), 'KFF_CAM_8_00004')
                      ]


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
        return resp.text + ' VIA SECURITY FUSION NODE', 205\



@app.route("/linksmart", methods=['POST'])
def set_linksmart_url():
    print('REQUEST: SET LINKSMART URL')
    if request.is_json:
        global linksmart_url
        linksmart_url = request.get_json(force=True)

        return 'Linksmart url UPDATED', 205
    else:
        return 'Aint no JSON.', 299


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
        print('NUMBER OF CONFIGS RETURNED = ' + str(len(cam_configs)), resp.status_code)
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
        log_text = ''
        message = json.loads(request.get_json(force=True))
        # FILTER CODE HERE: FIND THE CAMERA ID AND MODULE AND UPDATE recent_cam_messages
        # TODO: DATABASE HERE?
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

                log_text = log_text + ' crowd_density_local MESSAGE CONVERTED TO TOP DOWN.'

        global recent_cam_messages
        if len(recent_cam_messages) > 0:
            ind = None
            # FIND THE ENTRY FROM THIS CAM_ID FROM THIS MODULE AND REPLACE
            for i, item in enumerate(recent_cam_messages):
                if (item['camera_ids'][0] == camera_id) and (item['type_module'] == wp_module):
                    ind = i
            if ind is not None:
                print('THE MESSAGE FROM ' + wp_module + ' MODULE, FROM ' + camera_id + ', IS ALREADY STORED, REPLACING')
                log_text = log_text + 'PREVIOUS MESSAGE FROM ' + wp_module + ' MODULE, FROM ' + camera_id\
                    + ', ALREADY STORED, REPLACING.'
                recent_cam_messages[ind] = message
            else:
                # THIS IS THE FIRST INSTANCE OF THIS camera_id AND wp_module PAIR
                print('THIS IS A NEW MESSAGE FROM ' + wp_module + ' MODULE, FROM ' + camera_id)
                log_text = log_text + 'THIS IS A NEW MESSAGE FROM ' + wp_module + ' MODULE, FROM ' + camera_id + '.'
                recent_cam_messages.append(message)
        else:
            # NO MESSAGES HELD SO ADD THE FIRST ONE
            print('FIRST EVER MESSAGE')
            log_text = log_text + 'FIRST EVER MESSAGE.'
            recent_cam_messages.append(message)

        # message = next((item for item in recent_cam_messages
        #                if item['camera_id'] == camera_id and item['type_module'] == wp_module))

        # FILTER CODE HERE
        new_message = None
        if wp_module == 'crowd_density_local':
            # MESSAGE HAS ALREADY BEEN CONVERTED TO TOP DOWN VIEW
            new_message = message

        # DUMP THE NEW MESSAGE TO JSON AND FORWARD TO LINKSMART
        if new_message is not None:
            try:
                resp = requests.post(linksmart_url + 'add_message', json=json.dumps(new_message))
            except requests.exceptions.RequestException as e:
                print(e)
                return e, 299
            else:
                print(resp.text)
                log_text = log_text + ' MESSAGE HAS BEEN FORWARDED TO LINKSMART(' + resp.text + ').'

        # SHOULD WE RUN AMALGAMATION
        crowd_density_global = None
        topDown_maps = []
        config_for_amalgamation = []
        amal_cam_ids = []
        amal_density_count = 0

        # UNDER AND IF STATEMENT CHECK IF WE WANT TO AMALGAMATE AND CREATE A NEW MESSAGE
        if len(recent_cam_messages) > 0:
            ind = None
            # FIND THE ENTRY FROM THIS CAM_ID FROM THIS MODULE AND REPLACE
            for i, item in enumerate(recent_cam_messages):
                if (item['type_module'] == 'crowd_density_local'):
                    if i == 0:
                        amal_timestamp_1 = recent_cam_messages[i]['timestamp_1']
                        amal_timestamp_2 = recent_cam_messages[i]['timestamp_2']
                    else:
                        amal_timestamp_1 = min(amal_timestamp_1, recent_cam_messages[i]['timestamp_1'])
                        amal_timestamp_2 = max(amal_timestamp_2, recent_cam_messages[i]['timestamp_2'])
                    amal_cam_ids.append(recent_cam_messages[i]['camera_ids'])
                    amal_density_count += recent_cam_messages[i]['density_count']
                    topDown_maps.append(recent_cam_messages[i]['density_map'])
                    conf = next(
                        (item for item in cam_configs if item['camera_id'] == recent_cam_messages[i]['camera_ids'][0]))
                    # config_for_amalgamation.append(config['ground_plane_gps']+[conf['camera_tilt']])
                    config_for_amalgamation.append(config['ground_plane_position'] + [conf['camera_tilt']])
        else:
            # NO MESSAGES HELD
            print('NO MESSAGE in recent_cam_messages')

        # RUN THE AMALGAMATION
        print('111111111111111111111111111')
        print(len(recent_cam_messages))
        print(len(topDown_maps))
        amalgamated_topDown_map = sfn.generate_amalgamated_topDown_map(topDown_maps, config_for_amalgamation)
        print('222222222222222222222222222')
        # crowd_density_global = sfn.create_obs_message([camera_id], message['density_count'], message['density_map'],
        # Create new message                                             message['timestamp_1'], message['timestamp_2'])
        crowd_density_global = sfn.create_obs_message(amal_cam_ids, amal_density_count, amalgamated_topDown_map,
                                                      amal_timestamp_1, amal_timestamp_2)

        log_text = log_text + ' CURRENTLY HELD MESSAGES HAVE BEEN AMALGAMATED INTO THE crowd_density_global VIEW. '

        # SEND crowd_density_global MESSAGE TO LINKSMART
        if crowd_density_global is not None:
            try:
                resp = requests.post(linksmart_url + 'add_message', json=crowd_density_global)
            except requests.exceptions.RequestException as e:
                print(e)
                return e, 299
            else:
                print(resp.text)
                log_text = log_text + ' crowd_density_global MESSAGE CREATED AND SENT TO LINKSMART(' + resp.text + ').'

        return log_text, 205
    else:
        return 'Aint no JSON.', 299


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
