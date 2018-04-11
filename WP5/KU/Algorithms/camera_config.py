# camera_config.py
from cam_video_streamer import CamVideoStreamer
from frame_streamer import ImageSequenceStreamer
import argparse
from config_tools import ConfigTools
from tkinter import *
from PIL import Image, ImageTk

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
# parser.add_argument('--seq_location', default='/ocean/datasets/MONICA/TO/KFF 2017/channel 4/2017-07-08 14-00-00~14-10-00/',
# parser.add_argument('--seq_location', default='/ocean/datasets/MONICA/TO/KFF 2017/channel 2/2017-07-09 19-40-00~19-50-00/',
parser.add_argument('--seq_location', default=None,
                    type=str, help='Local file location to be used to stream images instead of RTSP')
parser.add_argument('--x_size', default=1080, type=int, help='Desired frame in X for loaded images.')
parser.add_argument('--y_size', default=768, type=int, help='Desired frame in Y for loaded images.')
parser.add_argument('--start_frame', default=1, type=int, help='Frame to start a given image sequence from.')
_args = parser.parse_args()

# TODO: ADD CAMERA BEARING
# TODO: ADD STATE ACTIVE INACTIVE RADIO BUTTON


class ConfigApp(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        # CREATE THE VARIABLES TO HOLD THE FRAMES
        self.title("ENTER CAMERA DETAILS")
        self.frames = {}
        # CREATE THE OVERALL CONTAINER FOR THE APP PAGES
        container = Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        # FRAMES ARE CREATED ONE ON TOP OF THE OTHER AND RAISED TO THE TOP WHEN VIEWED
        self.frames["PageOne"] = PageOne(parent=container, controller=self)
        self.frames["PageTwo"] = PageTwo(parent=container, controller=self)
        self.frames["PageThree"] = PageThree(parent=container, controller=self)
        self.frames["PageFour"] = PageFour(parent=container, controller=self)
        self.frames["PageOne"].grid(row=0, column=0, sticky="nsew")
        self.frames["PageTwo"].grid(row=0, column=0, sticky="nsew")
        self.frames["PageThree"].grid(row=0, column=0, sticky="nsew")
        self.frames["PageFour"].grid(row=0, column=0, sticky="nsew")
        # SET THE FIRST PAGE TO BE VIEWED
        self.show_frame("PageOne")
        # self.show_frame("PageThree")
        # START THE CALLBACK FUNCTION
        self.refresher()

    def show_frame(self, page_name):
        """Raise a frame so as to be viewable

        Keyword arguments:
        page_name -- (str) Name of the page as recorded in frames
        """
        if page_name == "PageFour":
            self.frames["PageFour"].draw_image()
        frame = self.frames[page_name]
        frame.tkraise()

    def load(self, cam_id):
        if config.load_config(cam_id):
            self.frames["PageOne"].e2.delete(0, END)
            self.frames["PageOne"].e3.delete(0, END)
            self.frames["PageOne"].e5.delete(0, END)
            self.frames["PageOne"].e6.delete(0, END)
            self.frames["PageOne"].e7.delete(0, END)
            self.frames["PageOne"].e2.insert(10, config.camera_position[0])
            self.frames["PageOne"].e3.insert(10, config.camera_position[1])
            self.frames["PageOne"].e5.insert(10, config.camera_tilt)
            self.frames["PageOne"].e6.insert(10, config.camera_type)
            self.frames["PageOne"].e7.insert(10, config.camera_height)

            self.frames["PageTwo"].roi = config.roi
            self.frames["PageTwo"].draw_rect()

            self.frames["PageThree"].e1.delete(0, END)
            self.frames["PageThree"].e2.delete(0, END)
            self.frames["PageThree"].e4.delete(0, END)
            self.frames["PageThree"].e1.insert(10, config.ground_plane_gps[0])
            self.frames["PageThree"].e2.insert(10, config.ground_plane_gps[1])
            self.frames["PageThree"].e4.insert(10, config.ground_plane_orientation)
            self.frames["PageThree"].ref_pt = [[int(config.ref_pt[0][0] / 1.25), int(config.ref_pt[0][1] / 1.25)],
                                               [int(config.ref_pt[1][0] / 1.25), int(config.ref_pt[1][1] / 1.25)],
                                               [int(config.ref_pt[2][0] / 1.25), int(config.ref_pt[2][1] / 1.25)],
                                               [int(config.ref_pt[3][0] / 1.25), int(config.ref_pt[3][1] / 1.25)],
                                               [int(config.ref_pt[4][0] / 1.25), int(config.ref_pt[4][1] / 1.25)]]
            self.frames["PageThree"].draw_image()
            self.frames["PageThree"].draw_top_down()

            self.frames["PageFour"].roi = config.ground_plane_roi
            self.frames["PageFour"].e1.delete(0, END)
            self.frames["PageFour"].e2.delete(0, END)
            self.frames["PageFour"].e1.insert(10, config.ground_plane_size[0])
            self.frames["PageFour"].e2.insert(10, config.ground_plane_size[1])
            self.frames["PageFour"].draw_image()
            self.frames["PageFour"].draw_rect()

    def refresher(self):
        """Call back function which refreshes the various labels/canvases in each frame.
        Updating the frames from the rstp stream and updating variables from the config tools
        """
        im_new = Image.fromarray(cam.read(), 'RGB')
        im_new = ImageTk.PhotoImage(im_new)
        self.frames["PageOne"].label.config(image=im_new)
        self.frames["PageOne"].label.image = im_new
        self.frames["PageTwo"].l1.config(text=str(config.roi))
        self.frames["PageThree"].l1.config(text=str(config.ref_pt))
        self.frames["PageThree"].draw_image()
        self.frames["PageFour"].l1.config(text=str(config.ground_plane_roi))

        # self.frames["PageThree"].label.config(image=im_new)
        # self.frames["PageThree"].label.image = im_new
        self.after(5, self.refresher)


class PageOne(Frame):
    # THE FIRST FRAME OF CONFIG TOOL
    def __init__(self, parent, controller):
        # INITIALISE THE FRAME
        Frame.__init__(self, parent)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=216)
        # GET THE CURRENT FRAME FROM THE STREAM AND CONVERT TO APPROPRIATE IMAGE
        frame = cam.read()
        im = Image.fromarray(frame, 'RGB')
        im = ImageTk.PhotoImage(im)
        # CREATE LABEL FOR THE IMAGE USE self TO ALLOW EXTERNAL ACCESS THROUGH refresher()
        self.label = Label(self, image=im)
        self.label.grid(row=0, columnspan=5)
        self.label.image = im

        # CREATE LABELS FOR ENTRY BOXES
        Label(self, text="Camera ID").grid(row=1, column=0)
        Label(self, text="Camera Type").grid(row=1, column=2)
        Label(self, text="Longitude and Latitude").grid(row=2, column=0)
        Label(self, text="Camera Height (m)").grid(row=2, column=3)
        Label(self, text="Tilt Angle (degrees)").grid(row=3, column=2)
        Label(self, text="Registration Message Address").grid(row=3, column=0)

        # ADD ENTRIES FOR THE VARIOUS TEXT BOXES AND LABELS FOR DESCRIPTIONS
        self.e1 = Entry(self, justify='center')
        self.e2 = Entry(self, justify='center')
        self.e3 = Entry(self, justify='center')
        self.e4 = Entry(self, justify='center')
        self.e5 = Entry(self, justify='center')
        self.e6 = Entry(self, justify='center')
        self.e7 = Entry(self, justify='center')
        self.e1.insert(10, "CAMERA_XXX")
        self.e2.insert(10, "51.40185")
        self.e3.insert(10, "-0.30261")
        self.e4.insert(10, NONE)
        self.e5.insert(10, "36")
        self.e6.insert(10, "RGB")
        self.e7.insert(10, "5")
        self.e1.grid(row=1, column=1, sticky="W")
        self.e2.grid(row=2, column=1)
        self.e3.grid(row=2, column=2)
        self.e4.grid(row=3, column=1)
        self.e5.grid(row=3, column=3)
        self.e6.grid(row=1, column=3)
        self.e7.grid(row=2, column=4)

        # CREATE BUTTONS FOR NAVIGATION
        # TODO:ADD LOGIC TO MAKE APPEAR A NEXT BUTTON WHEN ENTRIES RETURN TRUE FROM config_tools CHECKER
        b1 = Button(self, text='Quit', command=parent.quit)
        b1.grid(row=4, column=0, sticky=W, pady=4)
        b2 = Button(self, text='Save & Send', command=lambda: config.save_config(self.e4.get()))
        b2.grid(row=4, column=1, sticky=W, pady=4)
        b3 = Button(self, text='Load', command=lambda: controller.load(self.e1.get()))
        b3.grid(row=4, column=2, sticky=W, pady=4)
        b4 = Button(self, text='Go Back', command=lambda: self.next_page(controller))
        b4.grid(row=4, column=3, sticky=W, pady=4)
        b5 = Button(self, text='Next Page', command=lambda: self.next_page(controller))
        b5.grid(row=4, column=4, sticky=W, pady=4)

        self.update_config()

    def go_back(self, controller):
        self.update_config()
        controller.show_frame("PageThree")

    def next_page(self, controller):
        self.update_config()
        controller.show_frame("PageTwo")

    def update_config(self):
        config.camera_id = self.e1.get()
        config.camera_position = [float(self.e2.get()), float(self.e3.get())]
        config.camera_tilt = int(self.e5.get())
        config.camera_type = self.e6.get()
        config.camera_height = float(self.e7.get())


