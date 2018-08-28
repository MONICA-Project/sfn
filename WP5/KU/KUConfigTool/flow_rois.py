# flow_rois.py
"""The Optical Flow ROI GUI class for the KU Cam Config App
"""
from tkinter import *
import numpy as np
from PIL import Image, ImageTk

__version__ = '0.1'
__author__ = 'Rob Dupre (KU)'


class FlowROI(Frame):
    # THE FRAME OF THE CONFIG TOOL USED TO DEFINE THE REGION OF INTEREST
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
        self.ratio = controller.ratio
        # CREATE Canvas FOR THE IMAGE WHICH ALLOWS FOR DRAWING
        self.canvas = Canvas(self, width=self.width, height=self.height, cursor="cross")
        self.canvas.grid(row=0, columnspan=5)
        # BIND FUNCTIONS TO THE EVENT CALLBACKS
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<ButtonPress-3>", self.on_right_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # CREATE LABEL TO REFLECT CONTENT OF THE ConfigTool (UPDATED IN refresher())
        Label(self, text="Region of Interest Points").grid(row=1, column=0, sticky=E)

        self.l1 = Label(self, text="NONE")
        self.l1.grid(row=1, column=1)

        # CREATE BUTTONS FOR NAVIGATION
        b1 = Button(self, text='Quit', command=parent.quit)
        b1.grid(row=4, column=0, sticky=W, pady=4)
        b2 = Button(self, text='Reset Rois', command=lambda: self.reset_rois())
        b2.grid(row=4, column=2, sticky=W, pady=4)
        b3 = Button(self, text='Go Back', command=lambda: self.go_back(self.controller))
        b3.grid(row=4, column=3, sticky=E, pady=4)
        b4 = Button(self, text='Next Page', command=lambda: self.next_page(self.controller))
        b4.grid(row=4, column=4, sticky=W, pady=4)

        # VARIABLES USED IN OPERATION
        self.rects = []
        self.rois = []
        self.roi_count = 0

        # DRAW THE IMAGE
        self._draw_image()
        self.update_config()

    def go_back(self, controller):
        self.update_config()
        controller.show_frame("GroundPlane")

    def next_page(self, controller):
        self.update_config()
        controller.show_frame("Main")

    def update_config(self):
        self.controller.config_tools.flow_rois = (np.array(self.rois) / self.ratio).astype(np.uint).tolist()

    def reset_rois(self):
        self.rects = []
        self.rois = []
        self.roi_count = 0
        self.update_config()
        self.draw_rect()

    def _draw_image(self):
        self.canvas.create_image(0, 0, anchor="nw", image=self.image)

    def draw_rect(self):
        self.canvas.delete("all")
        self._draw_image()
        self.roi_count = len(self.rois)
        for roi in self.rois:
            self.rects.append(self.canvas.create_rectangle(roi[0], roi[1], 5, 5, fill=None, width=3))
            self.canvas.coords(self.rects[-1], roi[0], roi[1], roi[2], roi[3])

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
        self.roi_count = self.roi_count + 1
        self.update_config()
