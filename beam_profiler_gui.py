#GitHub: laser-cameras
#Optical Engineer
#Custom laser beam image acquisition and beam profiling GUI
#The code has been tested on Windows11

#Version: v1.2
#This software is made available via GNU

#required imports
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread
import PyQt5
import numpy as np
import matplotlib.pyplot as plt
import cv2
import os
import datetime
from camera import Camera
import time
import math
from cv2_enumerate_cameras import enumerate_cameras
import traceback

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

#ignore command line warnings
import warnings
warnings.filterwarnings("ignore")

#main GUI window definitions
class Ui_MainWindow(object):
    #set camera resolution which will be passed through the whole program
    W, H = 1280, 960
    pixel_um = 5.6
    ROI_Tracking = False
    AUTO_EXP = False
    REFERENCE_CROSSHAIR = False
    currentIndex = 0
    
    #setup UI elements
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("Beam GUI")
        #resize the window
        MainWindow.setFixedSize(935, 666)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        #note: Qrect input params are: x, y, wx, wy
        self.tabWidget.setGeometry(QtCore.QRect(14, 8, 907, 828))
        self.tabWidget.setObjectName("tabWidget")
        #first tab is for "Camera" view
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.lineEdit = QtWidgets.QLineEdit(MainWindow)
        self.lineEdit.setGeometry(QtCore.QRect(156, 44, 539, 25))
        self.lineEdit.setObjectName("lineEdit")
        self.lineEdit.setText("Root directory: "+os.getcwd())
        self.label = QtWidgets.QLabel(MainWindow)
        self.label.setGeometry(QtCore.QRect(122, 45, 65, 21))
        self.label.setObjectName("label")
        #first pushbutton is connected to Run, which starts the image acquisition
        self.pushButton = QtWidgets.QPushButton(MainWindow)
        self.pushButton.setGeometry(QtCore.QRect(703, 45, 55, 23))
        self.pushButton.setObjectName("pushButton")
        self.textEdit_2 = QtWidgets.QTextEdit(self.tab)
        self.textEdit_2.setGeometry(QtCore.QRect(52, 660, 801, 100))
        self.textEdit_2.setObjectName("textEdit_2")
        self.tabWidget.addTab(self.tab, "")
        #second tab is for "Beam"
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 943, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        
        #labels for image power and exposure setting
        self.label_P = QtWidgets.QLabel(self.tab_2)
        self.label_P.setGeometry(QtCore.QRect(20,160,101,41))
        self.lcdNumber_P = QtWidgets.QLCDNumber(self.tab_2)
        self.lcdNumber_P.setGeometry(QtCore.QRect(20, 190, 81, 41))
        self.lcdNumber_P.display("0")
        self.lineEdit_setExp = QtWidgets.QLineEdit(self.tab_2)
        self.lineEdit_setExp.setGeometry(QtCore.QRect(20, 110, 80, 40))
        self.lineEdit_setExp.setText("-7")
        self.pushbutton_setExp = QtWidgets.QPushButton(self.tab_2)
        self.pushbutton_setExp.setGeometry(QtCore.QRect(20, 70, 80, 40))
        #label for showing number of saturated pixels
        self.label_sat = QtWidgets.QLabel(self.tab_2)
        self.label_sat.setFont(QtGui.QFont('Any',12))
        self.label_sat.setText("# Saturated Pixels: 0")
        self.label_sat.setGeometry(QtCore.QRect(210,540,250,30))
        
        #labels for fps and exposure value
        self.label_fps = QtWidgets.QLabel(MainWindow)
        self.label_fps.setGeometry(QtCore.QRect(800,608,71,41))
        self.label_fps.setFont(QtGui.QFont('Any',12))
        self.label_fps.setText("fps: ")
        self.label_fps.setHidden(True)
        self.label_exp_ms = QtWidgets.QLabel(MainWindow)
        self.label_exp_ms.setGeometry(QtCore.QRect(630,608,175,41))
        self.label_exp_ms.setFont(QtGui.QFont('Any',12))
        self.label_exp_ms.setText("Exposure (ms): ")
        self.label_exp_ms.setHidden(True)
        
        #widgets for displaying centroid and estimated beam width
        #labels say d4 sigma. lcd's show computed widths
        self.label_centroid = QtWidgets.QLabel(self.tab_2)
        self.label_centroid.setFont(QtGui.QFont('Any',12))
        self.label_centroid.setText("Centroid (x,y) = 0, 0")
        self.label_centroid.setGeometry(QtCore.QRect(450, 540, 250, 30))
        self.label_dx = QtWidgets.QLabel(self.tab_2)
        self.label_dx.setGeometry(QtCore.QRect(20,230,101,41))
        self.lcdNumber_dx = QtWidgets.QLCDNumber(self.tab_2)
        self.lcdNumber_dx.setGeometry(QtCore.QRect(20, 260, 81, 41))
        self.lcdNumber_dx.display(0)
        self.label_dy = QtWidgets.QLabel(self.tab_2)
        self.label_dy.setGeometry(QtCore.QRect(20,300,101,41))
        self.lcdNumber_dy = QtWidgets.QLCDNumber(self.tab_2)
        self.lcdNumber_dy.setGeometry(QtCore.QRect(20, 330, 81, 41))
        self.lcdNumber_dy.display(0)
        
        #widgets for adjustable aperture
        #labels say aperture x, y, radius. line edits allow for adjustable (digital) aperture
        self.label_apx = QtWidgets.QLabel(self.tab_2)
        self.label_apx.setGeometry(QtCore.QRect(20,380,101,41))
        self.lineEdit_apx = QtWidgets.QLineEdit(self.tab_2)
        self.lineEdit_apx.setGeometry(QtCore.QRect(20, 410, 80, 40))
        self.lineEdit_apx.setText(str(self.pixel_um*self.W / 2))
        self.label_apy = QtWidgets.QLabel(self.tab_2)
        self.label_apy.setGeometry(QtCore.QRect(20,440,101,41))
        self.lineEdit_apy = QtWidgets.QLineEdit(self.tab_2)
        self.lineEdit_apy.setGeometry(QtCore.QRect(20, 470, 80, 40))
        self.lineEdit_apy.setText(str(self.pixel_um*self.H / 2))
        self.label_apr = QtWidgets.QLabel(self.tab_2)
        self.label_apr.setGeometry(QtCore.QRect(20,500,111,40))
        self.lineEdit_apr = QtWidgets.QLineEdit(self.tab_2)
        self.lineEdit_apr.setGeometry(QtCore.QRect(20, 530, 80, 40))
        self.lineEdit_apr.setText(str(self.pixel_um*(self.H / 2 - 100)))
        
        #widgets for saving data
        self.pushButton_S = QtWidgets.QPushButton(MainWindow)
        self.pushButton_S.setGeometry(QtCore.QRect(765, 45, 55, 23))
        #widgets for logging data continuously
        self.pushButton_L = QtWidgets.QPushButton(MainWindow)
        self.pushButton_L.setGeometry(QtCore.QRect(827, 45, 55, 23))

        #create an image frame for raw image (downsampled)
        #the image frame hosts the "Camera" tab image
        #the beam frame hosts the "Beam" tab image + processing
        #the cb frame hosts the colorbar (manual containment to insert colorbar). Requires cb.png in root directory
        self.image_frame = QtWidgets.QLabel(self.tab)
        self.beam_frame = QtWidgets.QLabel(self.tab_2)
        self.cb_frame = QtWidgets.QLabel(self.tab_2)
        #cb.png is required to manually place a colorbar (containment for cv2 heat map and colorbar)
        colorbar = cv2.imread("cb.png")
        colorbar = cv2.cvtColor(colorbar, cv2.COLOR_RGB2BGR)
        self.cb_frame.move(790,49)
        imGUI = QtGui.QImage(colorbar.data, colorbar.shape[1], colorbar.shape[0], \
        colorbar.shape[1]*3, QtGui.QImage.Format_RGB888)
        self.cb_frame.setPixmap(QtGui.QPixmap.fromImage(imGUI))

        #new check buttons
        self.tracking = QtWidgets.QCheckBox(self.tab_2)
        self.tracking.setGeometry(QtCore.QRect(20,590,100,20))
        self.autoExp = QtWidgets.QCheckBox(self.tab_2)
        self.autoExp.setGeometry(QtCore.QRect(120,590,100,20))
        
        #manual reference crosshair
        self.reference = QtWidgets.QCheckBox(self.tab_2)
        self.reference.setGeometry(QtCore.QRect(230,590,190,20))
        self.lineEdit_refX = QtWidgets.QLineEdit(self.tab_2)
        self.lineEdit_refX.setGeometry(QtCore.QRect(410, 590, 45, 20))
        self.lineEdit_refX.setText(str(self.pixel_um*(self.W / 2)))
        self.lineEdit_refY = QtWidgets.QLineEdit(self.tab_2)
        self.lineEdit_refY.setGeometry(QtCore.QRect(465, 590, 45, 20))
        self.lineEdit_refY.setText(str(self.pixel_um*(self.H / 2)))
        #camera select list
        self.cameraSelect = QtWidgets.QComboBox(self.tab)
        self.cameraSelect.setGeometry(QtCore.QRect(120,55,100,20))
        for camera_num in range(len(enumerate_cameras(cv2.CAP_MSMF))):
        #self.cameraSelect.addItems(['Camera 0','Camera 1','Camera 2','Camera 3','Camera 4','Camera 5' \
                                    #    ,'Camera 6','Camera 7'])
            self.cameraSelect.addItems(['Camera {}'.format(camera_num)])
        self.cameraSelect.currentIndexChanged.connect(self.dropDownCamera)
        
        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        #connect the pushbuttons to start image capture, calibrate power meter, save data
        self.pushButton.clicked.connect(self.run)
        self.pushbutton_setExp.clicked.connect(self.exp)
        self.pushButton_S.clicked.connect(self.save)
        self.pushButton_L.clicked.connect(self.log)
        self.tracking.stateChanged.connect(self.checkedTracking)
        self.autoExp.stateChanged.connect(self.checkedAutoExp)
        self.reference.stateChanged.connect(self.checkedReference)
        
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    #set text for GUI elements
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Beam GUI"))
        self.label.setText(_translate("MainWindow", "Info:"))
        self.pushButton.setText(_translate("MainWindow", "Run"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Camera"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Beam"))
        self.label_P.setText(_translate("MainWindow", "Power (ct*1E4)"))
        self.pushbutton_setExp.setText(_translate("MainWindow", "Set Exp\n[-13,-1]"))
        self.label_dx.setText(_translate("MainWindow", "D4σx (μm)"))
        self.label_dy.setText(_translate("MainWindow", "D4σy (μm)"))
        self.label_apx.setText(_translate("MainWindow", "ROI x (μm)"))
        self.label_apy.setText(_translate("MainWindow", "ROI y (μm)"))
        self.label_apr.setText(_translate("MainWindow", "ROI Radius (μm)"))
        self.pushButton_S.setText(_translate("MainWindow", "Save"))
        self.pushButton_L.setText(_translate("MainWindow", "Log"))
        self.tracking.setText(_translate("MainWindow", "ROI tracking"))
        self.autoExp.setText(_translate("MainWindow", "Auto Exposure"))
        self.reference.setText(_translate("MainWindow", "Reference Crosshair (x,y) (μm)"))
        #self.cameraSelect.setText("MainWindow", "Camera #")
        
    #run image acquisition and processing thread
    RUNNING = False
    def run(self):
        try:
            if not self.RUNNING:
                self.threadA = captureThread(self, self.W, self.H)
                self.threadA.start()
                if self.threadA.camera != None:
                    self.RUNNING = True
                self.label_exp_ms.setHidden(False)
                self.label_fps.setHidden(False)
            else:
                self.lineEdit.setText("System already running")
        except Exception:
            traceback.print_exc()
            return

    #set camera exposure
    def exp(self):
        if not self.RUNNING:
            self.lineEdit.setText("Run the system before setting exposure")
        else:
            if -13 <= int(self.lineEdit_setExp.text()) <= -1:
                self.threadA.exp()
            else:
                self.lineEdit.setText("Enter valid exposure in range [-13,-1]")
                
    #log data
    def log(self):
        if self.RUNNING:
            if not self.threadA.LOGGING:
                self.threadA.LOGGING = True
                self.pushButton_L.setText("Stop")
                self.lineEdit.setText("Data logging started")
            else:
                self.threadA.LOGGING = False
                self.pushButton_L.setText("Log")
                self.lineEdit.setText("Data logging stopped")
                self.autoExp.setChecked(False)
        else:
            self.lineEdit.setText("Run the system before logging data")
            
    #save images as png (can support other filetypes if needed)
    #save measurements as csv
    def save(self):
        if self.RUNNING:
            self.threadA.SAVE_NOW = True
        else:
            self.lineEdit.setText("Run the system before saving data")
            
    #check ROI tracking
    def checkedTracking(self, checked):
        if checked:
            self.ROI_Tracking = True
        else:
            self.ROI_Tracking = False
            
    #check auto exposure setting
    def checkedAutoExp(self, checked):
        if checked:
            self.AUTO_EXP = True
        else:
            self.AUTO_EXP = False
            
    def checkedReference(self, checked):
        if checked:
            self.REFERENCE_CROSSHAIR = True
        else:
            self.REFERENCE_CROSSHAIR = False
            
    #drop down for camera selection
    def dropDownCamera(self, index):
        self.currentIndex = index