class PageTwo(Frame):
    # THE SECOND FRAME OF CONFIG TOOL USED TO DEFINE THE REGION OF INTEREST
    def __init__(self, parent, controller):
        # INITIALISE THE FRAME
        Frame.__init__(self, parent)
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
        Label(self, text="Region of Interest Points").grid(row=1, column=3)
        self.l1 = Label(self, text="NONE")
        self.l1.grid(row=2, column=3)

        # CREATE BUTTONS FOR NAVIGATION
        b1 = Button(self, text='Quit', command=parent.quit)
        b1.grid(row=3, column=0, sticky=W, pady=4)
        b2 = Button(self, text='Go Back', command=lambda: controller.show_frame("PageOne"))
        b2.grid(row=3, column=3, sticky=W, pady=4)
        b2 = Button(self, text='Next Page', command=lambda: controller.show_frame("PageThree"))
        b2.grid(row=3, column=4, sticky=W, pady=4)

        # VARIABLES USED IN OPERATION
        self.rect = None
        self.roi = [0, 0, self.width, self.height]

        # DRAW THE IMAGE
        self._draw_image()
        self.update_config()

    def update_config(self):
        config.roi = self.roi

    def _draw_image(self):
        self.canvas.create_image(0, 0, anchor="nw", image=self.image)

    def draw_rect(self):
        self.rect = self.canvas.create_rectangle(self.roi[0], self.roi[1], 5, 5, fill=None)
        self.canvas.coords(self.rect, self.roi[0], self.roi[1], self.roi[2], self.roi[3])

    def on_button_press(self, event):
        # save mouse drag start position
        self.roi[0] = event.x
        self.roi[1] = event.y

        # create rectangle if not yet exist
        if not self.rect:
            self.rect = self.canvas.create_rectangle(self.roi[0], self.roi[1], 5, 5, fill=None)

    def on_move_press(self, event):
        self.roi[2], self.roi[3] = (event.x, event.y)
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


