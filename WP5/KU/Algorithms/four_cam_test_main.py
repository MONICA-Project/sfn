# four_cam_test_main.py
"""A test application designed to mimic (badly) the VCA framework."""
import datetime
import json
import pickle
import cv2
from random import randrange
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
from WP5.KU.definitions import KU_DIR
from WP5.KU.SharedResources.frame_streamer import ImageSequenceStreamer
import WP5.KU.SharedResources.get_incrementer as inc
from WP5.KU.Algorithms.crowd_density_local.get_crowd import GetCrowd
from WP5.KU.Algorithms.flow_analysis.get_flow import GetFlow

__version__ = '0.1'
__author__ = 'Rob Dupre (KU)'


def dataset(index):
    dataset_folder = '/ocean/datasets/'

    return {
        # [Address, Stream, Settings File
        19: [(dataset_folder + '/MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_1/'), 0, 'RIF_CAM_1'],
        20: [(dataset_folder + '/MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_2/'), 0, 'RIF_CAM_2'],
        21: [(dataset_folder + '/MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_3/'), 0, 'RIF_CAM_3'],
        22: [(dataset_folder + '/MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_4/'), 0, 'RIF_CAM_4'],
        23: [(dataset_folder + '/MONICA/BONN/Rein in Flammen 2018/20180505_233000_camera_1/'), 0, 'RIF_CAM_1'],
        24: [(dataset_folder + '/MONICA/BONN/Rein in Flammen 2018/20180505_233000_camera_2/'), 0, 'RIF_CAM_2'],
        25: [(dataset_folder + '/MONICA/BONN/Rein in Flammen 2018/20180505_233000_camera_3/'), 0, 'RIF_CAM_3'],
        26: [(dataset_folder + '/MONICA/BONN/Rein in Flammen 2018/20180505_233000_camera_4/'), 0, 'RIF_CAM_4'],
    }.get(index, -1)  # -1 is default if id not found


def load_settings(location):
    fo = open((location + '.pk'), 'rb')
    entry = pickle.load(fo, encoding='latin1')
    return entry


display = True

# LOAD THE SETTINGS AND PASS THEN WHEN PROCESSING A FRAME
info1 = dataset(19)
settings1 = load_settings(KU_DIR + '/KUConfigTool/cam_configs/' + info1[2])
info2 = dataset(20)
settings2 = load_settings(KU_DIR + '/KUConfigTool/cam_configs/' + info2[2])
info3 = dataset(21)
settings3 = load_settings(KU_DIR + '/KUConfigTool/cam_configs/' + info3[2])
info4 = dataset(22)
settings4 = load_settings(KU_DIR + '/KUConfigTool/cam_configs/' + info4[2])
info5 = dataset(23)
settings5 = load_settings(KU_DIR + '/KUConfigTool/cam_configs/' + info5[2])
info6 = dataset(24)
settings6 = load_settings(KU_DIR + '/KUConfigTool/cam_configs/' + info6[2])
info7 = dataset(25)
settings7 = load_settings(KU_DIR + '/KUConfigTool/cam_configs/' + info7[2])
info8 = dataset(26)
settings8 = load_settings(KU_DIR + '/KUConfigTool/cam_configs/' + info8[2])

settings = [settings1, settings2, settings3, settings4, settings5, settings6, settings7, settings8]
info = [info1, info2, info3, info4, info5, info6, info7, info8]

# CREATE AN analyser OBJECT AND CREATE THE REGISTRATION MESSAGE
# analyser = GetCrowd('001')
analyser = GetFlow('001')

reg_message = analyser.create_reg_message(datetime.datetime.utcnow().isoformat())
with open(KU_DIR + '/Algorithms/registration_messages/' + analyser.module_id + '_' + analyser.type_module + '_reg.txt',
          'w') as outfile:
    outfile.write(reg_message)
reg_message = json.loads(reg_message)

cam1 = ImageSequenceStreamer(info1[0], info1[1], (1080, 768), loop_last=False, repeat=True)
cam2 = ImageSequenceStreamer(info2[0], info2[1], (1080, 768), loop_last=False, repeat=True)
cam3 = ImageSequenceStreamer(info3[0], info3[1], (1080, 768), loop_last=False, repeat=True)
cam4 = ImageSequenceStreamer(info4[0], info4[1], (1080, 768), loop_last=False, repeat=True)
cam5 = ImageSequenceStreamer(info5[0], info5[1], (1080, 768), loop_last=False, repeat=True)
cam6 = ImageSequenceStreamer(info6[0], info6[1], (1080, 768), loop_last=False, repeat=True)
cam7 = ImageSequenceStreamer(info7[0], info7[1], (1080, 768), loop_last=False, repeat=True)
cam8 = ImageSequenceStreamer(info8[0], info8[1], (1080, 768), loop_last=False, repeat=True)
cam = [cam1, cam2, cam3, cam4, cam5, cam6, cam7, cam8]

count = 0
while cam1.open() & cam2.open() & cam3.open() & cam4.open() & cam5.open() & cam6.open() & cam7.open() & cam8.open():

    # choose random camera
    random_index = randrange(0, len(cam))
    frame = cam[random_index].read()

    setting = settings[random_index]

    if analyser.type_module == 'flow':
        message, frame = analyser.process_frame(frame, settings['camera_id'], settings['flow_rois'], True)
    if analyser.type_module == 'object_detection':
        message, frame = analyser.process_frame(frame, settings['camera_id'])
    elif analyser.type_module == 'crowd_density_local':
        message, frame = analyser.process_frame(frame, settings['camera_id'], settings['crowd_mask'],
                                                settings['image_2_ground_plane_matrix'],
                                                settings['ground_plane_roi'],
                                                settings['ground_plane_size'], True)

    # WRITE FILES FOR USE LATER
    save_folder = str(Path(__file__).absolute().parents[0]) + '/algorithm_output/'
    if message:
        with open(save_folder + info[random_index][2] + '_' + reg_message['type_module'] + '_' +
                      str(inc.get_incrementer(count, 5)) + '.txt', 'w') as outfile:
            outfile.write(message)
        count = count + 1
        if display:
            key = cv2.waitKey(1) & 0xFF
            # KEYBINDINGS FOR DISPLAY
            cv2.imshow('frame', frame)
            if key == 27:  # exit
                break
