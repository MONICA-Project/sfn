# ground_plane_gui.py
"""The Ground Plane GUI classes for the KU Cam Config App
"""
from tkinter import *
from PIL import Image, ImageTk

__version__ = '0.1'
__author__ = 'Rob Dupre (KU)'


class GroundPlane(Frame):
    # THE THIRD FRAME OF CONFIG TOOL USED TO DEFINE THE GROUND PLANE, CALCULATE THE TRANSFORMATION AND RECORD DETAILS
    def __init__(self, parent, controller, cam_stream):
        # INITIALISE THE FRAME
        Frame.__init__(self, parent)
        self.cam = cam_stream
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=216)
        # GET THE CURRENT FRAME AND CONVERT
        self.frame = controller.cam_frame
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

        # CREATE LABELS FOR ENTRY BOXES
        Label(self, text="Ground Plane Points").grid(row=1, column=0, sticky=E)
        Label(self, text="Compass Orientation (degrees)").grid(row=2, column=0, sticky=E)

        # ADD ENTRIES FOR THE VARIOUS TEXT BOXES AND LABELS FOR DESCRIPTIONS
        self.l1 = Label(self, text="NONE")
        self.l1.grid(row=1, column=1, columnspan=2)
        self.e3 = Entry(self, justify='center')
        self.e3.insert(10, "174")
        self.e3.grid(row=2, column=1)

        b1 = Button(self, text='Quit', command=parent.quit)
        b1.grid(row=4, column=0, sticky=W, pady=4)
        b2 = Button(self, text='Show Top Down', command=lambda: self.draw_top_down())
        b2.grid(row=4, column=1, sticky=W, pady=4)
        b3 = Button(self, text='ROI Top Down', command=lambda: self.roi_top_down(controller))
        b3.grid(row=4, column=2, sticky=W, pady=4)
        b4 = Button(self, text='Go Back', command=lambda: self.go_back(self.controller))
        b4.grid(row=4, column=3, sticky=E, pady=4)
        b5 = Button(self, text='Next Page', command=lambda: self.next_page(self.controller))
        b5.grid(row=4, column=4, sticky=W, pady=4)

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

    def go_back(self, controller):
        self.update_config()
        controller.show_frame("CrowdMask")

    def next_page(self, controller):
        self.update_config()
        controller.show_frame("FlowROIs")

    def update_config(self):
        # RESCALE THE POINTS TO ALLOW FOR THE SMALLER IMAGE
        ratio = self.controller.ratio
        t = [[int((self.ref_pt[0][0] * 1.25) / ratio), int((self.ref_pt[0][1] * 1.25) / ratio)],
             [int((self.ref_pt[1][0] * 1.25) / ratio), int((self.ref_pt[1][1] * 1.25) / ratio)],
             [int((self.ref_pt[2][0] * 1.25) / ratio), int((self.ref_pt[2][1] * 1.25) / ratio)],
             [int((self.ref_pt[3][0] * 1.25) / ratio), int((self.ref_pt[3][1] * 1.25) / ratio)],
             [int((self.ref_pt[4][0] * 1.25) / ratio), int((self.ref_pt[4][1] * 1.25) / ratio)]]
        self.controller.config_tools.ref_pt = t
        self.controller.config_tools.ground_plane_orientation = int(self.e3.get())

    def draw_image(self):
        # DELETE EVERYTHING OFF THE CANVAS
        self.canvas.delete("all")
        # RE-DRAW IMAGE
        self.frame = self.controller.cam_frame
        # self.frame = self.frame[self.controller.config_tools.frame_roi[1]:self.controller.config_tools.frame_roi[3],
        #                         self.controller.config_tools.frame_roi[0]:self.controller.config_tools.frame_roi[2],
        #                         :]
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
                                self.ref_pt[2][0], self.ref_pt[2][1], self.ref_pt[0][0], self.ref_pt[0][1], width=1)

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
        self.warped = self.controller.config_tools.perspective_transform(self.frame)
        self.warped = self.controller.config_tools.transform_points(self.warped)
        self.warped = self.controller.config_tools.shrink_image(self.warped, both=True)
        self.warped = Image.fromarray(self.warped, 'RGB')
        self.warped = self.warped.resize((self.width_t, self.height_t), Image.ANTIALIAS)
        self.warped = ImageTk.PhotoImage(self.warped)
        self.label.config(image=self.warped)
        self.label.image = self.warped

    def roi_top_down(self, controller):
        self.warped = self.controller.config_tools.perspective_transform(self.frame)
        self.warped = self.controller.config_tools.shrink_image(self.warped)
        self.warped = Image.fromarray(self.warped, 'RGB')
        self.warped = self.warped.resize((self.width_t, self.height_t), Image.ANTIALIAS)
        self.warped = ImageTk.PhotoImage(self.warped)
        controller.show_frame("TopDown")

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


class TopDown(Frame):
    # THE SECOND FRAME OF CONFIG TOOL USED TO DEFINE THE REGION OF INTEREST
    def __init__(self, parent, controller):
        # INITIALISE THE FRAME
        Frame.__init__(self, parent)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=216)
        # GET THE CURRENT FRAME AND CONVERT
        frame = self.controller.config_tools.warped_image
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
        Label(self, text="Top Down View: Region of Interest Points").grid(row=1, column=0, sticky=E)
        self.l1 = Label(self, text="NONE")
        self.l1.grid(row=1, column=1, columnspan=2)

        Label(self, text="Longitude and Latitude of reference location").grid(row=2, column=0, sticky=E)
        Label(self, text="Size X (m)").grid(row=3, column=0, sticky=E)
        Label(self, text="Size Y (m)").grid(row=3, column=2, sticky=E)

        # ADD ENTRIES FOR THE VARIOUS TEXT BOXES AND LABELS FOR DESCRIPTIONS
        self.e1 = Entry(self, justify='center')
        self.e2 = Entry(self, justify='center')
        self.e3 = Entry(self, justify='center')
        self.e4 = Entry(self, justify='center')
        self.e1.insert(10, "0")
        self.e2.insert(10, "0")
        self.e3.insert(10, "51.40168")
        self.e4.insert(10, "-0.30271")
        self.e1.grid(row=3, column=1)
        self.e2.grid(row=3, column=3)
        self.e3.grid(row=2, column=1)
        self.e4.grid(row=2, column=2)

        # CREATE BUTTONS FOR NAVIGATION
        b2 = Button(self, text='Go Back', command=lambda: self.go_back(controller))
        b2.grid(row=4, column=3, sticky=W, pady=4)

        # VARIABLES USED IN OPERATION
        self.rect = None
        self.roi = [0, 0, self.width, self.height]

        # DRAW THE IMAGE
        self.draw_image()
        self.update_config()

    def go_back(self, controller):
        self.update_config()
        controller.show_frame("GroundPlane")

    def update_config(self):
        self.controller.config_tools.ground_plane_roi = self.roi
        self.controller.config_tools.ground_plane_size = [int(self.e1.get()), int(self.e2.get())]
        self.controller.config_tools.ground_plane_position = [float(self.e3.get()), float(self.e4.get())]

    def draw_image(self):
        # frame = self.controller.config_tools.perspective_transform(self.controller.config_tools.warped_image)
        # frame = self.controller.config_tools.shrink_image(frame)
        frame = self.controller.config_tools.warped_image
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
        if x > int(self.roi[0] / self.w_scale) + 2 and y > int(self.roi[1] / self.h_scale) + 2:
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
