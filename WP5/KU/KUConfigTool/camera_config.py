# camera_config.py
"""The KU Camera config app. Designed to produce all the reqequired meta data and finally the registration messages to
be sent off to the LinkSmart component
"""

import argparse
from tkinter import *
from PIL import Image, ImageTk
from pathlib import Path
import sys
import cv2
import numpy as np
sys.path.append(str(Path(__file__).absolute().parents[3]))
from WP5.KU.SharedResources.cam_video_streamer import CamVideoStreamer
from WP5.KU.SharedResources.frame_streamer import ImageSequenceStreamer
from WP5.KU.KUConfigTool.config_tools import ConfigTools
from WP5.KU.KUConfigTool.ground_plane_gui import GroundPlane, TopDown
from WP5.KU.KUConfigTool.crowd_mask import CrowdMask
from WP5.KU.KUConfigTool.flow_rois import FlowROI

__version__ = '0.3'
__author__ = 'Rob Dupre (KU)'

parser = argparse.ArgumentParser(description='Config Tool to create settings files for each camera '
                                             'and the required algorithms.')
parser.add_argument('--rtsp', default='rtsp://root:pass@10.144.129.107/axis-media/media.amp',
                    type=str, help='The RTSP stream address to allow access to the feed and run the config on.')
parser.add_argument('--seq_location', default='None',
                    type=str, help='Local file location to be used to stream images instead of RTSP')
parser.add_argument('--x_size', default=None, type=int, help='Desired frame in X for loaded images.')
parser.add_argument('--y_size', default=None, type=int, help='Desired frame in Y for loaded images.')
parser.add_argument('--start_frame', default=0, type=int, help='Frame to start a given image sequence from.')
_args = parser.parse_args()
# TODO: ADD VISUAL CONFIRMATION SAVE HAS COMPLETED


