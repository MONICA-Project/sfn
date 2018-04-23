# camera_config.py
"""The KU Camera config app. Designed to produce all the reqequired meta data and finally the registration messages to
be sent off to the LinkSmart component
"""

import argparse
from tkinter import *
from PIL import Image, ImageTk
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[3]))
from WP5.KU.SharedResources.cam_video_streamer import CamVideoStreamer
from WP5.KU.SharedResources.frame_streamer import ImageSequenceStreamer
from WP5.KU.KUConfigTool.config_tools import ConfigTools
from WP5.KU.KUConfigTool.ground_plane_gui import GroundPlane, TopDown
from WP5.KU.KUConfigTool.flow_rois import FlowROI

__version__ = '0.2'
__author__ = 'Rob Dupre (KU)'

parser = argparse.ArgumentParser(description='Config Tool to create settings files for each camera '
                                             'and the required algorithms.')
parser.add_argument('--file_location', default='/weights/ssd_300_VOC0712.pth',
                    type=str, help='The save location for the resultant settings file, also used as the input for '
                                   'frame analysers.')
parser.add_argument('--identifier', default='001', type=str, help='Camera identifier, used to check the config file.'
                    ' is being loaded to the correct camera')
parser.add_argument('--rtsp', default='rtsp://root:pass@10.144.129.107/axis-media/media.amp',
                    type=str, help='The RTSP stream address to allow access to the feed and run the config on.')
# parser.add_argument('--seq_location', default='/ocean/datasets/MONICA/TO/KFF 2017/channel 8/2017-07-08 20-40-00~20-50-00//',
parser.add_argument('--seq_location', default='/ocean/datasets/MONICA/TO/KFF 2017/channel 4/2017-07-08 14-00-00~14-10-00/',
# parser.add_argument('--seq_location', default='/ocean/datasets/MONICA/TO/KFF 2017/channel 2/2017-07-09 19-40-00~19-50-00/',
# parser.add_argument('--seq_location', default=None,
                    type=str, help='Local file location to be used to stream images instead of RTSP')
parser.add_argument('--x_size', default=1080, type=int, help='Desired frame in X for loaded images.')
parser.add_argument('--y_size', default=768, type=int, help='Desired frame in Y for loaded images.')
parser.add_argument('--start_frame', default=1, type=int, help='Frame to start a given image sequence from.')
_args = parser.parse_args()

# TODO: IMPROVE LAYOUT
# TODO: ADD VISUAL CONFIRMATION SAVE HAS COMPLETED
# TODO: Further test


