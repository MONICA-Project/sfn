# message_processing.py
"""Functions to process the incoming messages to the SFN"""
import json
import requests
import time

__version__ = '0.3'
__author__ = 'RoViT (KU)'


def crowd_density_local(sfn_instance, camera_id, url, message):
    """ Message process function to be used when messages of type crowd_density_local are sent to the sfn_service.
        Convert to top down, save in db and forward on message
        Keyword arguments:
            sfn_instance --     The instance of the SFN module, handling all database interactions
            camera_id --        Used to pull back the correct config data from the SFN database
            url --              The url to forward the message to once processing has been completed
            message --          The original decoded JSON message in Dictionary form
            j_id --             A Unique identifier serving as a primary key in the log db
        Returns:
            log_text --         A trace text outlining the path the message has taken
            resp_code --        A code which can be used in the SFN_Service response
        """
    log_text = ''
    # start = time.time()
    # REMOVE THE FRAME AND IMAGE SIZE AS ITS NOT NEEDED
    message['frame_byte_array'] = ''
    message['image_dims'] = ''
    # SAVE TO THE DATABASE OF MESSAGES AND FORWARD THE NEW MESSAGE
    log_text = log_text + sfn_instance.insert_db(camera_id, 'crowd_density_local', json.dumps(message))
    text, resp_code = forward_message(json.dumps(message), url)
    log_text = log_text + text
    # LOG THE OUTPUT OF THIS MESSAGE OPERATION
    sfn_instance.insert_log(time.time(), message['timestamp_1'], log_text)
    # print('Function has taken: {}s'.format(time.time() - start))
    return log_text, resp_code


def flow_analysis(sfn_instance, camera_id, url, message):
    """ Message process function to be used when messages of type flow_analysis are sent to the sfn_service
        Keyword arguments:
            sfn_instance --     The instance of the SFN module, handling all database interactions
            camera_id --        Used to pull back the correct config data from the SFN database
            url --              The url to forward the message to once processing has been completed
            message --          The original decoded JSON message in Dictionary form
            j_id --             A Unique identifier serving as a primary key in the log db
        Returns:
            log_text --         A trace text outlining the path the message has taken
            resp_code --        A code which can be used in the SFN_Service response
        """
    log_text = ''
    # start = time.time()
    # FORWARD THE NEW MESSAGE

    if camera_id is not '':
        text, resp_code = forward_message(json.dumps(message), url)
        log_text = log_text + text
        # LOG THE OUTPUT OF THIS MESSAGE OPERATION
        if sfn_instance.flow_save:
            log_text = log_text + sfn_instance.insert_db(camera_id, 'flow_analysis', json.dumps(message))
        if sfn_instance.logging:
            sfn_instance.insert_log(time.time(), message['timestamp'], log_text)
        # print('Function has taken: {}s'.format(time.time() - start))
    else:
        log_text = log_text + 'THIS IS THE FIRST flow MESSAGE AND IS THEREFORE BLANK.'
        if sfn_instance.logging:
            sfn_instance.insert_log(time.time(), message['timestamp'], log_text)
        resp_code = 200
    return log_text, resp_code


def fighting_detection(sfn_instance, camera_id, url, message):
    """ Message process function to be used when messages of type fighting_detection are sent to the sfn_service
        Keyword arguments:
            sfn_instance --     The instance of the SFN module, handling all database interactions
            camera_id --        Used to pull back the correct config data from the SFN database
            url --              The url to forward the message to once processing has been completed
            message --          The original decoded JSON message in Dictionary form
            j_id --             A Unique identifier serving as a primary key in the log db
        Returns:
            log_text --         A trace text outlining the path the message has taken
            resp_code --        A code which can be used in the SFN_Service response
        """
    log_text = ''
    # start = time.time()
    # FORWARD THE NEW MESSAGE
    text, resp_code = forward_message(json.dumps(message), url)
    log_text = log_text + text
    # LOG THE OUTPUT OF THIS MESSAGE OPERATION

    if sfn_instance.fight_save:
        log_text = log_text + sfn_instance.insert_db(camera_id, 'fighting_detection', json.dumps(message))
    if sfn_instance.logging:
        sfn_instance.insert_log(time.time(), message['timestamp'], log_text)
    # print('Function has taken: {}s'.format(time.time() - start))
    return log_text, resp_code


def object_detection(sfn_instance, camera_id, url, message):
    """ Message process function to be used when messages of type object_detection are sent to the sfn_service
        Keyword arguments:
            sfn_instance --     The instance of the SFN module, handling all database interactions
            camera_id --        Used to pull back the correct config data from the SFN database
            url --              The url to forward the message to once processing has been completed
            message --          The original decoded JSON message in Dictionary form
            j_id --             A Unique identifier serving as a primary key in the log db
        Returns:
            log_text --         A trace text outlining the path the message has taken
            resp_code --        A code which can be used in the SFN_Service response
        """
    log_text = ''
    # start = time.time()
    # FORWARD THE NEW MESSAGE
    text, resp_code = forward_message(json.dumps(message), url)
    log_text = log_text + text
    # LOG THE OUTPUT OF THIS MESSAGE OPERATION
    if sfn_instance.object_save:
        log_text = log_text + sfn_instance.insert_db(camera_id, 'object_detection', json.dumps(message))
    if sfn_instance.logging:
        sfn_instance.insert_log(time.time(), message['timestamp'], log_text)
    # print('Function has taken: {}s'.format(time.time() - start))
    return log_text, resp_code


