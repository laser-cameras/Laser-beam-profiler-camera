Open-source laser beam profiling application using Python.

Required packages:  
- PyQt5
- numpy
- matplotlib
- opencv-python
- cv2_enumerate_cameras

Source files:  
- beam_profiler_gui.py
- camera.py
- cb.png

Low cost Arducam UVC USB camera 20MP AR2020 B0511C (with enclosure) $265.  
https://www.arducam.com/presalesarducam-20mp-ar2020-monochrome-manual-focus-usb-3-0-camera.html  
Other cameras (UVC/web-cam type) may be used but compatibility is not guaranteed and minor modification of the code may be required.

<img width="325" height="325" alt="image" src="https://github.com/user-attachments/assets/425f62e0-1d45-4896-9e50-6a6e62cd9fdf" />

Sensor AR2020  
Monochrome rolling shutter  
Native resolution 20MP 5120 x 3840, 1.4 um pixel size  
Application resolution (4x4 binning) 1280 x 960, 5.6 um pixel size, 8 bit depth  
Sensor format: 1/8"  
Exposure: 150 us to 640 ms  

[option 1] S-mount (M12) to C-mount adapter. Edmund Optics 63-974 $60  
https://www.edmundoptics.com/p/male-s-to-female-c-adapter/18686/?srsltid=AfmBOoq1u2u2iRjV2_g_2uVE0Q3QIOe_mvLaDkdhgzAN5ILeAnjkB363

[option 2] C-mount to SM1 mount adapter. Thorlabs SM1A9 $23  
https://www.thorlabs.com/thorproduct.cfm?partnumber=SM1A9

Hardware installation instructions:
1. Remove the M12 lens attached to the enclosure of the B0511C camera. There may be glue dot(s) securing the lens thread to the camera body. Break the glue dot(s) as needed and/or use pliers to unthread the lens
2. Attach option 1 and 2 as desired to convert the camera from S-mount to C-mount or SM1 mount
3. Install desired 1" optic in the thread (ND, bandpass, tube lens etc)
4. Attach 1/4-20 post to the body of the camera
5. Mount on optical system in beam path as desired
6. Connect USB-C cable to the camera and PC

<img width="234" height="228" alt="camera_ex" src="https://github.com/user-attachments/assets/e7fba40b-9cac-4179-9cd2-8146edfdbca0" />  
<br>

<img width="470" height="692" alt="1_1" src="https://github.com/user-attachments/assets/7ae555cf-f386-4c32-ac8d-9e73b40c56af" />
<img width="470" height="692" alt="2" src="https://github.com/user-attachments/assets/71d6e12a-6ccb-4562-84d2-50419f3b13ed" />


Beam profiling software features:
- Camera raw image feed
- Beam profiling image feed (false color)
- Manual ROI placement with centroid and radius
- Auto ROI tracking
- Centroid tracking
- Centroid and beam width (d4sigma) readout
- Reference crosshair placement
- Power (integrated counts) readout
- Exposure setting
- Auto exposure
- Saturated pixel detection
- fps counter
- Save instantaneous data
  - Camera image
  - Beam profile image
  - X centroid lineout plot
  - Y centroid lineout plot
  - Measurements csv: Camera settings, beam centroid, D4sigma, Aperture (ROI), Exposure, Max signal, Power, saturated pixels, camera identifier
- Logging (continuous measurements data saving)
- Connect to multiple cameras on a single PC
  - If logging is enabled while multiple cameras are connected, the software will loop through the cameras with auto ROI, auto exposure and record data
  - The software will naively connect to any webcams the PC has. This can be bypassed by determining the path of the camera, assigning an identifier and only allowing beam profiling cameras to be used (see init_camera function in gui script)
- To run from command line:
  - cd (working-directory)
  - py beam_profiler_gui.py

