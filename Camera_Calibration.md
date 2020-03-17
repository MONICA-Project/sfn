
# Camera Calibration tutorial

The video datasteams from the cameras are required to be calibrated to facilitate data pre-processing for the various algorithms.

The instructions in this document outlines the steps to be carried out for calibration of the datasteams through the camera calibration app. Calibration is done for each camera datastream.

## Camera calibration tool

A pre-requisite is to obtain the ```RTSP stream URL``` of the camera along with the stream ```username``` and ```password```. An example RTSP stream may look as below.

> 'rtsp://root:pass@10.144.129.107/axis-media/media.amp'

The camera calibration tool can be revoked with the below command.

> python3 WP5/KU/KUConfigTool/camera_config.py --rtsp 'rtsp://root:pass@10.144.129.107/axis-media/media.amp'

The calibration tool opens with a GUI and streaming from the camera.

![logo](./Images/cam-cal.png)

## Calibration process

The calibration process follows the below process.

1. Enter camera ID preferably based on the pilot name and camera IP.
2. Enter ```Zone ID```. Pick something informative (example: Entrance or Main_gate)
3. Get a screenshot.

  ![logo](./Images/cam-cal-pg1.png)

4. Go to the ```Next Page```.
5. At the next page, the ```region of interest (RoI)``` where crowd/human movement is expected needs to be selected. This creates a mask on which the algorithms work. The RoI is selected by drawing boxes around the potential regions.
6. In the same window, key in camera ```longitude, Latitude, tilt angle, height``` and ```camera bearing angle``` (from the north).

  ![logo](./Images/cam-cal-pg2.png)

7. Go to the ```Next Page```.
8. Rearrange the box based on the 3m*3m square on the ground. This box helps in aligning for a top-down view of the camera frames.

  ![logo](./Images/cam-cal-pg3.png)
9. Use ```show top down``` to check out the top down view. if the ```compass orientation degree``` is correct the box should be up straight.
10. Go to ```ROI Top down```.
11. Draw the region of interest.
12. Keep the bottom left corner of the ROI box as the reference point, key in the estimated latitude and longitude of the reference point with the help of google maps. Next, enter the X and Y which are the size of ROI in meter, again use google maps to get an estimate dimensions.

  ![logo](./Images/cam-cal-pg4.png)

13. Click on ```Go back```.
14. Go to ```Next page```.
15. Draw the ROI for ```flow analysis```. Draw a box in somewhere suitable which many people may pass.
16. Go to the ```Next Page``` (it iterates to the first page).
17. Click on ```Save and Send```.

The aforementioned process creates two files - a text file in ```KUConfigTool``` folder and ```.PK``` file in ```cam_config``` folder.

Repeat the process for each camera.