#thread which handles live image acquisition and beam image processing
#runs separately from main GUI thread to prevent hang ups
class captureThread(QThread):
    #variables which can be accessed across functions and threads
    image_live = np.empty(1) #live camera image
    camera = None #camera variable for Camera
    MainWindow = None #MainWindow passed to thread so thread can modify UI elements
    SAVE_NOW = False #flag to save all data once
    LOGGING = False #flag to continuously log data
    FRAMES_INIT = False #used to set camera and beam frame sizes and locations to draw images on
    pix_sum, pix_max, sat_num = 0,0,0 #used for power and signal level
    count_x,count_y,count_r = 0,0,0 #used to reset aperture values if input is left blank
    mask_x, mask_y, mask_r = 1296,972,880 #mask values for digital aperture. Changes based on text input
    W = 1280 #camera/image width to be set
    H = 960 #camera/image height to be set
    pixel_um = 5.6 #multiply a pixel width by 5.6 micron to get physical width #SENSOR DEPENDENT
    exposure_dict = {-1:640, -2:320, -3:160, -4:80, -5:40, -6:20, -7:10, -8:5, -9:2.5, -10:1.25,\
        -11:.65, -12:.312, -13:.150} #exposure dict, values are related to exposure time in ms
    centroid_x_save = int(1280/2) #centroid tracking X
    centroid_y_save = int(960/2) #centroid tracking Y
    d4s_major_save = int(380)
    centroid_x_save_init, centroid_y_save_init, d4s_major_save_init = centroid_x_save, centroid_y_save, d4s_major_save# fix to allow autoROI to reset between different cameras
    count = 1
    currentCamera = 0
    scale = 2
    path = ''
    camera_designator = ''
    LOGGING_CNT_THRESHOLD = 10000
    fps_time1 = 0
    fps_time2 = 0
    fps_counter = 0
    fps_averaging = 10 #number of frames to average the fps calculation over
    
    #initialize camera and set main window for interaction between thread and MainWindow
    def __init__(self, MainWindow, W, H):
        QThread.__init__(self)
        #set the camera resolution
        self.W, self.H = W, H
        self.MainWindow = MainWindow
        index = self.MainWindow.currentIndex
        self.init_camera(index=index,firstInit=True)

        self.autoExpCounter = 0
    
    #fps tracking function
    def fps(self):
        if self.fps_counter == 0:
            self.fps_time1 = datetime.datetime.now()
            self.fps_counter += 1
        elif self.fps_counter == self.fps_averaging:
            self.fps_time2 = datetime.datetime.now()
            time_diff = self.fps_time2 - self.fps_time1
            average_fps = self.fps_averaging/time_diff.total_seconds()
            self.MainWindow.label_fps.setText('fps: {:.1f}'.format(average_fps))
            self.fps_counter = 0
        else:
            self.fps_counter += 1
            
    #capture live images and convert to beam profile
    def run(self):
        while(1):
            if self.camera != None:
                try:
                    self.autoExpCounter = 0
                    if self.LOGGING:
                        for index in range(len(enumerate_cameras(cv2.CAP_MSMF))):
                            #print(index)
                            self.centroid_x_save, self.centroid_y_save, self.d4s_major_save = self.centroid_x_save_init, self.centroid_y_save_init, self.d4s_major_save_init
                            self.MainWindow.currentIndex = index
                            self.MainWindow.autoExp.setChecked(True)
                            self.MainWindow.tracking.setChecked(True)
                            self.autoExpCounter = 0
                            time.sleep(0.5)
                            while self.MainWindow.AUTO_EXP:
                                self.fps()
                                self.live_image()
                                self.beam()
                            time.sleep(0.5)
                    else:
                        self.fps()
                        self.live_image()
                        self.beam()
                        self.MainWindow.label_exp_ms.setText("Exposure (ms): {}".format(self.exposure_dict[self.camera.exposure]))
                except Exception:
                    #self.MainWindow.RUNNING = False
                    #still = np.zeros([int(self.H/self.scale),int(self.W/self.scale),3])
                    #imGUI = QtGui.QImage(still.data, still.shape[1], still.shape[0], \
                    #still.shape[1]*3, QtGui.QImage.Format_RGB888)
                    #self.MainWindow.beam_frame.setPixmap(QtGui.QPixmap.fromImage(imGUI))
                    #self.MainWindow.image_frame.setPixmap(QtGui.QPixmap.fromImage(imGUI))
                    traceback.print_exc()
                    #return
            else:
                self.MainWindow.RUNNING = False
                return
    
    #initialize camera settings
    #instructions are provided to assign path and camera designators for unique device labeling and preventing normal webcam access
    def init_camera(self,index=0,firstInit=False):
        if not firstInit:
            self.camera.release()
            
        cap = Camera(int(self.MainWindow.lineEdit_setExp.text()),index)
        cap.open()
        #cap.set_exposure(int(self.MainWindow.lineEdit_setExp.text()))
        
        if not cap.isOpened():
            self.MainWindow.lineEdit.setText('Camera #{} failed to open'.format(index))
            return
        
        if not firstInit:
            cap.set_exposure(self.camera.exposure)
            #self.MainWindow.lineEdit_setExp.setText("-7")
            
        self.camera = cap
        self.MainWindow.lineEdit_setExp.setText(str(self.camera.exposure))
        self.currentCamera = index
        for camera_info in enumerate_cameras(cv2.CAP_MSMF):
            if index==camera_info.index:
                path = camera_info.path
                #uncomment the following print line and run the program
                ##Choose cameras from the drop down to print out and read the path
                #print(path)
                
        if firstInit:
            self.MainWindow.lineEdit_setExp.setText(str(self.camera.exposure))
            
        #insert corresponding path identifier below that is printed e.g. 8&150091a5 for your camera and PC
        ##this corresponds to a physical camera which can be used as the designator, e.g. 'Near Field 1064 nm camera 1'
        if '8&150091a5' in path:
            camera_designator = 'Camera identifier 1'
        elif '8&27ba424a' in path:
            camera_designator = 'Camera identifier 2'
        elif '8&3a73f2ef' in path:
            camera_designator = 'Camera identifier 3'
        elif '9&c029877' in path:
            camera_designator = 'Camera identifier 4'
        elif '9&894e05f' in path:
            camera_designator = 'Camera identifier 5'
        elif '9&3175f9c1' in path:
            camera_designator = 'Camera identifier 6'
        elif 'find this out' in path:
            camera_designator = 'Camera identifier 7'
        #once camera paths and designators are assigned, comment out the following else statement to prevent software from accessing
        ##undesired webcam
        else: camera_designator = 'Unidentified Camera'
        print(camera_designator)
        self.camera_designator = camera_designator
        self.path = path
        self.MainWindow.lineEdit.setText('Camera index #{} - {} - initialized! Acquistion is live'.format(index, camera_designator))

    #capture an image from the camera and store to self.image_live
    def img_capture(self):
        self.image_live = self.camera.read()
    
    #take camera capture and display live on "Camera" tab
    def live_image(self):
        #time printouts can be used for runtime optimization which directly translates to framerate of images
        #A = datetime.datetime.now()
        
        if self.camera == None:
            return
            
        if not (self.MainWindow.currentIndex == self.currentCamera):
            self.init_camera(index=self.MainWindow.currentIndex)
            if self.camera == None:
                return
                
        #take a raw capture
        self.img_capture()
        #downsample the image by scale factor to fit on the GUI screen
        scale = 2
        imR = cv2.resize(self.image_live, (int(self.W/scale),int(self.H/scale)))
        #imR = self.image_live
        #set the image to the proper position on the window if not already done
        if not self.FRAMES_INIT:
            self.MainWindow.image_frame.move(120,-150)#0,0)#125,60)
            self.MainWindow.image_frame.resize(int(self.W),int(self.H))
        imGUI = QtGui.QImage(imR.data, imR.shape[1], imR.shape[0], imR.shape[1]*3, QtGui.QImage.Format_RGB888)
        self.MainWindow.image_frame.setPixmap(QtGui.QPixmap.fromImage(imGUI))
        #B = datetime.datetime.now()
        #print("Live image runtime: "+str(B-A))

    #set the camera exposure
    def exp(self):
        exposure = int(self.MainWindow.lineEdit_setExp.text())
        self.camera.set_exposure(exposure)
        self.MainWindow.lineEdit.setText("Exposure Set!")
        
    
    #convert camera image to beam profile (rainbow map) and display on GUI
    #centroid and ROI
    #compute metrics of beam (centroid, D4σ)
    def beam(self):
        #time printouts can be used for runtime optimization which directly translates to framerate of images
        #A = datetime.datetime.now()
        #take grayscale version of the image for intensity profiling
            
        image = cv2.cvtColor(self.image_live, cv2.COLOR_RGB2GRAY)
        self.pix_max = np.max(image)
        if self.MainWindow.AUTO_EXP:
            if self.count == 1:
                self.autoExpCounter += 1
                if self.autoExpCounter >= 15:
                    if self.LOGGING:
                        self.MainWindow.autoExp.setChecked(False)
                    self.MainWindow.lineEdit.setText("Max autoexposure tries reached")
                elif np.max(image) < 0.7*255:
                    exposure_val = int(self.camera.exposure+1)
                    if not (self.camera.exposure==-1):
                        self.camera.set_exposure(exposure_val)
                        self.MainWindow.lineEdit_setExp.setText(str(exposure_val))
                    else:
                        self.MainWindow.lineEdit.setText("Already at max exposure")
                        if self.LOGGING:
                            self.MainWindow.autoExp.setChecked(False)
                elif np.max(image) > 0.9*255:
                    exposure_val = int(self.camera.exposure-1)
                    if not (self.camera.exposure==-13):
                        self.camera.set_exposure(exposure_val)
                        self.MainWindow.lineEdit_setExp.setText(str(exposure_val))
                    else:
                        self.MainWindow.lineEdit.setText("Already at min exposure")
                        if self.LOGGING:
                            self.MainWindow.autoExp.setChecked(False)
                else:
                    self.MainWindow.lineEdit.setText("Auto exposure complete")
                    if self.LOGGING:
                        self.MainWindow.autoExp.setChecked(False)
                self.count += 1
            else:
                if self.count == 10:
                    self.count = 1
                else:
                    self.count += 1
                    
            
        #set the aperture mask values to those input by the user in the text boxes
        #if the text boxes are left blank for some time, they will default
        if not self.MainWindow.ROI_Tracking:
            try:        
                self.mask_x = int(float(self.MainWindow.lineEdit_apx.text())/self.pixel_um)
                self.count_x = 0
            except:
                if self.count_x == 10:
                    self.mask_x = int(self.W / 2)
                    self.MainWindow.lineEdit_apx.setText(str(self.pixel_um*self.mask_x))
                self.count_x += 1
            try:
                self.mask_y = int(float(self.MainWindow.lineEdit_apy.text())/self.pixel_um)
                self.count_y = 0
            except:
                if self.count_y == 10:
                    self.mask_y = int(self.H / 2)
                    self.MainWindow.lineEdit_apy.setText(str(self.pixel_um*self.mask_y))
                self.count_y += 1
            try:
                self.mask_r = int(float(self.MainWindow.lineEdit_apr.text())/self.pixel_um)
                self.count_r = 0
            except:
                if self.count_r == 10:
                    self.mask_r = int(self.H/2 - 100)
                    self.MainWindow.lineEdit_apr.setText(str(self.pixel_um*self.mask_r))
                self.count_r += 1
        else:
            try:        
                self.mask_x = self.centroid_x_save
                self.MainWindow.lineEdit_apx.setText(str(int(self.pixel_um*self.centroid_x_save)))
                self.count_x = 0
            except:
                if self.count_x == 10:
                    self.mask_x = int(self.W / 2)
                    self.MainWindow.lineEdit_apx.setText(str(self.pixel_um*self.mask_x))
                self.count_x += 1
            try:
                self.mask_y = self.centroid_y_save
                self.MainWindow.lineEdit_apy.setText(str(int(self.pixel_um*self.centroid_y_save)))
                self.count_y = 0
            except:
                if self.count_y == 10:
                    self.mask_y = int(self.H / 2)
                    self.MainWindow.lineEdit_apy.setText(str(self.pixel_um*self.mask_y))
                self.count_y += 1
            try:
                if np.sum(image) >= self.LOGGING_CNT_THRESHOLD:
                    self.mask_r = 1.5*self.d4s_major_save/2
                    self.MainWindow.lineEdit_apr.setText(str(int(1.5*self.pixel_um*self.d4s_major_save/2)))
                else:
                    self.mask_r = int(self.H/2 - 100)
                self.count_r = 0
            except:
                if self.count_r == 10:
                    self.mask_r = int(self.H/2 - 100)
                    self.MainWindow.lineEdit_apr.setText(str(self.pixel_um*self.mask_r))
                self.count_r += 1
                
        if self.mask_r < 10:
            self.mask_r = 10
            
        #define a mask depending on aperture
        mask = np.zeros([self.H,self.W])
        mask = cv2.circle(mask, (int(self.mask_x),int(self.mask_y)), int(self.mask_r), 255, -1)

        #copy and mask the image based on the circular aperture mask
        image_m = np.copy(image)
        image_m[mask==0] = 0
        
        #get the sum and peak values of the image
        self.pix_sum = np.sum(image_m)
        self.pix_max = np.max(image_m)
        self.MainWindow.lcdNumber_P.display(round(self.pix_sum/1E4))
        
        #count the number of saturated pixels
        self.sat_num = len(np.where(image_m==255)[0])
        self.MainWindow.label_sat.setText("# Saturated Pixels: "+str(self.sat_num))
        
        #compute the centroid and D4σ in pixel values if image is not empty
        MOM = cv2.moments(image_m)
        if MOM['m00'] != 0:
            centroid_x = MOM['m10']/MOM['m00']
            centroid_y = MOM['m01']/MOM['m00']
            self.centroid_x_save = centroid_x
            self.centroid_y_save = centroid_y
            #note 1 pixel has physical dimension: pixel_um * pixel_um (= 1.55 um (micron) * 1.55 um for Raspi HQ Camera module)
            #With no scaling (lens) the physical beam widths are then d4x (px) * 1.55 um, d4y (px) * 1.55 um
            d4x_px = 4*math.sqrt(abs(MOM['m20']/MOM['m00'] - centroid_x**2))
            d4y_px = 4*math.sqrt(abs(MOM['m02']/MOM['m00'] - centroid_y**2))
            self.d4s_major_save = np.max(np.array([d4x_px, d4y_px]))
            d4x = self.pixel_um * d4x_px
            d4y = self.pixel_um * d4y_px
        else:
            centroid_x = self.mask_x
            centroid_y = self.mask_y
            self.d4s_major_save = self.mask_r
            d4x_px, d4y_px, d4x, d4y = 0,0,0,0
        self.MainWindow.label_centroid.setText("Centroid x,y (μm): "+'{0:.1f}'.format(self.pixel_um*centroid_x)+", "+'{0:.1f}'.format(self.pixel_um*centroid_y))
        self.MainWindow.lcdNumber_dx.display(round(d4x))
        self.MainWindow.lcdNumber_dy.display(round(d4y))
        
        #take the negative of the image in grayscale space to apply cv2 rainbow map
        image_n = 255 - image
        beam = cv2.applyColorMap(image_n, cv2.COLORMAP_RAINBOW)
        
        if (self.LOGGING and (not self.MainWindow.AUTO_EXP)):
            savepath = os.path.join(os.getcwd(), "saves")
            day = datetime.datetime.now().strftime('%Y%m%d')
            if not os.path.exists(savepath):
                os.mkdir(savepath)
            day = datetime.datetime.now().strftime('%Y%m%d')
            filename = "all_cameras_"+day+".csv"
            if not os.path.exists(os.path.join(savepath,filename)):
                logfile = open(os.path.join(savepath,filename), 'w', encoding="utf-8")
                logfile.write("<time>,<camera ID>,<pixel pitch (um)>,<image width>,<image height>,<centroid x>,<centroid y>,<d4sigma x>,<d4sigma y>,<aperture x>,<aperture y>,<aperture r>,<exposure ms>,<peak count>,<integrated count>\n")
            else:
                logfile = open(os.path.join(savepath,filename), 'a', encoding="utf-8")
            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            if self.pix_sum >= self.LOGGING_CNT_THRESHOLD:
                logfile.write('{},'.format(timestamp))
                logfile.write('{},'.format(self.camera_designator))
                logfile.write('{},'.format(self.pixel_um))
                logfile.write('{},{},'.format(self.W,self.H))
                logfile.write('{0:.2f},{1:.2f},'.format(centroid_x,centroid_y))
                logfile.write('{0:.2f},{1:.2f},'.format(d4x_px,d4y_px))
                logfile.write('{0:.1f},{1:.1f},{2:.1f},'.format(self.mask_x,self.mask_y,self.mask_r))
                logfile.write('{},'.format(self.exposure_dict[int(self.camera.exposure)]))
                logfile.write('{},{}\n'.format(self.pix_max,self.pix_sum))
                logfile.close()
                
            
        #save all data if SAVE_NOW is flagged by save button, then reset the flag
        if self.SAVE_NOW:
            savepath = os.path.join(os.getcwd(), "saves")
            day = datetime.datetime.now().strftime('%Y%m%d')
            savepath = os.path.join(savepath,day)
            if not os.path.exists(savepath):
                os.mkdir(savepath)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            camerastamp = self.camera_designator
            filename1 = "camera_"+timestamp+"_"+camerastamp+".png"
            filename2 = "beam_"+timestamp+"_"+camerastamp+".png"
            filename3 = "measurements_"+timestamp+"_"+camerastamp+".csv"
            filename4 = "x_profile_"+timestamp+"_"+camerastamp+".png"
            filename5 = "y_profile_"+timestamp+"_"+camerastamp+".png"
            cv2.imwrite(os.path.join(savepath,filename1), self.image_live) #may need to cvt color
            cv2.imwrite(os.path.join(savepath,filename2), beam)
            statsfile = open(os.path.join(savepath,filename3), 'w', encoding="utf-8")
            statsfile.write("Pixel pitch (um)\n")
            statsfile.write('{}\n'.format(self.pixel_um))
            statsfile.write("Image width (px), height (px)\n")
            statsfile.write('{},{}\n'.format(self.W,self.H))
            statsfile.write("Centroid x (px), y (px)\n")
            statsfile.write('{0:.2f},{1:.2f}\n'.format(centroid_x,centroid_y))
            statsfile.write("D4σ x (px), y (px)\n")
            statsfile.write('{0:.2f},{1:.2f}\n'.format(d4x_px,d4y_px))
            statsfile.write("Aperture x (px), y (px), radius (px)\n")
            statsfile.write('{0:.1f},{1:.1f},{2:.1f}\n'.format(self.mask_x,self.mask_y,self.mask_r))
            statsfile.write("Exposure Setting\n")
            statsfile.write('{}\n'.format(self.camera.exposure))
            statsfile.write("Exposure value (ms)\n")
            statsfile.write('{}\n'.format(self.exposure_dict[int(self.camera.exposure)]))
            statsfile.write("Gray value max (ct), sum (ct), saturated pixels (ct)\n")
            statsfile.write('{},{},{}\n'.format(self.pix_max,self.pix_sum,self.sat_num))
            statsfile.write("Identification info\n")
            statsfile.write('{},{}\n'.format(self.camera_designator, self.path))
            statsfile.close()
            x_prof = image[round(centroid_y),:]
            plt.plot(range(len(x_prof)),x_prof)
            plt.title('Beam profile along x-axis at y-centroid')
            plt.xlim(0,len(x_prof)-1)
            plt.ylim(0,255)
            plt.xlabel('Pixel')
            plt.ylabel('Intensity')
            plt.savefig(os.path.join(savepath,filename4))
            plt.close('all')
            y_prof = image[:,round(centroid_x)]
            plt.plot(range(len(y_prof)),y_prof)
            plt.title('Beam profile along y-axis at x-centroid')
            plt.xlim(0,len(y_prof)-1)
            plt.ylim(0,255)
            plt.xlabel('Pixel')
            plt.ylabel('Intensity')
            plt.savefig(os.path.join(savepath,filename5))
            plt.close('all')
            #only stop the saving if LOGGING is not enabled
            #update info bar depending on whether logging or single save
            self.MainWindow.lineEdit.setText("Data saved to: "+savepath)
            self.SAVE_NOW = False
            
        #convert to int by rounding
        d4x, d4y, centroid_x, centroid_y = round(d4x), round(d4y), round(centroid_x), round(centroid_y)
        
        #add dashed lines for reference crosshair if enabled
        if self.MainWindow.REFERENCE_CROSSHAIR:
            refX = float(self.MainWindow.lineEdit_refX.text())/self.pixel_um
            refY = float(self.MainWindow.lineEdit_refY.text())/self.pixel_um
            refXpix = int(refX)
            refYpix = int(refY)
            deltaX = refX - self.W/2
            deltaY = refY - self.H/2
            numdashesV = 24#12
            addDashesV = self.addDashes(deltaY,numdashesV,direction='V')
            for i in range(0-addDashesV-1,numdashesV-addDashesV+1):
                cv2.line(beam, (refXpix,i*int(self.H/numdashesV)+int(self.H/(4*numdashesV))+int(deltaY)), \
                    (refXpix,(2*i+1)*int(self.H/(2*numdashesV))+int(self.H/(4*numdashesV))+int(deltaY)), (0,0,0), thickness=2)
            numdashesH = 32#16
            addDashesH = self.addDashes(deltaX,numdashesH,direction='H')
            for i in range(0-addDashesH-1,numdashesH-addDashesH+1):
                cv2.line(beam, (i*int(self.W/numdashesH)+int(self.W/(4*numdashesH))+int(deltaX),refYpix), \
                    ((2*i+1)*int(self.W/(2*numdashesH))+int(self.W/(4*numdashesH))+int(deltaX),refYpix), (0,0,0), thickness=2)
            cv2.circle(beam, (refXpix,refYpix), radius=3, color=(0, 0, 0), thickness=-1)
        #apply centroid line tracking
        cv2.line(beam, (centroid_x,0), (centroid_x,self.H), (0,0,0), thickness=3)
        cv2.line(beam, (0,centroid_y), (self.W,centroid_y), (0,0,0), thickness=3)
        #downsample the image by scale factor 4 to fit on the GUI screen
        scale = 2#4
        beam_R = cv2.resize(beam, (int(self.W/scale),int(self.H/scale)))
        beam_R = cv2.cvtColor(beam_R, cv2.COLOR_BGR2RGB)
        #line below is to add aperture mask circle
        #image is reduced by scale times, so center coordinate is mask_x/scale, mask_y/scale; radius is mask_r/scale
        beam_R = cv2.circle(beam_R, (round(self.mask_x/scale),round(self.mask_y/scale)),\
            int(self.mask_r/scale), (0,0,0), 2)
        #set the image to the proper position on the window if not already done
        if not self.FRAMES_INIT:
            self.MainWindow.beam_frame.move(125,60)
            self.MainWindow.beam_frame.resize(int(self.W/scale),int(self.H/scale))
            self.FRAMES_INIT = True
        imGUI = QtGui.QImage(beam_R.data, beam_R.shape[1], beam_R.shape[0], \
        beam_R.shape[1]*3, QtGui.QImage.Format_RGB888)
        self.MainWindow.beam_frame.setPixmap(QtGui.QPixmap.fromImage(imGUI))
        #B = datetime.datetime.now()
        #print("Beam runtime: "+str(B-A))
        
    #helper function to add dashes for drawing reference crosshair
    def addDashes(self,delta,numdashes,direction):
        if direction=='V':
            addDashes = delta/(self.H/numdashes)
        elif direction=='H':
            addDashes = delta/(self.W/numdashes)
        if addDashes > 0:
            addDashes = int(np.ceil(addDashes))
        elif addDashes < 0:
            addDashes = int(np.floor(addDashes))
        else:
            addDashes = int(0)
        return addDashes
                
#run the GUI      
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())