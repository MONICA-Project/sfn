"""
  A dummy task
"""
from time import sleep
import sys
import mmap
import numpy as np
import cv2
import json
import os
import uuid
import arrow
import socket
import pickle

# from flow_analysis.get_flow import GetFlow
from monica.WP5.KU.Algorithms.crowd_density_local.get_crowd import GetCrowd
from monica.WP5.KU.Algorithms.flow_analysis.get_flow import GetFlow

channel_set = set([])
channel_vector = []

crowd_density_analyzer = None
crowd_flow_analyzer = None

def get_internal_id(vca_channel_id):
    internal_channel_id = None

    for idx, channel in enumerate(channel_vector):
            if channel == vca_channel_id:
                internal_channel_id = idx

    return internal_channel_id

def get_current_directory():
    return os.path.dirname(__file__)

def work(width, height, buffer, seq_id, settings):
    global crowd_density_analyzer
    global crowd_flow_analyzer

    # sys.stderr.write("buf: %d == %d\n" % (len(buffer), width*height*3/2) )
    vec = np.frombuffer(buffer, dtype=np.uint8)
    mat = np.reshape(vec, (height + int(height/2), width))
    rgb = cv2.cvtColor(mat, cv2.COLOR_YUV2RGB_NV12, 3)

    if crowd_density_analyzer == None:
        crowd_density_analyzer = GetCrowd(str(uuid.uuid5(uuid.NAMESPACE_DNS, socket.gethostname() + 'crowd_density_local')))
        # crowd_density_analyzer.create_reg_message(arrow.utcnow())
    if crowd_flow_analyzer == None:
        crowd_flow_analyzer = GetFlow(str(uuid.uuid5(uuid.NAMESPACE_DNS, socket.gethostname() + 'flow')))
        # crowd_flow_analyzer.create_reg_message(arrow.utcnow())

    final_message = ''
    seq_id = str(seq_id)
    if seq_id in settings.keys():
        camera_settings = settings[seq_id]
        message, density_map = crowd_density_analyzer.process_frame(rgb, camera_settings['camera_id'],camera_settings['crowd_mask'],camera_settings['image_2_ground_plane_matrix'],camera_settings['ground_plane_roi'],camera_settings['ground_plane_size'])
        final_message += str(message) + '|'
        message, density_map = crowd_flow_analyzer.process_frame(rgb, camera_settings['camera_id'],camera_settings['flow_rois'])
        final_message += str(message)
        sys.stdout.write(str(final_message) + '\n')
    else:
        # sys.stderr.write("WARNING: No settings file for channel" + str(seq_id) + "\n")
        sys.stdout.write('None\n')
    # cv2.imshow('bw', rgb)
    # cv2.waitKey(5)
    # Simulate doing something with the image (5 fps = 0.2s processing)

if __name__ == '__main__':
    settings_file_path = os.path.join(get_current_directory(), 'settings.json')
    settings_data = json.loads(open(settings_file_path, 'r').read())

    for key in settings_data.keys():
        fo = open(os.path.join(get_current_directory(), settings_data[key]['calibration_file']), 'rb')
        data = pickle.load(fo, encoding='latin1')
        # data = json.loads(open(os.path.join(get_current_directory(), settings_data[key]['calibration_file']), 'r').readline())
        settings_data[key] = data

    fd = open(sys.argv[3], 'rb')
    data = mmap.mmap(fd.fileno(), 0, access=mmap.ACCESS_READ)
    # init here.
    # k = ku.init())
    for line in sys.stdin.buffer:
        line = line.decode('utf-8')
        channel_id = json.loads(line)['channel_id']
        if 'stop' in str(line):
            break
        work(int(sys.argv[1]), int(sys.argv[2]), data, channel_id, settings_data)
