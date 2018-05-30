# video_to_frames.py
"""Takes a video file and extracts and saves frames at a set frame rate"""

import cv2
import os
import numpy as np
import sys
from pathlib import Path
import WP5.KU.SharedResources.get_incrementer as incrementer
sys.path.append(str(Path(__file__).absolute().parents[4]))

__version__ = '0.1'
__author__ = 'Rob Dupre'


def video_to_images(folder, image_file_type, frame_rate=25, display=False):

    file_names = []
    # GET LIST OF VIDEOS AT FILE LOCATION
    valid_types = ('.mp4', '.avi')
    for f in sorted(os.listdir(folder)):
        ext = os.path.splitext(f)[1]
        if ext.lower().endswith(valid_types):
            file_names.append(os.path.join(folder, f))

    # LOOP THROUGH THE VIDEOS
    for file in file_names:
        # CREATE A NEW FOLDER TO HOLD THE FRAMES
        new_folder = os.path.dirname('{}/'.format(os.path.splitext(file)[0]))
        if not os.path.exists(new_folder):
            os.makedirs(new_folder)

        # DELETE THE CONTENTS OF TEH FOLDER
        for the_file in os.listdir(new_folder):
            file_path = os.path.join(new_folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

        # LOAD THE VIDEO, CHECK ITS OPENED
        video = cv2.VideoCapture(file)
        if video.isOpened():
            # GET THE LENGTH AND FPS
            fps = video.get(cv2.CAP_PROP_FPS)
            if fps < frame_rate:
                print('Warning: Desired frame rate is higher than the videos actual frame rate. '
                      'Setting frame rate to max available.')
                frame_rate = fps
            # GET THE INCREMENTS FOR THE COUNTER WHEN A FRAME SHOULD BE SAVED
            frame_interval = int(np.floor(fps / frame_rate))
            length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            num_digits = incrementer.get_num_length(length) + 1

            counter = 0
            ret, frame = video.read()
            while ret:
                # Capture frame-by-frame
                ret, frame = video.read()
                # EVERY frame_rate INTERVAL SAVE THE FRAME
                if np.mod(counter, frame_interval) == 0:

                    cv2.imwrite('{}/{}.{}'.format(new_folder, incrementer.get_incrementer(counter, num_digits),
                                                  image_file_type), frame)

                    if display:
                        cv2.imshow('frame', frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break

                counter = counter + 1
            # When everything done, release the capture
            video.release()
            cv2.destroyAllWindows()
        else:
            print('Video did not open')


# TEST
video_to_images('/ocean/datasets/MONICA/BONN/Rein in Flammen 2018/', 'jpeg', frame_rate=1, display=False)