class ConfigApp(Tk):
    def __init__(self, cam_stream, config_tools, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        # CREATE THE VARIABLES TO HOLD THE FRAMES
        self.title("KU Camera Registration and Configuration Tool")
        self.frames = {}
        self.config_tools = config_tools
        self.cam = cam_stream
        self.ratio, self.stream_w, self.stream_h = self.calculate_frame_size()
        self.config_tools.ratio = self.ratio
        self.cam_frame = []
        self.current_frame = []
        self.get_frame()
        # CREATE THE OVERALL CONTAINER FOR THE APP PAGES
        container = Frame(self)
        # container = Frame(self, width=2024, height=768)
        # container.pack(fill=None, expand=False)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        # FRAMES ARE CREATED ONE ON TOP OF THE OTHER AND RAISED TO THE TOP WHEN VIEWED
        self.frames["Main"] = MainPage(parent=container, controller=self)
        self.frames["CrowdMask"] = CrowdMask(container, self, self.cam)
        self.frames["GroundPlane"] = GroundPlane(container, self, self.cam)
        self.frames["TopDown"] = TopDown(parent=container, controller=self)
        self.frames["FlowROIs"] = FlowROI(container, self, self.cam)
        self.frames["Main"].grid(row=0, column=0, sticky="nsew")
        self.frames["CrowdMask"].grid(row=0, column=0, sticky="nsew")
        self.frames["GroundPlane"].grid(row=0, column=0, sticky="nsew")
        self.frames["TopDown"].grid(row=0, column=0, sticky="nsew")
        self.frames["FlowROIs"].grid(row=0, column=0, sticky="nsew")
        # SET THE FIRST PAGE TO BE VIEWED
        self.show_frame("Main")
        # self.show_frame("CrowdMask")
        # self.show_frame("FlowROIs")
        # self.show_frame("GroundPlane")
        # START THE CALLBACK FUNCTION
        self.refresher()

    def show_frame(self, page_name):
        """Raise a frame so as to be viewable

        Keyword arguments:
        page_name -- (str) Name of the page as recorded in frames
        """
        if page_name == "TopDown":
            self.frames["TopDown"].draw_image()
        frame = self.frames[page_name]
        frame.tkraise()

    def load(self, cam_id):
        if self.config_tools.load_config(cam_id):
            self.frames["Main"].e2.delete(0, END)
            self.frames["Main"].e4.delete(0, END)
            self.frames["Main"].e2.insert(10, self.config_tools.camera_type)
            self.frames["Main"].e4.insert(10, self.config_tools.zone_id)
            self.frames["Main"].v1.set(self.config_tools.module_types[0])
            self.frames["Main"].v2.set(self.config_tools.module_types[1])
            self.frames["Main"].v3.set(self.config_tools.module_types[2])
            self.frames["Main"].v4.set(self.config_tools.module_types[3])
            self.frames["Main"].v5.set(self.config_tools.state)

            self.frames["CrowdMask"].roi = self.config_tools.frame_roi
            self.frames["CrowdMask"].draw_rect()
            self.frames["CrowdMask"].e1.delete(0, END)
            self.frames["CrowdMask"].e2.delete(0, END)
            self.frames["CrowdMask"].e3.delete(0, END)
            self.frames["CrowdMask"].e4.delete(0, END)
            self.frames["CrowdMask"].e5.delete(0, END)
            self.frames["CrowdMask"].e1.insert(10, self.config_tools.camera_position[0])
            self.frames["CrowdMask"].e2.insert(10, self.config_tools.camera_position[1])
            self.frames["CrowdMask"].e3.insert(10, self.config_tools.camera_height)
            self.frames["CrowdMask"].e4.insert(10, self.config_tools.camera_tilt)
            self.frames["CrowdMask"].e5.insert(10, self.config_tools.camera_bearing)

            self.frames["CrowdMask"].mask = self.config_tools.crowd_mask
            self.frames["CrowdMask"].draw_rect()

            self.frames["GroundPlane"].e3.delete(0, END)
            self.frames["GroundPlane"].e3.insert(10, self.config_tools.ground_plane_orientation)
            self.frames["GroundPlane"].ref_pt = [
                [int((self.config_tools.ref_pt[0][0] / 1.25) * self.ratio), int((self.config_tools.ref_pt[0][1] / 1.25) * self.ratio)],
                [int((self.config_tools.ref_pt[1][0] / 1.25) * self.ratio), int((self.config_tools.ref_pt[1][1] / 1.25) * self.ratio)],
                [int((self.config_tools.ref_pt[2][0] / 1.25) * self.ratio), int((self.config_tools.ref_pt[2][1] / 1.25) * self.ratio)],
                [int((self.config_tools.ref_pt[3][0] / 1.25) * self.ratio), int((self.config_tools.ref_pt[3][1] / 1.25) * self.ratio)],
                [int((self.config_tools.ref_pt[4][0] / 1.25) * self.ratio), int((self.config_tools.ref_pt[4][1] / 1.25) * self.ratio)]]
            self.frames["GroundPlane"].draw_image()
            self.frames["GroundPlane"].draw_top_down()

            self.frames["TopDown"].roi = self.config_tools.ground_plane_roi
            self.frames["TopDown"].e1.delete(0, END)
            self.frames["TopDown"].e2.delete(0, END)
            self.frames["TopDown"].e3.delete(0, END)
            self.frames["TopDown"].e4.delete(0, END)
            self.frames["TopDown"].e1.insert(10, self.config_tools.ground_plane_size[0])
            self.frames["TopDown"].e2.insert(10, self.config_tools.ground_plane_size[1])
            self.frames["TopDown"].e3.insert(10, self.config_tools.ground_plane_position[0])
            self.frames["TopDown"].e4.insert(10, self.config_tools.ground_plane_position[1])
            self.frames["TopDown"].draw_image()
            self.frames["TopDown"].draw_rect()

            self.frames["FlowROIs"].rois = (np.array(self.config_tools.flow_rois) * self.ratio).astype(np.uint).tolist()
            self.frames["FlowROIs"].draw_rect()

    def refresher(self):
        """Call back function which refreshes the various labels/canvases in each frame.
        Updating the frames and updating variables from the config tools
        """
        self.get_frame()
        self.frames["Main"].label.config(image=self.current_frame)
        self.frames["Main"].label.image = self.current_frame
        self.frames["CrowdMask"].l1.config(text=str(self.frames["CrowdMask"].roi_count))
        self.frames["GroundPlane"].l1.config(text=str(self.config_tools.ref_pt))
        self.frames["GroundPlane"].draw_image()
        self.frames["TopDown"].l1.config(text=str(self.config_tools.ground_plane_roi))
        self.frames["FlowROIs"].l1.config(text=str(self.config_tools.flow_rois))

        self.after(5, self.refresher)

    def get_frame(self, just_frame=False):
        self.cam_frame = cam.read()
        if self.ratio < 1:
            self.cam_frame = cv2.resize(cam.read(),
                                        dsize=(int(self.stream_w * self.ratio), int(self.stream_h * self.ratio)))
        self.current_frame = ImageTk.PhotoImage(Image.fromarray(self.cam_frame, 'RGB'))

    def calculate_frame_size(self):
        display_w = self.winfo_screenwidth()
        display_h = self.winfo_screenheight()
        stream_w = cam.read().shape[0]
        stream_h = cam.read().shape[1]

        if stream_h > stream_w:
            t = stream_h
            stream_h = stream_w
            stream_w = t
        if display_w - stream_w < 0 or display_h - stream_h < 0:
            if (display_w - stream_w) < (display_h - stream_h):
                ratio = (display_w / stream_w) * 0.9
            else:
                ratio = (display_h / stream_h) * 0.9
            print('SCREEN SIZE IS SMALLER THAN THE STREAM SIZE RATIO:{}'.format(ratio))
        else:
            ratio = 1
        return ratio, stream_w, stream_h


class MainPage(Frame):
    # THE FIRST FRAME OF CONFIG TOOL
    def __init__(self, parent, controller):
        # INITIALISE THE FRAME
        Frame.__init__(self, parent)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=216)
        # GET THE CURRENT FRAME FROM THE STREAM AND CONVERT TO APPROPRIATE IMAGE
        im = controller.current_frame
        # CREATE LABEL FOR THE IMAGE USE self TO ALLOW EXTERNAL ACCESS THROUGH refresher()
        self.label = Label(self, image=im)
        self.label.grid(row=0, columnspan=7)
        self.label.image = im

        # CREATE LABELS FOR ENTRY BOXES
        Label(self, text="Camera ID").grid(row=1, column=3, sticky=E)
        Label(self, text="Zone ID").grid(row=1, column=5, sticky=E)
        Label(self, text="Camera Type").grid(row=2, column=3, sticky=E)
        Label(self, text="Registration Message Address").grid(row=3, column=3, sticky=E)
        Label(self, text="Modules:").grid(row=1, column=1, sticky=E)
        Label(self, text="Camera State:").grid(row=1, column=0, sticky=W)

        # ADD ENTRIES FOR THE VARIOUS TEXT BOXES AND LABELS FOR DESCRIPTIONS
        self.e1 = Entry(self, justify='center')
        self.e2 = Entry(self, justify='center')
        self.e3 = Entry(self, justify='center')
        self.e4 = Entry(self, justify='center')
        self.e1.insert(10, "CAMERA_XXX")
        self.e2.insert(10, "RGB")
        self.e3.insert(10, "NONE")
        self.e4.insert(10, "Not Set")
        self.e1.grid(row=1, column=4, sticky="W")
        self.e2.grid(row=2, column=4)
        self.e3.grid(row=3, column=4)
        self.e4.grid(row=1, column=6)

        self.v1 = IntVar()
        self.v1.set(1)
        self.v2 = IntVar()
        self.v2.set(1)
        self.v3 = IntVar()
        self.v3.set(1)
        self.v4 = IntVar()
        self.v4.set(1)
        self.c1 = Checkbutton(self, text='Crowd Density', variable=self.v1).grid(row=2, column=1, sticky=E)
        self.c2 = Checkbutton(self, text='Optical Flow', variable=self.v2).grid(row=2, column=2, sticky=W)
        self.c3 = Checkbutton(self, text='Fight Detection', variable=self.v3).grid(row=3, column=1, sticky=E)
        self.c4 = Checkbutton(self, text='Object Detection', variable=self.v4, anchor="w").grid(row=3, column=2, sticky=W)

        self.v5 = IntVar()
        self.v5.set(1)
        self.r1 = Radiobutton(self, text='Active', variable=self.v5, value=1).grid(row=2, column=0, sticky=W)
        self.r1 = Radiobutton(self, text='Inactive', variable=self.v5, value=0).grid(row=3, column=0, sticky=W)

        # CREATE BUTTONS FOR NAVIGATION
        # TODO:ADD LOGIC TO MAKE APPEAR A NEXT BUTTON WHEN ENTRIES RETURN TRUE FROM config_tools CHECKER
        b1 = Button(self, text='Quit', command=parent.quit)
        b1.grid(row=4, column=0, sticky=W, pady=4)
        b1 = Button(self, text='Screenshot', command=lambda: cam.save(self.e1.get()))
        b1.grid(row=4, column=2, sticky=W, pady=4)
        b2 = Button(self, text='Save & Send', command=lambda: self.save())
        b2.grid(row=4, column=3, sticky=W, pady=4)
        b3 = Button(self, text='Load', command=lambda: controller.load(self.e1.get()))
        b3.grid(row=4, column=4, sticky=W, pady=4)
        b4 = Button(self, text='Go Back', command=lambda: self.go_back(controller))
        b4.grid(row=4, column=5, sticky=E, pady=4)
        b5 = Button(self, text='Next Page', command=lambda: self.next_page(controller))
        b5.grid(row=4, column=6, sticky=W, pady=4)

        self.update_config()

    def go_back(self, controller):
        self.update_config()
        controller.show_frame("FlowROIs")

    def next_page(self, controller):
        self.update_config()
        controller.show_frame("CrowdMask")

    def save(self):
        self.update_config()
        self.controller.config_tools.save_config(str(self.e3.get()))

    def update_config(self):
        self.controller.config_tools.camera_id = self.e1.get()
        self.controller.config_tools.camera_type = self.e2.get()
        self.controller.config_tools.zone_id = self.e4.get()
        self.controller.config_tools.module_types = [self.v1.get(), self.v2.get(), self.v3.get(), self.v4.get()]
        self.controller.config_tools.state = self.v5.get()