class ConfigApp(Tk):
    def __init__(self, cam_stream, config_tools, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        # CREATE THE VARIABLES TO HOLD THE FRAMES
        self.title("KU Camera Registration and Configuration Tool")
        self.frames = {}
        self.config_tools = config_tools
        self.cam = cam_stream
        # CREATE THE OVERALL CONTAINER FOR THE APP PAGES
        container = Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        # FRAMES ARE CREATED ONE ON TOP OF THE OTHER AND RAISED TO THE TOP WHEN VIEWED
        self.frames["Main"] = MainPage(parent=container, controller=self)
        self.frames["FrameROI"] = FrameROI(parent=container, controller=self)
        self.frames["GroundPlane"] = GroundPlane(container, self, self.cam)
        self.frames["TopDown"] = TopDown(parent=container, controller=self)
        self.frames["FlowROIs"] = FlowROI(container, self, self.cam)
        self.frames["Main"].grid(row=0, column=0, sticky="nsew")
        self.frames["FrameROI"].grid(row=0, column=0, sticky="nsew")
        self.frames["GroundPlane"].grid(row=0, column=0, sticky="nsew")
        self.frames["TopDown"].grid(row=0, column=0, sticky="nsew")
        self.frames["FlowROIs"].grid(row=0, column=0, sticky="nsew")
        # SET THE FIRST PAGE TO BE VIEWED
        self.show_frame("Main")
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

            self.frames["FrameROI"].roi = self.config_tools.frame_roi
            self.frames["FrameROI"].draw_rect()
            self.frames["FrameROI"].e1.delete(0, END)
            self.frames["FrameROI"].e2.delete(0, END)
            self.frames["FrameROI"].e3.delete(0, END)
            self.frames["FrameROI"].e4.delete(0, END)
            self.frames["FrameROI"].e5.delete(0, END)
            self.frames["FrameROI"].e1.insert(10, self.config_tools.camera_position[0])
            self.frames["FrameROI"].e2.insert(10, self.config_tools.camera_position[1])
            self.frames["FrameROI"].e3.insert(10, self.config_tools.camera_height)
            self.frames["FrameROI"].e4.insert(10, self.config_tools.camera_tilt)
            self.frames["FrameROI"].e5.insert(10, self.config_tools.camera_bearing)

            self.frames["GroundPlane"].e3.delete(0, END)
            self.frames["GroundPlane"].e3.insert(10, self.config_tools.ground_plane_orientation)
            self.frames["GroundPlane"].ref_pt = [
                [int(self.config_tools.ref_pt[0][0] / 1.25), int(self.config_tools.ref_pt[0][1] / 1.25)],
                [int(self.config_tools.ref_pt[1][0] / 1.25), int(self.config_tools.ref_pt[1][1] / 1.25)],
                [int(self.config_tools.ref_pt[2][0] / 1.25), int(self.config_tools.ref_pt[2][1] / 1.25)],
                [int(self.config_tools.ref_pt[3][0] / 1.25), int(self.config_tools.ref_pt[3][1] / 1.25)],
                [int(self.config_tools.ref_pt[4][0] / 1.25), int(self.config_tools.ref_pt[4][1] / 1.25)]]
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

            self.frames["FlowROIs"].rois = self.config_tools.flow_rois
            self.frames["FlowROIs"].draw_rect()

    def refresher(self):
        """Call back function which refreshes the various labels/canvases in each frame.
        Updating the frames from the rstp stream and updating variables from the config tools
        """
        im_new = Image.fromarray(cam.read(), 'RGB')
        im_new = ImageTk.PhotoImage(im_new)
        self.frames["Main"].label.config(image=im_new)
        self.frames["Main"].label.image = im_new
        self.frames["FrameROI"].l1.config(text=str(self.config_tools.frame_roi))
        self.frames["GroundPlane"].l1.config(text=str(self.config_tools.ref_pt))
        self.frames["GroundPlane"].draw_image()
        self.frames["TopDown"].l1.config(text=str(self.config_tools.ground_plane_roi))
        self.frames["FlowROIs"].l1.config(text=str(self.config_tools.flow_rois))

        # self.frames["GroundPlane"].label.config(image=im_new)
        # self.frames["GroundPlane"].label.image = im_new
        self.after(5, self.refresher)


class MainPage(Frame):
    # THE FIRST FRAME OF CONFIG TOOL
    def __init__(self, parent, controller):
        # INITIALISE THE FRAME
        Frame.__init__(self, parent)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=216)
        # GET THE CURRENT FRAME FROM THE STREAM AND CONVERT TO APPROPRIATE IMAGE
        frame = cam.read()
        im = Image.fromarray(frame, 'RGB')
        im = ImageTk.PhotoImage(im)
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
        self.e2.insert(10, "Not Set")
        self.e3.insert(10, 'https://portal.monica-cloud.eu/scral/sfn/camera')
        self.e4.insert(10, "Not Set")
        self.e1.grid(row=1, column=4, sticky="W")
        self.e2.grid(row=2, column=4)
        self.e3.grid(row=3, column=4)
        self.e4.grid(row=1, column=6)

        self.v1 = IntVar()
        self.v2 = IntVar()
        self.v3 = IntVar()
        self.v4 = IntVar()
        self.c1 = Checkbutton(self, text='Crowd Density', variable=self.v1).grid(row=2, column=1, sticky=E)
        self.c2 = Checkbutton(self, text='Optical Flow', variable=self.v2).grid(row=2, column=2, sticky=W)
        self.c3 = Checkbutton(self, text='Fight Detection', variable=self.v3).grid(row=3, column=1, sticky=E)
        self.c4 = Checkbutton(self, text='Object Detection', variable=self.v4, anchor="w").grid(row=3, column=2, sticky=W)

        self.v5 = IntVar()
        self.r1 = Radiobutton(self, text='Active', variable=self.v5, value=1).grid(row=2, column=0, sticky=W)
        self.r1 = Radiobutton(self, text='Inactive', variable=self.v5, value=0).grid(row=3, column=0, sticky=W)

        # CREATE BUTTONS FOR NAVIGATION
        # TODO:ADD LOGIC TO MAKE APPEAR A NEXT BUTTON WHEN ENTRIES RETURN TRUE FROM config_tools CHECKER
        b1 = Button(self, text='Quit', command=parent.quit)
        b1.grid(row=4, column=0, sticky=W, pady=4)
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
        controller.show_frame("FrameROI")

    def save(self):
        self.update_config()
        self.controller.config_tools.save_config(str(self.e3.get()))

    def update_config(self):
        self.controller.config_tools.camera_id = self.e1.get()
        self.controller.config_tools.camera_type = self.e2.get()
        self.controller.config_tools.zone_id = self.e4.get()
        self.controller.config_tools.module_types = [self.v1.get(), self.v2.get(), self.v3.get(), self.v4.get()]
        self.controller.config_tools.state = self.v5.get()


