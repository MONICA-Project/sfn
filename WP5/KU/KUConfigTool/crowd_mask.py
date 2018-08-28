# crowd_mask.py
"""The Crowd Mask GUI class for the KU Cam Config App
"""
from tkinter import *
from PIL import Image, ImageTk
import numpy as np
import cv2

__version__ = '0.2'
__author__ = 'Rob Dupre (KU)'


class CrowdMask(Frame):
    # THE FRAME OF THE CONFIG TOOL USED TO DEFINE A MASK TO IGNORE AREAS OF THE FRAME
    def __init__(self, parent, controller, cam_stream):
        # INITIALISE THE FRAME
        Frame.__init__(self, parent)
        self.controller = controller
        self.cam = cam_stream
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=216)
        # GET THE CURRENT FRAME AND CONVERT
        self.image = controller.current_frame
        self.width = self.image.width()
        self.height = self.image.height()
        self.stream_w = controller.stream_w
        self.stream_h = controller.stream_h
        self.ratio = controller.ratio
        self.frame = controller.cam_frame
        self.mask = np.zeros([self.height, self.width])
        # CREATE Canvas FOR THE IMAGE WHICH ALLOWS FOR DRAWING
        self.canvas = Canvas(self, width=self.width, height=self.height, cursor="cross")
        self.canvas.grid(row=0, columnspan=5)

        # VARIABLES USED IN OPERATION
        self.rects = []
        self.rois = []
        self.roi_count = 0

        # BIND FUNCTIONS TO THE EVENT CALLBACKS
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<ButtonPress-3>", self.on_right_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # CREATE LABEL TO REFLECT CONTENT OF THE ConfigTool (UPDATED IN refresher())
        Label(self, text="Num Rectangles").grid(row=1, column=0, sticky=E)
        Label(self, text="Longitude and Latitude").grid(row=2, column=0, sticky=E)
        Label(self, text="Camera Height (m)").grid(row=2, column=3, sticky=E)
        Label(self, text="Tilt Angle (degrees)").grid(row=3, column=0, sticky=E)
        Label(self, text="Camera bearing (degrees)").grid(row=3, column=2, sticky=E)

        self.l1 = Label(self, text=str(self.roi_count))
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
        b2 = Button(self, text='Reset Rois', command=lambda: self.reset_rois())
        b2.grid(row=4, column=2, sticky=W, pady=4)
        b3 = Button(self, text='Go Back', command=lambda: self.go_back(self.controller))
        b3.grid(row=4, column=3, sticky=E, pady=4)
        b4 = Button(self, text='Next Page', command=lambda: self.next_page(self.controller))
        b4.grid(row=4, column=4, sticky=W, pady=4)

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
        self.controller.config_tools.crowd_mask = cv2.resize(self.mask, dsize=(self.stream_w, self.stream_h))
        self.controller.config_tools.camera_position = [float(self.e1.get()), float(self.e2.get())]
        self.controller.config_tools.camera_height = float(self.e3.get())
        self.controller.config_tools.camera_tilt = int(self.e4.get())
        self.controller.config_tools.camera_bearing = int(self.e5.get())

    def reset_rois(self):
        self.rects = []
        self.rois = []
        self.roi_count = 0
        self.update_config()
        self.mask = np.zeros([self.height, self.width])
        self.draw_rect()

    def _draw_image(self):
        if self.mask.shape[0] != self.height and self.mask.shape[1] != self.width:
            self.mask = cv2.resize(self.mask, (self.width, self.height))
            self.mask[self.mask > 0] = 1
            self.controller.config_tools.crowd_mask = self.mask

        t_frame = self.frame * ((np.dstack((self.mask, self.mask, self.mask)) + 1) * 0.5)
        self.im = Image.fromarray(t_frame.astype(np.uint8), 'RGB')
        self.image = ImageTk.PhotoImage(self.im)
        self.canvas.create_image(0, 0, anchor="nw", image=self.image)

    def draw_rect(self):
        self.canvas.delete("all")
        self._draw_image()
        self.roi_count = len(self.rois)

    def on_button_press(self, event):
        # save mouse drag start position
        self.rois.append([0, 0, 0, 0])
        self.rois[self.roi_count][0] = event.x
        self.rois[self.roi_count][1] = event.y
        self.rois[self.roi_count][2] = event.x + 5
        self.rois[self.roi_count][3] = event.y + 5

        # ADD RECTANGLE TO RECTANGLE LIST
        self.rects.append(self.canvas.create_rectangle(self.rois[self.roi_count][0], self.rois[self.roi_count][1],
                                                       self.rois[self.roi_count][2], self.rois[self.roi_count][3],
                                                       fill=None, width=3))

    def on_right_button_press(self, event):
        # IF THERE IS AN roi THEN REMOVE IT AND REDRAW THE FRAME
        if len(self.rois) > 0:
            self.mask[
                self.rois[-1][1]:self.rois[-1][3],
                self.rois[-1][0]:self.rois[-1][2]] = 0
            self.rois.pop(-1)
            self.draw_rect()

    def on_move_press(self, event):
        x, y = (event.x, event.y)
        # LIMIT DRAG ONLY DOWN RIGHT
        if x > self.rois[self.roi_count][0] + 2 and y > self.rois[self.roi_count][1] + 2:
            self.rois[self.roi_count][2] = x
            self.rois[self.roi_count][3] = y
            # LIMIT DRAG TO WITHIN IMAGE DIMENSIONS
            if self.rois[self.roi_count][2] < 0:
                self.rois[self.roi_count][2] = 0
            elif self.rois[self.roi_count][2] > self.width:
                self.rois[self.roi_count][2] = self.width

            if self.rois[self.roi_count][3] < 0:
                self.rois[self.roi_count][3] = 0
            elif self.rois[self.roi_count][3] > self.height:
                self.rois[self.roi_count][3] = self.height

            # expand rectangle as you drag the mouse
            self.canvas.coords(self.rects[-1], self.rois[self.roi_count][0], self.rois[self.roi_count][1],
                               self.rois[self.roi_count][2], self.rois[self.roi_count][3])

    def on_button_release(self, event):
        self.mask[
            self.rois[self.roi_count][1]:self.rois[self.roi_count][3],
            self.rois[self.roi_count][0]:self.rois[self.roi_count][2]] = 1
        self.roi_count = self.roi_count + 1
        self.update_config()
        self.draw_rect()
