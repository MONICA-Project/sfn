# message_processing.py
"""Functions to process the incoming messages to the SFN"""

import numpy as np
import cv2
import json
import requests
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
    # GET THE CONFIG WITH MATCHING camera_id
    config = sfn_instance.query_config_db(camera_id)
    if len(config) == 1:
        config = json.loads(config[0][1])
        # CONVERT TO TOP DOWN
        # TODO: SORT OUT THE IMAGE SIZES
        message['density_map'], heat_image = generate_heat_map(
            message['density_map'], config['image_2_ground_plane_matrix'], config['ground_plane_roi'],
            config['ground_plane_size'], timestamp=message['timestamp_1'],
            frame=tools.decode_image(message['frame_byte_array'], message['image_dims'], False)
        )
        # REMOVE THE FRAME AND IMAGE SIZE AS ITS NOT NEEDED
        message['frame_byte_array'] = ''
        message['image_dims'] = ''
        log_text = log_text + 'crowd_density_local MESSAGE CONVERTED TO TOP DOWN. '
        # SAVE TO THE DATABASE OF MESSAGES AND FORWARD THE NEW MESSAGE
        log_text = log_text + sfn_instance.insert_db(camera_id, 'crowd_density_local', json.dumps(message))
        text, resp_code = forward_message(json.dumps(message), url)
        log_text = log_text + text
    else:
        log_text = log_text + 'EITHER NO CONFIG WAS FOUND OR > 1 WAS LOCATED AND CONFUSED THINGS. '
    # LOG THE OUTPUT OF THIS MESSAGE OPERATION
    sfn_instance.insert_log(j_id, message['timestamp_1'], log_text)
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


def generate_heat_map(detections, transform, gp_roi, ground_plane_size, frame=None, timestamp=None):
    """ Converts a heat map or list of detections from the image plane to a top down view, through the use of a pre-
    defined transformation
        Keyword arguments:
            detections --       Either a list of X, Y locations or an 1-D image where each pixel intensity correlates to
                                to the number of detections in that region
            transform --        Pre defined transformation matrix used to convert from image plane to top down
            gp_roi --           List[x1, y1, x2, y2] integers, defining 2 points used to specify a section of the top
                                down image that will be returned.
            ground_plane_size --List[size_X, size_Y] in meters represented by the gp_roi
            frame --            [OPTIONAL] the original frame on which the detections are based, used for debugging
            timestamp --        [OPTIONAL/required if frame is present] Time stamp of when the original detections were
                                made, used to label the saved debugging image.
        Returns:
            heat_map --         The top down heatmap, of size ground_plane_size, representing the 2-D histogram of
                                detection volume
            heat_image --       Overlay of the heat_map over the warped frame
        """
    detections = np.array(detections)
    # detections IS EITHER AN (MxN) IMAGE OR A (Mx2) LIST OF X Y COORDINATES
    if detections.shape[1] > 2:
        # CONVERT TO LIST OF POINTS
        detections_image = detections.copy()
        values = detections_image[detections_image > 0]
        detections = np.array(np.nonzero(detections_image > 0))
        detections = np.transpose(np.vstack([detections[1, :], detections[0, :]]))
    else:
        # ELSE CREATE VALUES FOR INDIVIDUAL DETECTIONS
        values = np.ones(len(detections))

    # TRANSFORM THE LIST OF DETECTIONS
    q = np.dot(transform, np.transpose(np.hstack([detections, np.ones([len(detections), 1])])))
    p = np.array(q[2, :])
    transformed_pts = np.int32(np.round(np.vstack([(q[0, :] / p), (q[1, :] / p)])))
    transformed_pts = np.vstack([transformed_pts, values])

    # import datetime
    # start = datetime.datetime.now()

    # FOR EACH DETECTION CHECK IT IS WITHIN THE gp_roi AND BIN
    x = transformed_pts[0, :]
    transformed_pts = transformed_pts[:, (gp_roi[0] < x) & (x < gp_roi[2])]
    y = transformed_pts[1, :]
    transformed_pts = transformed_pts[:, (gp_roi[1] < y) & (y < gp_roi[3])]

    # print(datetime.datetime.now() - start)
    # CREATE THE HEAT MAP, USING THE transformed_pts, USING THE NUMBER OF BINS DEFINED IN ground_plane_size,
    # WHERE WEIGHTS ARE THE AMOUNT ADDED TO EACH BIN FOR EACH POINT AND APPLYING THE RANGE GIVEN BY gp_roi
    heat_map, _, _ = np.histogram2d(transformed_pts[1, :], transformed_pts[0, :], bins=ground_plane_size[::-1],
                                    weights=transformed_pts[2, :],
                                    range=[[gp_roi[1], gp_roi[3]], [gp_roi[0], gp_roi[2]]])

    heat_image = None
    # IF A FRAME IS PROVIDED GET THE HEAT MAP OVERLAID
    if frame is not None:
        transform = np.array(transform)
        warped_image = cv2.warpPerspective(frame, transform, (10000, 10000))

        # CHANGE TO GRAY SCALE AND GET ONLY THE roi FOR THE WARPED IMAGE
        if np.ndim(frame) > 2:
            warped_image = cv2.cvtColor(warped_image[gp_roi[1]: gp_roi[3], gp_roi[0]: gp_roi[2]],
                                        cv2.COLOR_RGB2GRAY)
        else:
            warped_image = warped_image[gp_roi[1]: gp_roi[3], gp_roi[0]: gp_roi[2]]
        # SCALE UP THE heat_map TO ENCOMPASS THE WHOLE WARPED roi
        heat_image = cv2.resize(heat_map, (gp_roi[2] - gp_roi[0], gp_roi[3] - gp_roi[1]))
        heat_image = ((warped_image / 255) / 3) + heat_image
        # SAVE THE IMAGE (NORMALISE UP TO 255)
        cv2.imwrite('Detections_' + str(timestamp) + '.jpeg', heat_image*255)
        # cv2.imshow('frame', heat_image)
        # cv2.waitKey(0)
    return heat_map.tolist(), heat_image


