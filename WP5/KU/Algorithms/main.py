# frame_streamer.py
import cv2
import json
import get_incrementer as inc
from cam_video_streamer import CamVideoStreamer
from frame_streamer import ImageSequenceStreamer
from get_people import GetPeople
from get_crowd import GetCrowd
import time
import datetime
import requests


def dataset(index):
    dataset_folder = 'C:/Users/Rob/Desktop/CROWD_DATASETS/'
    dataset_folder = '/ocean/datasets/'

    return {
        # [Address, Stream, Settings File]
        0: ['rtsp://root:pass@10.144.129.107/axis-media/media.amp', 'Live', 'CAMERA_KU'],
        # [Location, Image Type, Start Frame, Settings File]
        1: [(dataset_folder + 'UCSD_Anomaly/UCSDped1/Train/Train001/'), 0],
        2: [(dataset_folder + 'Mall_Dataset/frames/'), 0],
        3: [(dataset_folder + 'EWAP_Dataset/seq_eth/'), 0],
        4: [(dataset_folder + 'EWAP_Dataset/seq_hotel/'), 0],
        5: [(dataset_folder + 'YOUTUBE/TIMES_SQUARE/'), 0],
        6: [(dataset_folder + 'YOUTUBE/DELHI_CROWD/'), 0],
        7: [(dataset_folder + 'KU_Courtyard_Dataset/20130805_140532_52EB_00408CDCC71E/'), 50],
        8: [(dataset_folder + 'KU_LAB/Output_1/'), 15],
        9: [(dataset_folder + 'OXFORD_TOWNCENTRE/TownCentreXVID/'), 1, 2000],
        10: [(dataset_folder + 'MONICA/TO/KFF 2017/channel 2/2017-07-09 19-40-00~19-50-00/'), 0, 'KFF_CAM_2'],
        11: [(dataset_folder + 'MONICA/TO/KFF 2017/channel 4/2017-07-08 14-00-00~14-10-00/'), 0, 'KFF_CAM_4'],
        12: [(dataset_folder + 'MONICA/TO/KFF 2017/channel 8/2017-07-08 20-40-00~20-50-00/'), 0, 'KFF_CAM_8'],
        13: [(dataset_folder + '/MONICA/SAMPLE_VIDEOS/KFF/'), 0],
        14: [(dataset_folder + '/MONICA/SAMPLE_VIDEOS/LED/'), 0],
        15: [(dataset_folder + '/MONICA/SAMPLE_VIDEOS/DOM/'), 0],
        16: [(dataset_folder + '/MONICA/SAMPLE_VIDEOS/MRK_1/'), 0],
        17: [(dataset_folder + '/MONICA/SAMPLE_VIDEOS/MRK_2/'), 0],
        18: [(dataset_folder + '/Temp/'), 0, 'KFF_CAM_8'],
    }.get(index, -1)  # -1 is default if id not found


info = dataset(10)
# info = dataset(0)
print(info)
project_folder = 'C:/Users/Rob/Desktop/Dropbox/WORK/PYTHON SCRIPTS/'
# project_folder = '/home/robdupre/PycharmProjects/'
settings_location = '/ocean/robdupre/PYTHON_SCRIPTS/MONICA/'

analyser = GetCrowd('001', settings_location + '/' + info[2])
# analyser = GetPeople(info[3], settings_location)
# analyser = GetFlow(info[3], settings_location)

with open(analyser.module_id + '_reg.txt', 'w') as outfile:
    json.dump(analyser.create_reg_message(datetime.datetime.utcnow().isoformat()), outfile)

if info == -1:
    print('NO DATA SET SELECTED')
else:
    if info[1] == 'Live':
        cap = CamVideoStreamer(info[0])
        cap.start()
        if cap.open():
            print("CAMERA CONNECTION IS ESTABLISHED.")
        else:
            print("FAILED TO CONNECT TO CAMERA.")
            exit(-1)

        count = 0
        while cap.open():
            frame = cap.read()
            message, frame = analyser.process_frame(frame, info[2])
            cv2.putText(frame, json.dumps(message, indent=4), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (255, 255, 255), 1, cv2.LINE_AA)
            with open(info[2] + '_' + str(inc.get_incrementer(count, 5)) + '.txt', 'w') as outfile:
                json.dump(message, outfile)

            count = count + 1
            key = cv2.waitKey(1) & 0xFF
            # KEYBINDINGS FOR DISPLAY
            if key == ord('p'):  # pause
                while True:
                    key2 = cv2.waitKey(1) or 0xff
                    cv2.imshow('frame', frame)
                    if key2 == ord('p'):  # resume
                        break
            cv2.imshow('frame', frame)
            if key == 27:  # exit
                break
    else:
        cam = ImageSequenceStreamer(info[0], info[1], (1080, 768), loop_last=False, repeat=True)
        count = 0
        while cam.open():
            frame = cam.read()
            message, result = analyser.process_frame(frame, info[2])

            # SEND A HTTP REQUEST OFF
            # try:
            #     res = requests.post('http://127.0.0.2:5000/message', json=message)
            # except requests.exceptions.RequestException as e:
            #     print(e)
            # else:
            #     print(res.status_code, res.headers['content-type'], res.text)
            # WRITE FILES FOR USE LATER
            # cv2.imwrite(info[2] + '_Frame_' + str(inc.get_incrementer(count, 5)) + '.jpeg', frame)
            # cv2.imwrite(info[2] + '_Result_' + str(inc.get_incrementer(count, 5)) + '.jpeg', result)
            with open(info[2] + '_' + str(inc.get_incrementer(count, 5)) + '.txt', 'w') as outfile:
                json.dump(message, outfile)
            count = count + 1
            key = cv2.waitKey(1) & 0xFF
            # KEYBINDINGS FOR DISPLAY
            if key == ord('p'):  # pause
                while True:
                    key2 = cv2.waitKey(1) or 0xff
                    cv2.imshow('frame', frame)
                    if key2 == ord('p'):  # resume
                        break
            cv2.imshow('frame', frame)
            if key == 27:  # exit
                break
