# message_processing.py
"""Functions to process the incoming messages to the SFN"""

import numpy as np
import cv2
import json
import requests
import time
from pathlib import Path
import sys
import time
sys.path.append(str(Path(__file__).absolute().parents[4]))
import WP5.KU.SecurityFusionNodeService.loader_tools as tools


__version__ = '0.2'
__author__ = 'RoViT (KU)'


def crowd_density_local(sfn_instance, camera_id, url, message, j_id=0):
    """ Message process function to be used when messages of type crowd_density_local are sent to the sfn_service.
        Convert to top down, save in db and forward on message
        Keyword arguments:
            sfn_instance --     The instance of the SFN module, handling all database interactions
            camera_id --        Used to pull back the correct config data from the SFN database
            url --              The url to forward the message to once processing has been completed
            message --          The original decoded JSON message in Dictionary form
        Returns:
            log_text --         A trace text outlining the path the message has taken
            resp_code --        A code which can be used in the SFN_Service response
        """
    log_text = ''
    resp_code = 0
    start = time.time()

    # GET THE CONFIG WITH MATCHING camera_id
    config = sfn_instance.query_config_db(camera_id)
    if len(config) == 1:
        # config = json.loads(config[0][1])

        # print('Function has taken: {}s'.format(time.time() - start))
        # REMOVE THE FRAME AND IMAGE SIZE AS ITS NOT NEEDED
        message['frame_byte_array'] = ''
        message['image_dims'] = ''
        # SAVE TO THE DATABASE OF MESSAGES AND FORWARD THE NEW MESSAGE
        log_text = log_text + sfn_instance.insert_db(camera_id, 'crowd_density_local', json.dumps(message))
        text, resp_code = forward_message(json.dumps(message), url)
        log_text = log_text + text
    else:
        log_text = log_text + 'EITHER NO CONFIG WAS FOUND OR > 1 WAS LOCATED AND CONFUSED THINGS. '
    # LOG THE OUTPUT OF THIS MESSAGE OPERATION
    sfn_instance.insert_log(j_id, message['timestamp_1'], log_text)
    # print('Function has taken: {}s'.format(time.time() - start))
    return log_text, resp_code


def flow_analysis(sfn_instance, url, message):
    """ Message process function to be used when messages of type flow_analysis are sent to the sfn_service
        Keyword arguments:
            sfn_instance --     The instance of the SFN module, handling all database interactions
            url --              The url to forward the message to once processing has been completed
            message --          The original decoded JSON message in Dictionary form
        Returns:
            log_text --         A trace text outlining the path the message has taken
            resp_code --        A code which can be used in the SFN_Service response
        """
    log_text = ''
    resp_code = 0
    print('DO SOMETHING FLOW-ISH')
    return log_text, resp_code


def forward_message(message, url):
    try:
        resp = requests.put(url, data=message, headers={'content-Type': 'application/json'})
    except requests.exceptions.RequestException as e:
        print(e)
        return 'Connection Failed: ' + str(e), 450
    else:
        print(resp.text)
        return 'MESSAGE HAS BEEN FORWARDED (' + resp.text + '). ', 201


def amalgamate_crowd_density_local(sfn_instance, url):
    sfn_module = sfn_instance
    log_text = ''

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
        amalgamation_cam_ids.append(recent_cam_messages[i]['camera_ids'][0])
        amalgamation_density_count += recent_cam_messages[i]['density_count']
        top_down_maps.append(recent_cam_messages[i]['density_map'])

        config = sfn_module.query_config_db(recent_cam_messages[i]['camera_ids'][0])
        config = json.loads(config[0][1])
        config_for_amalgamation.append(config['ground_plane_position'] + [config['camera_tilt']])

    # RUN THE AMALGAMATION
    amalgamated_top_down_map, amalgamation_ground_plane_position = sfn_module.generate_amalgamated_top_down_map(
        top_down_maps, config_for_amalgamation)
    log_text = log_text + 'CURRENTLY HELD MESSAGES HAVE BEEN AMALGAMATED INTO THE crowd_density_global VIEW. '

    # Create new message
    crowd_density_global = sfn_module.create_obs_message(amalgamation_cam_ids, amalgamation_density_count,
                                                         amalgamated_top_down_map, amalgamation_timestamp_1,
                                                         amalgamation_timestamp_2, amalgamation_ground_plane_position)
    log_text = log_text + 'crowd_density_global MESSAGE CREATED. '

    # SEND crowd_density_global MESSAGE TO LINKSMART
    text, resp_code = forward_message(crowd_density_global, url)
    log_text = log_text + text
    return log_text, resp_code


def waste_time(time_amount):
    print('started')
    time.sleep(time_amount)
    print('finished')
    return 'Done'
