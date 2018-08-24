import os
import cv2
import arrow
import WP5.KU.SharedResources.loader_tools as tools
import WP5.KU.SharedResources.get_incrementer as inc
from WP5.KU.Algorithms.crowd_density_local.get_crowd import GetCrowd
import time
import numpy as np
import json

font = cv2.FONT_HERSHEY_SIMPLEX
blk = (0, 0, 0)
wht = (255, 255, 255)
# LOAD THE IMAGES AND CREATE ANNOTATED VERSIONS
dataset_folder = '/ocean/datasets/MONICA/YCCC-LR/LEEDS_2018_AUG/'
folder_location = dataset_folder + 'ORIGINAL_IMAGES/'
# folder_location = dataset_folder + 'EVAL/'
save_folder = dataset_folder + 'EVAL/'
renaming = False
evaluating = True

# GET LIST OF MESSAGES AT FILE LOCATION
messages = []
for f in sorted(os.listdir(folder_location)):
    ext = os.path.splitext(f)[1]
    if ext.lower().endswith('.txt'):
        messages.append(os.path.join(folder_location, f))

if evaluating:
    analyser = GetCrowd('001')

    for i in messages:
        file_name = os.path.splitext(i)[0]
        message = tools.load_json_txt(location=i)
        f = cv2.imread(file_name + '_frame.jpeg')
        frame = cv2.imread(file_name + '_frame.jpeg')
        # density = cv2.imread(file_name + '_density.jpeg')

        # settings_location = dataset_folder + 'CONFIG/ORIGINAL/'
        # config = tools.load_settings(settings_location, message['camera_ids'][0])
        # cv2.rectangle(f, (5, 5), (375, 60), blk, -1)
        # cv2.putText(f, 'Camera Name: {}'.format(message['camera_ids'][0]), (5, 20), font, 0.5, wht, 1, cv2.LINE_AA)
        # cv2.putText(f, 'Number of People: {}'.format(message['density_count']), (5, 35), font, 0.5, wht, 1, cv2.LINE_AA)
        # cv2.putText(f, 'Time: {}'.format(message['timestamp_1']), (5, 50), font, 0.5, wht, 1, cv2.LINE_AA)
        #
        # roi = config['frame_roi']
        # cv2.rectangle(f, (roi[0], roi[1]), (roi[2], roi[3]), (0, 0, 255), 2)
        # key = cv2.waitKey(1) & 0xFF
        # cv2.imshow('frame', frame)
        # cv2.imwrite(os.path.join(save_folder, os.path.split(file_name)[1] + '_frame.jpeg'), f)

        settings_location = dataset_folder + 'CONFIG/'
        config = tools.load_settings(settings_location, message['camera_ids'][0])
        message, result = analyser.process_frame(frame, config['camera_id'], config['crowd_mask'],
                                                 config['image_2_ground_plane_matrix'],
                                                 config['ground_plane_roi'],
                                                 config['ground_plane_size'])
        message = json.loads(message)
        mask = cv2.resize(np.array(config['crowd_mask']), (frame.shape[1], frame.shape[0]))
        mask[mask > 0] = 1

        t_frame = (frame * ((np.dstack((mask, mask, mask)) + 1) * 0.5)).astype(np.uint8)
        cv2.rectangle(t_frame, (5, 5), (375, 60), blk, -1)
        cv2.putText(t_frame, 'Camera Name: {}'.format(message['camera_ids'][0]), (5, 20), font, 0.5, wht, 1, cv2.LINE_AA)
        cv2.putText(t_frame, 'Number of People: {}'.format(message['density_count']), (5, 35), font, 0.5, wht, 1, cv2.LINE_AA)
        cv2.putText(t_frame, 'Time: {}'.format(message['timestamp_1']), (5, 50), font, 0.5, wht, 1, cv2.LINE_AA)
        # disp_frame = np.zeros((t_frame.shape[0], t_frame.shape[1] * 2, 3))
        # disp_frame[:, 0:t_frame.shape[1], :] = t_frame
        # disp_frame[:, t_frame.shape[1]:, :] = np.dstack((result, result, result))
        # disp_frame = disp_frame.astype(np.uint8)
        # key = cv2.waitKey(1) & 0xFF
        # cv2.imshow('frame', t_frame)
        cv2.imwrite(os.path.join(save_folder, os.path.split(file_name)[1] + '_updated_frameB.jpeg'), t_frame)


# RENAMING FILES IF RESTARTS HAVE HAPPENED DURING THE EVENT
if renaming:
    timestamps = []
    for i in messages:
        file_name = os.path.splitext(i)[0]
        message = tools.load_json_txt(location=i)
        frame = cv2.imread(file_name + '_frame.jpeg')
        density = cv2.imread(file_name + '_density.jpeg')
        timestamps.append([arrow.get(message['timestamp_1']), message, frame, density])

    folder_location = dataset_folder + 'ORIGINAL_IMAGES/'
    timestamps = sorted(timestamps, key=lambda x: x[0])
    for i, contents in enumerate(timestamps):
        mes = contents[1]
        fra = contents[2]
        den = contents[3]
        save_name = inc.get_incrementer(i, 7) + '_' + mes['camera_ids'][0] + '_' + mes['module_id']
        tools.save_json_txt(mes, folder_location, save_name)
        cv2.imwrite(os.path.join(folder_location, save_name + '_frame.jpeg'), fra)
        cv2.imwrite(os.path.join(folder_location, save_name + '_density.jpeg'), den)