def action_recognition(sfn_instance, camera_id, url, message):
    """ Message process function to be used when messages of type action_recognition are sent to the sfn_service
        Keyword arguments:
            sfn_instance --     The instance of the SFN module, handling all database interactions
            camera_id --        Used to pull back the correct config data from the SFN database
            url --              The url to forward the message to once processing has been completed
            message --          The original decoded JSON message in Dictionary form
            j_id --             A Unique identifier serving as a primary key in the log db
        Returns:
            log_text --         A trace text outlining the path the message has taken
            resp_code --        A code which can be used in the SFN_Service response
        """
    log_text = ''
    # start = time.time()
    # FORWARD THE NEW MESSAGE
    text, resp_code = forward_message(json.dumps(message), url)
    log_text = log_text + text
    # LOG THE OUTPUT OF THIS MESSAGE OPERATION
    if sfn_instance.object_save:
        log_text = log_text + sfn_instance.insert_db(camera_id, 'action_recognition', json.dumps(message))
    if sfn_instance.logging:
        sfn_instance.insert_log(time.time(), message['timestamp'], log_text)
    # print('Function has taken: {}s'.format(time.time() - start))
    return log_text, resp_code


def forward_message(message, url):
    try:
        resp = requests.put(url, data=message, headers={'content-Type': 'application/json'})
    except requests.exceptions.RequestException as e:
        print(e)
        return 'Connection Failed: ' + str(e), 450
    else:
        print('RESPONSE: ' + resp.text + str(resp.status_code))
        return 'MESSAGE FORWARDED (' + resp.text + str(resp.status_code) + '). ', resp.status_code


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
    recent_cam_messages = sfn_module.query_db(None, None, 'crowd_density_local')  # Search for a specific module_id
    recent_cam_messages = [json.loads(item.msg) for item in recent_cam_messages]

    # GET ONLY CAMERAS CONFIGS
    configs = sfn_module.query_config_db(None)
    configs = [json.loads(config.msg) for config in configs]
    config = None

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

        for c in configs:
            if 'camera_id' in c:
                if c['camera_id'] == recent_cam_messages[i]['camera_ids'][0]:
                    config = c
                    break

        if config is not None:
            config_for_amalgamation.append(config['ground_plane_position'] + [config['camera_bearing']])
        else:
            print('ERROR: NO CONFIG WAS RETURNED LOOKING FOR {}. '.format(recent_cam_messages[i]['camera_ids'][0]))
            log_text = log_text + 'ERROR: NONE OR MORE THAN ONE CONFIG WAS RETURNED, BREAKING OUT OF AMALGAMATION. '

    # RUN THE AMALGAMATION
    if len(recent_cam_messages) == len(config_for_amalgamation):
        amalgamated_top_down_map, amalgamation_ground_plane_position = sfn_module.generate_amalgamated_top_down_map(
            top_down_maps, config_for_amalgamation, amalgamation_density_count)
        log_text = log_text + 'CURRENTLY HELD MESSAGES HAVE BEEN AMALGAMATED INTO THE crowd_density_global VIEW. '
        # Create new message
        crowd_density_global = sfn_module.create_obs_message(amalgamation_cam_ids, amalgamation_density_count,
                                                             amalgamated_top_down_map, amalgamation_timestamp_1,
                                                             amalgamation_timestamp_2,
                                                             amalgamation_ground_plane_position)

        log_text = log_text + 'crowd_density_global MESSAGE CREATED. '

        # SEND crowd_density_global MESSAGE TO LINKSMART
        log_text = log_text + sfn_instance.insert_db('GLOBAL', 'crowd_density_global', json.dumps(crowd_density_global))
        text, resp_code = forward_message(crowd_density_global, url)
        log_text = log_text + text

        # sfn_module.debug = True
        if sfn_module.debug:
            sfn_module.dump_amalgamation_data()
            log_text = log_text + 'DEBUGGING IS ENABLES SO A DATABASE DUMP HAS BEEN DONE. '

    else:
        print('ERROR: NOT EQUAL CAM MESSAGES AND CONFIGS. ')
        resp_code = 500
        log_text = log_text + 'ERROR: NOT EQUAL CAM MESSAGES AND CONFIGS. '

    sfn_instance.insert_log(time.time(), time.time(), log_text)
    return log_text, resp_code


def waste_time(time_amount):
    print('started')
    time.sleep(time_amount)
    print('finished')
    return 'Done'