class PageThree(Frame):
    # THE THIRD FRAME OF CONFIG TOOL USED TO DEFINE THE GROUND PLANE, CALCULATE THE TRANSFORMATION AND RECORD DETAILS
    def __init__(self, parent, controller):
        # INITIALISE THE FRAME
        Frame.__init__(self, parent)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=216)
        # GET THE CURRENT FRAME AND CONVERT
        self.frame = cam.read()
        self.width = int(self.frame.shape[1] / 1.25)
        self.height = int(self.frame.shape[0] / 1.25)
        self.im = Image.fromarray(self.frame, 'RGB')
        self.im = self.im.resize((self.width, self.height), Image.ANTIALIAS)
        self.image = ImageTk.PhotoImage(self.im)
        # CREATE Canvas FOR THE IMAGE WHICH ALLOWS FOR DRAWING
        self.canvas = Canvas(self, width=self.width, height=self.height, cursor="cross")
        self.canvas.grid(row=0, columnspan=4)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        # CREATE LABEL TO HOLD THE WARPED IMAGE TO CHECK IT LOOKS CORRECT
        self.width_t = int(self.frame.shape[1] * 0.25)
        self.height_t = int(self.frame.shape[0] * 0.25)
        self.label = Label(self, image=self.image, width=self.width_t, height=self.height_t)
        self.label.grid(row=0, column=4)
        self.label.image = self.im
        # CREATE LABEL TO DISPLAY THE CURRENTLY HELD GROUP PLANE POINTS
        Label(self, text="Ground Plane Points").grid(row=1, column=0)
        self.l1 = Label(self, text="NONE")
        self.l1.grid(row=1, column=1)

        # CREATE LABELS FOR ENTRY BOXES
        Label(self, text="Longitude and Latitude of reference location").grid(row=2, column=0)
        Label(self, text="Compass Orientation (degrees)").grid(row=2, column=3)

        # ADD ENTRIES FOR THE VARIOUS TEXT BOXES AND LABELS FOR DESCRIPTIONS
        self.e1 = Entry(self, justify='center')
        self.e2 = Entry(self, justify='center')
        self.e4 = Entry(self, justify='center')
        self.e1.insert(10, "51.40168")
        self.e2.insert(10, "-0.30271")
        self.e4.insert(10, "174")
        self.e1.grid(row=2, column=1)
        self.e2.grid(row=2, column=2)
        self.e4.grid(row=2, column=4)

        b1 = Button(self, text='Quit', command=parent.quit)
        b1.grid(row=3, column=0, sticky=W, pady=4)
        b2 = Button(self, text='Show Top Down', command=lambda: self.draw_top_down())
        b2.grid(row=3, column=1, sticky=W, pady=4)
        b3 = Button(self, text='ROI Top Down', command=lambda: self.roi_top_down(controller))
        b3.grid(row=3, column=2, sticky=W, pady=4)
        b4 = Button(self, text='Go Back', command=lambda: controller.show_frame("PageTwo"))
        b4.grid(row=3, column=3, sticky=W, pady=4)
        b5 = Button(self, text='Next Page', command=lambda: controller.show_frame("PageOne"))
        b5.grid(row=3, column=4, sticky=W, pady=4)

        # FIRST 4 POINTS ARE THE GROUND PLANE SECOND FOUR ARE REFERENCE POINTS TO CHECK IT MAKES SENSE
        self.ref_pt = [[50, 50], [300, 50], [50, 300], [300, 300], [100, 100]]

        # DRAWING THE GROUND PLANE
        self.intPt = []
        self.clone = []
        self.warped = []
        self.drawing = False
        self.current_point = -1

        self.draw_image()
        self.update_config()

    def update_config(self):
        # RESCALE THE POINTS TO ALLOW FOR THE SMALLER IMAGE
        t = [[int(self.ref_pt[0][0] * 1.25), int(self.ref_pt[0][1] * 1.25)],
             [int(self.ref_pt[1][0] * 1.25), int(self.ref_pt[1][1] * 1.25)],
             [int(self.ref_pt[2][0] * 1.25), int(self.ref_pt[2][1] * 1.25)],
             [int(self.ref_pt[3][0] * 1.25), int(self.ref_pt[3][1] * 1.25)],
             [int(self.ref_pt[4][0] * 1.25), int(self.ref_pt[4][1] * 1.25)]]
        config.ref_pt = t
        config.ground_plane_position = [float(self.e1.get()), float(self.e2.get())]
        config.ground_plane_orientation = int(self.e4.get())

    def draw_image(self):
        # DELETE EVERYTHING OFF THE CANVAS
        self.canvas.delete("all")
        # RE-DRAW IMAGE
        self.frame = cam.read()
        self.frame = self.frame[config.roi[1]:config.roi[3], config.roi[0]:config.roi[2], :]
        self.width = int(self.frame.shape[1] / 1.25)
        self.height = int(self.frame.shape[0] / 1.25)
        self.im = Image.fromarray(self.frame, 'RGB')
        self.im = self.im.resize((self.width, self.height), Image.ANTIALIAS)
        self.image = ImageTk.PhotoImage(self.im)
        self.canvas.create_image(0, 0, anchor="nw", image=self.image)
        # DRAW LINES AND OVALS
        self.canvas.create_line(self.ref_pt[0][0], self.ref_pt[0][1], self.ref_pt[1][0], self.ref_pt[1][1],
                                self.ref_pt[1][0], self.ref_pt[1][1], self.ref_pt[3][0], self.ref_pt[3][1],
                                self.ref_pt[3][0], self.ref_pt[3][1], self.ref_pt[2][0], self.ref_pt[2][1],
                                self.ref_pt[2][0], self.ref_pt[2][1], self.ref_pt[0][0], self.ref_pt[0][1], width=3)

        self.canvas.create_oval(self.ref_pt[0][0], self.ref_pt[0][1], self.ref_pt[0][0], self.ref_pt[0][1], width=5)
        self.canvas.create_oval(self.ref_pt[1][0], self.ref_pt[1][1], self.ref_pt[1][0], self.ref_pt[1][1], width=5)
        self.canvas.create_oval(self.ref_pt[2][0], self.ref_pt[2][1], self.ref_pt[2][0], self.ref_pt[2][1], width=5)
        self.canvas.create_oval(self.ref_pt[3][0], self.ref_pt[3][1], self.ref_pt[3][0], self.ref_pt[3][1], width=5)
        self.canvas.create_oval(self.ref_pt[4][0], self.ref_pt[4][1], self.ref_pt[4][0], self.ref_pt[4][1], width=6)
        self.canvas.create_text(self.ref_pt[0][0], self.ref_pt[0][1] + 5, fill="darkblue", font="Ariel 10 bold",
                                text="X_0, Y_1")
        self.canvas.create_text(self.ref_pt[1][0], self.ref_pt[1][1] + 5, fill="darkblue", font="Ariel 10 bold",
                                text="X_1, Y_1")
        self.canvas.create_text(self.ref_pt[2][0], self.ref_pt[2][1] + 5, fill="darkblue", font="Ariel 10 bold",
                                text="X_0, Y_0")
        self.canvas.create_text(self.ref_pt[3][0], self.ref_pt[3][1] + 5, fill="darkblue", font="Ariel 10 bold",
                                text="X_1, Y_0")
        self.canvas.create_text(self.ref_pt[4][0], self.ref_pt[4][1] + 5, fill="darkblue", font="Ariel 10 bold",
                                text="Ref Loc")

    def draw_top_down(self):
        # USING THE ALREADY COMPUTED TRANSFORM, RETURN THE WARPED IMAGE FROM config_tools AND DISPLAY
        self.warped = config.perspective_transform(self.frame)
        self.warped = config.transform_points(self.warped)
        self.warped = config.shrink_image(self.warped, both=True)
        self.warped = Image.fromarray(self.warped, 'RGB')
        self.warped = self.warped.resize((self.width_t, self.height_t), Image.ANTIALIAS)
        self.warped = ImageTk.PhotoImage(self.warped)
        self.label.config(image=self.warped)
        self.label.image = self.warped

    def roi_top_down(self, controller):
        self.warped = config.perspective_transform(self.frame)
        self.warped = config.shrink_image(self.warped)
        self.warped = Image.fromarray(self.warped, 'RGB')
        self.warped = self.warped.resize((self.width_t, self.height_t), Image.ANTIALIAS)
        self.warped = ImageTk.PhotoImage(self.warped)
        controller.show_frame("PageFour")

    def on_button_press(self, event):
        # save mouse drag start position
        x = event.x
        y = event.y

        self.drawing = True
        # FIND THE SELECTED POINT
        for i in range(len(self.ref_pt)):
            if abs(x - self.ref_pt[i][0]) < 10:
                if abs(y - self.ref_pt[i][1]) < 10:
                    self.current_point = i
                    break

    def on_move_press(self, event):
        x = event.x
        y = event.y
        # LIMIT DRAG TO WITHIN IMAGE DIMENSIONS
        if x < 0:
            x = 0
        elif x > self.width:
            x = self.width

        if y < 0:
            y = 0
        elif y > self.height:
            y = self.height

        if self.drawing is True:
            # print('MOVING WITH MOUSE DOWN')
            if self.current_point is not -1:
                self.ref_pt[self.current_point] = (x, y)

    def on_button_release(self, event):
        self.drawing = False
        self.current_point = -1
        self.update_config()


