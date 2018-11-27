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
dataset_folder = '/ocean/datasets/MONICA/TO/MOVIDA_2018/'
folder_location = dataset_folder + 'ORIGINAL_IMAGES/'
settings_folder = '/ocean/robdupre/PYTHON_SCRIPTS/MONICA_repo/WP5/KU/KUConfigTool/cam_configs/'
save_folder = dataset_folder + 'EVAL/'
renaming = False
evaluating = False
visualise = True


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
        # key = cv2.waitKey(1) & 0xFF
        # cv2.imshow('frame', frame)
        # cv2.imwrite(os.path.join(save_folder, os.path.split(file_name)[1] + '_frame.jpeg'), f)

        config = tools.load_settings(settings_folder, message['camera_ids'][0])
        # message, result = analyser.process_frame(frame, config['camera_id'], config['crowd_mask'],
        #                                          config['image_2_ground_plane_matrix'],
        #                                          config['ground_plane_roi'],
        #                                          config['ground_plane_size'])
        # message = json.loads(message)
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


if visualise:
    for i in messages:
        file_name = os.path.splitext(i)[0]
        message = tools.load_json_txt(location=i)
        config = tools.load_settings(settings_folder, message['camera_ids'][0])
        if message['type_module'] == 'flow':
            frame = cv2.imread(file_name + '_frame.jpeg')
            frame2 = cv2.imread(file_name + '_frame2.jpeg')
            flow = cv2.imread(file_name + '.jpeg')
        else:
            frame = cv2.imread(file_name + '_frame.jpeg')
            density = cv2.imread(file_name + '.jpeg')
            mask = cv2.resize(np.array(config['crowd_mask']), (frame.shape[1], frame.shape[0]))
            mask[mask > 0] = 1
            t_frame = (frame * ((np.dstack((mask, mask, mask)) + 1) * 0.5)).astype(np.uint8)

            # CREATE A SIDE BY SIDE VIEW WITH THE DENSITY
            display_frame = np.zeros((t_frame.shape[0], t_frame.shape[1] * 2, 3))
            display_frame[:, 0:t_frame.shape[1], :] = t_frame
            display_frame[:, t_frame.shape[1]:, :] = density
            display_frame = display_frame.astype(np.uint8)
            cv2.rectangle(display_frame, (5, 5), (375, 60), blk, -1)
            cv2.putText(display_frame, 'Camera Name: {}'.format(message['camera_ids'][0]), (5, 20), font, 0.5, wht,
                        1, cv2.LINE_AA)
            cv2.putText(display_frame, 'Number of People: {}'.format(message['density_count']), (5, 35), font, 0.5, wht,
                        1, cv2.LINE_AA)
            cv2.putText(display_frame, 'Time: {}'.format(message['timestamp_1']), (5, 50), font, 0.5, wht,
                        1, cv2.LINE_AA)
            cv2.imwrite(os.path.join(save_folder, os.path.split(file_name)[1] + '_double.jpeg'), display_frame)

            # OVERLAY THE DENSITY ON TOP OF THE ORIGINAL
            # t_frame[:, :, 0] = t_frame[:, :, 0] + density[:, :, 0]
            # t_frame[:, :, 1] = t_frame[:, :, 1] + density[:, :, 1]
            # t_frame[:, :, 2] = t_frame[:, :, 2] + density[:, :, 2]
            # cv2.rectangle(t_frame, (5, 5), (375, 60), blk, -1)
            # cv2.putText(t_frame, 'Camera Name: {}'.format(message['camera_ids'][0]), (5, 20), font, 0.5, wht,
            # 1, cv2.LINE_AA)
            # cv2.putText(t_frame, 'Number of People: {}'.format(message['density_count']), (5, 35), font, 0.5, wht,
            # 1, cv2.LINE_AA)
            # cv2.putText(t_frame, 'Time: {}'.format(message['timestamp_1']), (5, 50), font, 0.5, wht,
            # 1, cv2.LINE_AA)
            # key = cv2.waitKey(1) & 0xFF
            # cv2.imshow('frame', t_frame)
            # cv2.imwrite(os.path.join(save_folder, os.path.split(file_name)[1] + '_overlay.jpeg'), t_frame)


# RENAMING FILES IF RESTARTS HAVE HAPPENED DURING THE EVENT
if renaming:
    timestamps = []
    for i in messages:
        file_name = os.path.splitext(i)[0]
        message = tools.load_json_txt(location=i)
        if message['type_module'] == 'flow':
            frame = cv2.imread(file_name + '_frame1.jpeg')
            frame2 = cv2.imread(file_name + '_frame2.jpeg')
            flow = cv2.imread(file_name + '_flow.jpeg')
            timestamps.append([arrow.get(message['timestamp']), message, frame, frame2, flow])
        else:
            frame = cv2.imread(file_name + '_frame.jpeg')
            density = cv2.imread(file_name + '_density.jpeg')
            timestamps.append([arrow.get(message['timestamp_1']), message, frame, density])

    folder_location = dataset_folder + 'ORIGINAL_IMAGES2/'
    timestamps = sorted(timestamps, key=lambda x: x[0])
    counter = 0
    for i, contents in enumerate(timestamps):
        mes = contents[1]
        fra = contents[2]

        save_name = '{}_{}_{}'.format(contents[0].to('GMT').timestamp, mes['camera_ids'][0], mes['type_module'])
        tools.save_json_txt(mes, folder_location, save_name)
        counter = counter + 1
        cv2.imwrite(os.path.join(folder_location, save_name + '_frame.jpeg'), fra)
        counter = counter + 1
        if mes['type_module'] == 'flow':
            cv2.imwrite(os.path.join(folder_location, save_name + '_frame2.jpeg'), contents[3])
            counter = counter + 1
            cv2.imwrite(os.path.join(folder_location, save_name + ' .jpeg'), contents[4])
            counter = counter + 1
        else:
            cv2.imwrite(os.path.join(folder_location, save_name + '.jpeg'), contents[3])
            counter = counter + 1

    print(counter)
