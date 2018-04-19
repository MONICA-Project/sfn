# flow_rois.py
"""The Optical Flow ROI GUI class for the KU Cam Config App
"""
from tkinter import *
from PIL import Image, ImageTk

__version__ = '0.1'
__author__ = 'Rob Dupre (KU)'


class FlowROI(Frame):
    # THE SECOND FRAME OF CONFIG TOOL USED TO DEFINE THE REGION OF INTEREST
    def __init__(self, parent, controller, cam_stream):
        # INITIALISE THE FRAME
        Frame.__init__(self, parent)
        self.controller = controller
        self.cam = cam_stream
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=216)
        # GET THE CURRENT FRAME AND CONVERT
        frame = self.cam.read()
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

        self.l1 = Label(self, text="NONE")
        self.l1.grid(row=1, column=1)

        # CREATE BUTTONS FOR NAVIGATION
        b1 = Button(self, text='Quit', command=parent.quit)
        b1.grid(row=4, column=0, sticky=W, pady=4)
        b2 = Button(self, text='Go Back', command=lambda: self.go_back(self.controller))
        b2.grid(row=4, column=3, sticky=E, pady=4)
        b2 = Button(self, text='Next Page', command=lambda: self.next_page(self.controller))
        b2.grid(row=4, column=4, sticky=W, pady=4)

        # VARIABLES USED IN OPERATION
        self.rect = None
        self.rois = [0, 0, self.width, self.height]

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
        self.controller.config_tools.flow_rois = self.rois

    def _draw_image(self):
        self.canvas.create_image(0, 0, anchor="nw", image=self.image)

    def draw_rect(self):
        self.canvas.delete("all")
        self._draw_image()
        self.rect = self.canvas.create_rectangle(self.rois[0], self.rois[1], 5, 5, fill=None)
        self.canvas.coords(self.rect, self.rois[0], self.rois[1], self.rois[2], self.rois[3])

    def on_button_press(self, event):
        # save mouse drag start position
        self.rois[0] = event.x
        self.rois[1] = event.y
        self.rois[2] = event.x + 5
        self.rois[3] = event.y + 5

        # create rectangle if not yet exist
        if not self.rect:
            self.rect = self.canvas.create_rectangle(self.rois[0], self.rois[1], self.rois[2], self.rois[3], fill=None)

    def on_move_press(self, event):
        x, y = (event.x, event.y)
        # LIMIT DRAG ONLY DOWN RIGHT
        if x > self.rois[0] + 1 and y > self.rois[1] + 1:
            self.rois[2] = x
            self.rois[3] = y
            # LIMIT DRAG TO WITHIN IMAGE DIMENSIONS
            if self.rois[2] < 0:
                self.rois[2] = 0
            elif self.rois[2] > self.width:
                self.rois[2] = self.width

            if self.rois[3] < 0:
                self.rois[3] = 0
            elif self.rois[3] > self.height:
                self.rois[3] = self.height

            # expand rectangle as you drag the mouse
            self.canvas.coords(self.rect, self.rois[0], self.rois[1], self.rois[2], self.rois[3])

    def on_button_release(self, event):
        self.update_config()