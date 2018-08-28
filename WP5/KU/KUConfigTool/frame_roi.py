# frame_roi.py
"""The Frame ROI GUI class for the KU Cam Config App
"""
from tkinter import *
from PIL import Image, ImageTk

__version__ = '0.1'
__author__ = 'Rob Dupre (KU)'


class FrameROI(Frame):
    # THE SECOND FRAME OF CONFIG TOOL USED TO DEFINE THE REGION OF INTEREST
    def __init__(self, parent, controller, cam_stream):
        # INITIALISE THE FRAME
        Frame.__init__(self, parent)
        self.controller = controller
        self.cam = cam_stream
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=216)
        # GET THE CURRENT FRAME AND CONVERT
        self.image = controller.get_frame()
        self.width = self.image.width()
        self.height = self.image.height()
        # CREATE Canvas FOR THE IMAGE WHICH ALLOWS FOR DRAWING
        self.canvas = Canvas(self, width=self.width, height=self.height, cursor="cross")
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