# TODO: LOOK INTO CHANGING THE DENSITY MAP (WHICH IS MASSIVE) TO A SCALED IMAGE AND JUST HAVING THE HEAT MAP AS RELATIVE
# TO THE NUMBER OF PEOPLE NOT ACTUALLY HOW MANY ARE IN EACH AREA.
def generate_heat_map2(density_map, transform, gp_roi, ground_plane_size, frame=None, timestamp=None):
    """ Converts a heat map or list of detections from the image plane to a top down view, through the use of a pre-
    defined transformation
        Keyword arguments:
            density_map --      Either a list of X, Y locations or an 1-D image where each pixel intensity correlates to
                                to the number of detections in that region
            transform --        Pre defined transformation matrix used to convert from image plane to top down
            gp_roi --           List[x1, y1, x2, y2] integers, defining 2 points used to specify a section of the top
                                down image that will be returned.
            ground_plane_size --List[size_X, size_Y] in meters represented by the gp_roi
            frame --            [OPTIONAL] the original frame on which the detections are based, used for debugging
            timestamp --        [OPTIONAL/required if frame is present] Time stamp of when the original detections were
                                made, used to label the saved debugging image.
        Returns:
            heat_map --         The top down heatmap, of size ground_plane_size, representing the 2-D histogram of
                                detection volume
            heat_image --       Overlay of the heat_map over the warped frame
        """

    density_map = cv2.resize(density_map, (0, 0), fx=4, fy=4)
    transform = np.array(transform)
    warped_dm = cv2.warpPerspective(density_map, transform, (10000, 10000))
    warped_dm = warped_dm[gp_roi[1]: gp_roi[3], gp_roi[0]: gp_roi[2]]

    detections_image = warped_dm.copy()
    values = detections_image[detections_image > 0]
    detections = np.array(np.nonzero(detections_image > 0))
    detections = np.transpose(np.vstack([detections[1, :], detections[0, :]]))

    # print(datetime.datetime.now() - start)
    # CREATE THE HEAT MAP, USING THE transformed_pts, USING THE NUMBER OF BINS DEFINED IN ground_plane_size,
    # WHERE WEIGHTS ARE THE AMOUNT ADDED TO EACH BIN FOR EACH POINT AND APPLYING THE RANGE GIVEN BY gp_roi
    heat_map, _, _ = np.histogram2d(detections[1, :], detections[0, :], bins=ground_plane_size[::-1],
                                    weights=detections[2, :],
                                    range=[[gp_roi[1], gp_roi[3]], [gp_roi[0], gp_roi[2]]])

    heat_image = None
    # IF A FRAME IS PROVIDED GET THE HEAT MAP OVERLAID
    if frame is not None:
        transform = np.array(transform)
        warped_image = cv2.warpPerspective(frame, transform, (10000, 10000))

        # CHANGE TO GRAY SCALE AND GET ONLY THE roi FOR THE WARPED IMAGE
        if np.ndim(frame) > 2:
            warped_image = cv2.cvtColor(warped_image[gp_roi[1]: gp_roi[3], gp_roi[0]: gp_roi[2]],
                                        cv2.COLOR_RGB2GRAY)
        else:
            warped_image = warped_image[gp_roi[1]: gp_roi[3], gp_roi[0]: gp_roi[2]]
        # SCALE UP THE heat_map TO ENCOMPASS THE WHOLE WARPED roi
        heat_image = cv2.resize(heat_map, (gp_roi[2] - gp_roi[0], gp_roi[3] - gp_roi[1]))
        heat_image = ((warped_image / 255) / 3) + heat_image
        # SAVE THE IMAGE (NORMALISE UP TO 255)
        cv2.imwrite('Detections_' + str(timestamp) + '.jpeg', heat_image*255)
        # cv2.imshow('frame', heat_image)
        # cv2.waitKey(0)
    return heat_map.tolist(), heat_image


def waste_time(time_amount):
    print('started')
    time.sleep(time_amount)
    print('finished')
    return 'Done'
