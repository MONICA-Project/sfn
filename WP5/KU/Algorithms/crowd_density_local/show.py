import sys, os
import numpy as np
import cv2 as cv
import glob
import json
import pickle


class Frame:
    pass

def show(camera_id = None):
    if camera_id is not None:
        print("Loading frames only for camera: ", camera_id)

    script_path = os.path.dirname(sys.argv[0])
    files = glob.glob('*_frame.jpeg')
    files.sort(reverse=True)

    # Load image and messages
    frames = []
    for file in files:
        # print(file)
        base_name,_ = os.path.splitext(file)
        base_name = '_'.join(base_name.split('_')[:-1])

        frame = Frame()
        frame.frame_file = base_name+'_frame.jpeg' 
        frame.density_file = base_name+'_density.jpeg' 
        frame.count_file = base_name+'.txt' 

        count_msg = json.load(open(frame.count_file, 'rt'))
        frame.count = count_msg['density_count'] 
        frame.camera = count_msg['camera_ids'][0] 
        frame.time = count_msg['timestamp_1']

        if camera_id == None or camera_id.upper() == frame.camera.upper():
            frames.append(frame)
        
    print("Loaded images:", len(frames))

    # Show images and densities
    frame_id = 0
    configs = {}
    while True:
        frame = frames[frame_id]
        if frame.camera not in configs:
            cfg_path = os.path.join(script_path, '../../KUConfigTool/cam_configs/'+frame.camera.upper()+'.pk')
            cfg = pickle.load(open(cfg_path, 'rb'), encoding='latin1')
            configs[frame.camera] = cfg

        cfg = configs[frame.camera]
        gp_size = cfg['ground_plane_size']
        gp_roi = cfg['ground_plane_roi']
        M = cfg['image_2_ground_plane_matrix']

        frame_img = cv.imread(frame.frame_file)
        frame_img = cv.cvtColor(frame_img, cv.COLOR_BGR2RGB)
        density_img = cv.imread(frame.density_file)
        density_img = cv.applyColorMap(density_img, cv.COLORMAP_HOT)
        alpha = 0.3
        img_with_densities = cv.addWeighted(frame_img, alpha, density_img, 1-alpha, gamma=0) 
        cv.imshow('Crowd Density', img_with_densities)
        print(frame_id,': ',frame.count,'   ',frame.time, '  ', frame.camera, '  ', frame.frame_file)

        key = cv.waitKey(0) & 0xFF
        if key == 27: break
        if key == ord('k'): frame_id-=1
        if key == ord('j'): frame_id+=1
        if frame_id < 0: frame_id = 0
        if frame_id == len(frames): frame_id = len(frames)-1

if __name__ == "__main__":
    camera_id = sys.argv[1] if len(sys.argv)>1 else None
    show(camera_id)