class FrameROI(Frame):
    # THE SECOND FRAME OF CONFIG TOOL USED TO DEFINE THE REGION OF INTEREST
    def __init__(self, parent, controller):
        # INITIALISE THE FRAME
        Frame.__init__(self, parent)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=216)
        # GET THE CURRENT FRAME AND CONVERT
        frame = cam.read()
        self.width = frame.shape[1]
        self.height = frame.shape[0]
        self.im = Image.fromarray(frame, 'RGB')
        self.image = ImageTk.PhotoImage(self.im)
        # CREATE Canvas FOR THE IMAGE WHICH ALLOWS FOR DRAWING
        self.canvas = Canvas(self, width=frame.shape[1], height=frame.shape[0], cursor="cross")
        self.canvas.grid(row=0, columnspan=5)
        # BIND FUNCTIONS TO THE EVENT CALLBACKS
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # CREATE LABEL TO REFLECT CONTENT OF THE ConfigTool (UPDATED IN refresher())
        Label(self, text="Region of Interest Points").grid(row=1, column=0, sticky=E)
        Label(self, text="Longitude and Latitude").grid(row=2, column=0, sticky=E)
        Label(self, text="Camera Height (m)").grid(row=2, column=3, sticky=E)
        Label(self, text="Tilt Angle (degrees)").grid(row=3, column=0, sticky=E)
        Label(self, text="Camera bearing (degrees)").grid(row=3, column=2, sticky=E)

        self.l1 = Label(self, text="NONE")
        self.l1.grid(row=1, column=1)

        self.e1 = Entry(self, justify='center')
        self.e2 = Entry(self, justify='center')
        self.e3 = Entry(self, justify='center')
        self.e4 = Entry(self, justify='center')
        self.e5 = Entry(self, justify='center')
        self.e1.insert(10, "4.")
        self.e2.insert(10, "3.")
        self.e3.insert(10, 8)
        self.e4.insert(10, 35)
        self.e5.insert(10, 270)
        self.e1.grid(row=2, column=1)
        self.e2.grid(row=2, column=2)
        self.e3.grid(row=2, column=4)
        self.e4.grid(row=3, column=1)
        self.e5.grid(row=3, column=3)

        # CREATE BUTTONS FOR NAVIGATION
        b1 = Button(self, text='Quit', command=parent.quit)
        b1.grid(row=4, column=0, sticky=W, pady=4)
        b2 = Button(self, text='Go Back', command=lambda: self.go_back(self.controller))
        b2.grid(row=4, column=3, sticky=E, pady=4)
        b2 = Button(self, text='Next Page', command=lambda: self.next_page(self.controller))
        b2.grid(row=4, column=4, sticky=W, pady=4)

        # VARIABLES USED IN OPERATION
        self.rect = None
        self.roi = [0, 0, self.width, self.height]

        # DRAW THE IMAGE
        self._draw_image()
        self.update_config()

    def go_back(self, controller):
        self.update_config()
        controller.show_frame("Main")

    def next_page(self, controller):
        self.update_config()
        controller.show_frame("GroundPlane")

    def update_config(self):
        self.controller.config_tools.frame_roi = self.roi
        self.controller.config_tools.camera_position = [float(self.e1.get()), float(self.e2.get())]
        self.controller.config_tools.camera_height = float(self.e3.get())
        self.controller.config_tools.camera_tilt = int(self.e4.get())
        self.controller.config_tools.camera_bearing = int(self.e5.get())

    def _draw_image(self):
        self.canvas.create_image(0, 0, anchor="nw", image=self.image)

    def draw_rect(self):
        self.canvas.delete("all")
        self._draw_image()
        self.rect = self.canvas.create_rectangle(self.roi[0], self.roi[1], 5, 5, fill=None)
        self.canvas.coords(self.rect, self.roi[0], self.roi[1], self.roi[2], self.roi[3])

    def on_button_press(self, event):
        # save mouse drag start position
        self.roi[0] = event.x
        self.roi[1] = event.y
        self.roi[2] = event.x + 5
        self.roi[3] = event.y + 5

        # create rectangle if not yet exist
        if not self.rect:
            self.rect = self.canvas.create_rectangle(self.roi[0], self.roi[1], self.roi[2], self.roi[3], fill=None)

    def on_move_press(self, event):
        x, y = (event.x, event.y)
        # LIMIT DRAG ONLY DOWN RIGHT
        if x > self.roi[0] + 1 and y > self.roi[1] + 1:
            self.roi[2] = x
            self.roi[3] = y
            # LIMIT DRAG TO WITHIN IMAGE DIMENSIONS
            if self.roi[2] < 0:
                self.roi[2] = 0
            elif self.roi[2] > self.width:
                self.roi[2] = self.width

            if self.roi[3] < 0:
                self.roi[3] = 0
            elif self.roi[3] > self.height:
                self.roi[3] = self.height

            # expand rectangle as you drag the mouse
            self.canvas.coords(self.rect, self.roi[0], self.roi[1], self.roi[2], self.roi[3])

    def on_button_release(self, event):
        self.update_config()


if __name__ == '__main__':
    if _args.seq_location is None:
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