class PageFour(Frame):
    # THE SECOND FRAME OF CONFIG TOOL USED TO DEFINE THE REGION OF INTEREST
    def __init__(self, parent, controller):
        # INITIALISE THE FRAME
        Frame.__init__(self, parent)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=216)
        # GET THE CURRENT FRAME AND CONVERT
        frame = config.warped_image
        self.width = frame.shape[1]
        self.height = frame.shape[0]
        self.w_scale = 1
        self.h_scale = 1
        self.im = Image.fromarray(frame, 'RGB')
        self.im = self.im.resize((self.width, self.height), Image.ANTIALIAS)
        self.image = ImageTk.PhotoImage(self.im)
        # CREATE Canvas FOR THE IMAGE WHICH ALLOWS FOR DRAWING
        self.canvas = Canvas(self, width=self.width, height=self.height, cursor="cross")
        self.canvas.grid(row=0, columnspan=5)
        # BIND FUNCTIONS TO THE EVENT CALLBACKS
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        # self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # CREATE LABEL TO REFLECT CONTENT OF THE ConfigTool (UPDATED IN refresher())
        Label(self, text="Top Down View: Region of Interest Points").grid(row=1, column=1)
        self.l1 = Label(self, text="NONE")
        self.l1.grid(row=1, column=2)

        Label(self, text="Size X (m)").grid(row=2, column=3)
        Label(self, text="Size Y (m)").grid(row=2, column=5)

        # ADD ENTRIES FOR THE VARIOUS TEXT BOXES AND LABELS FOR DESCRIPTIONS
        self.e1 = Entry(self, justify='center')
        self.e2 = Entry(self, justify='center')
        self.e1.insert(10, "0")
        self.e2.insert(10, "0")
        self.e1.grid(row=2, column=4)
        self.e2.grid(row=2, column=6)

        # CREATE BUTTONS FOR NAVIGATION
        b2 = Button(self, text='Go Back', command=lambda: self.go_back(controller))
        b2.grid(row=3, column=3, sticky=W, pady=4)

        # VARIABLES USED IN OPERATION
        self.rect = None
        self.roi = [0, 0, self.width, self.height]

        # DRAW THE IMAGE
        self.draw_image()
        self.update_config()

    def go_back(self, controller):
        self.update_config()
        controller.show_frame("PageThree")

    def update_config(self):
        config.ground_plane_roi = self.roi
        config.ground_plane_size = [int(self.e1.get()), int(self.e2.get())]

    def draw_image(self):
        # frame = config.perspective_transform(config.warped_image)
        # frame = config.shrink_image(frame)
        frame = config.warped_image
        self.im = Image.fromarray(frame, 'RGB')
        self.w_scale = frame.shape[1] / self.width
        self.h_scale = frame.shape[0] / self.height
        self.im = self.im.resize((self.width, self.height), Image.ANTIALIAS)
        self.image = ImageTk.PhotoImage(self.im)
        self.canvas.create_image(0, 0, anchor="nw", image=self.image)
        if self.rect:
            self.rect = self.canvas.create_rectangle(int(self.roi[0] / self.w_scale), int(self.roi[1] / self.h_scale),
                               int(self.roi[2] / self.w_scale), int(self.roi[3] / self.h_scale), outline='white')

    def draw_rect(self):
        self.rect = self.canvas.create_rectangle(int(self.roi[0] / self.w_scale), int(self.roi[1] / self.h_scale),
                                                 int(self.roi[2] / self.w_scale), int(self.roi[3] / self.h_scale),
                                                 outline='white')

    def on_button_press(self, event):
        # save mouse drag start position
        x = event.x
        y = event.y

        # create rectangle if not yet exist
        if not self.rect:
            self.rect = self.canvas.create_rectangle(x, y, 5, 5, fill=None, outline='white')
        self.roi[0] = int(x * self.w_scale)
        self.roi[1] = int(y * self.h_scale)

    def on_move_press(self, event):
        x, y = (event.x, event.y)
        # LIMIT DRAG TO WITHIN IMAGE DIMENSIONS
        if x < 0:
            x = 0
        elif x > self.width:
            x = self.width

        if y < 0:
            y = 0
        elif y > self.height:
            y = self.height

        # expand rectangle as you drag the mouse
        self.canvas.coords(self.rect, int(self.roi[0] / self.w_scale), int(self.roi[1] / self.h_scale), x, y)
        # self.canvas.create_text(self.roi[0], self.roi[1] + 5, fill="darkblue", font="Ariel 10 bold", text="X_0, Y_1")
        # self.canvas.create_text(self.roi[3], self.roi[1] + 5, fill="darkblue", font="Ariel 10 bold", text="X_1, Y_1")
        # self.canvas.create_text(self.roi[0], self.roi[2] + 5, fill="darkblue", font="Ariel 10 bold", text="X_0, Y_0")
        # self.canvas.create_text(self.roi[3], self.roi[2] + 5, fill="darkblue", font="Ariel 10 bold", text="X_1, Y_0")
        self.roi[2] = int(x * self.w_scale)
        self.roi[3] = int(y * self.h_scale)


if __name__ == '__main__':
    if _args.seq_location is None:
        cam = CamVideoStreamer(_args.rtsp)
        cam.start()
    else:
        cam = ImageSequenceStreamer(_args.seq_location, _args.start_frame, (_args.x_size, _args.y_size))
    if cam.open():
        print("CAMERA CONNECTION IS ESTABLISHED.")
        config = ConfigTools()
        config_app = ConfigApp()
        config_app.mainloop()
        cam.stop()
        exit(-1)
    else:
        print("FAILED TO CONNECT TO CAMERA.")
        exit(-1)