if __name__ == '__main__':
    # _args.seq_location = '/ocean/datasets/OXFORD_TOWNCENTRE/TownCentreXVID/'
    # _args.seq_location = '/ocean/datasets/MONICA/TO/KFF 2017/channel 8/2017-07-08 20-40-00~20-50-00//'
    # _args.seq_location = '/ocean/datasets/MONICA/TO/KFF 2017/channel 4/2017-07-08 14-00-00~14-10-00/'
    # _args.seq_location = '/ocean/datasets/MONICA/TO/KFF 2017/channel 2/2017-07-09 19-40-00~19-50-00/'
    # _args.seq_location = '/ocean/datasets/MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_1/'
    # _args.seq_location = '/ocean/datasets/MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_2/'
    # _args.seq_location = '/ocean/datasets/MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_3/'
    # _args.seq_location = '/ocean/datasets/MONICA/BONN/Rein in Flammen 2018/20180505_193000_camera_4/'
    # _args.seq_location = '/ocean/datasets/MONICA/YCCC-LR/LEEDS_2018_AUG/CONFIG/LEEDS_4//'
    _args.seq_location = '/ocean/datasets/MONICA/TIVOLI/REVIEW_2018/CONFIG/TIVOLI_25//'

    # _args.rtsp = 'rtsp://root:pass@10.144.129.107/axis-media/media.amp'

    if _args.seq_location is 'None':
        cam = CamVideoStreamer(_args.rtsp)
        cam.start()
    else:
        cam = ImageSequenceStreamer(_args.seq_location, _args.start_frame, (_args.x_size, _args.y_size))
    if cam.open():
        print("CAMERA CONNECTION IS ESTABLISHED.")
        config = ConfigTools()
        config_app = ConfigApp(cam, config)
        config_app.mainloop()
        cam.stop()
        exit(-1)
    else:
        print("FAILED TO CONNECT TO CAMERA.")
        exit(-1)
