import time
import cv2
import numpy as np

class Camera:

    def __init__(self, exposure=-7,index=0,selector=cv2.CAP_MSMF,W=1280,H=960,I=0,RST=10, pp=5.6) -> None:
        self.index = index
        self.selector = selector
        self.cap = None
        self.width = W
        self.height = H
        self.fps = None
        self.pp = pp
        self.exposure = exposure

    def open(self):
        self.cap = cv2.VideoCapture(self.index, self.selector)
        self.cap.set(cv2.CAP_PROP_CONVERT_RGB, 1)
        self.cap.set(cv2.CAP_PROP_AUTO_WB, 0)

        if self.width and self.height:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        if self.fps:
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
        self.set_exposure(self.exposure)
    
    def set_width(self, width):
        self.width = width
    
    def set_height(self, height):
        self.height = height
    
    def set_fps(self, fps):
        self.fps = fps

    def set_focus(self, val):
        self.cap.set(cv2.CAP_PROP_FOCUS, val)
        
    def set_exposure(self, val):
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
        self.cap.set(cv2.CAP_PROP_EXPOSURE, val)
        self.exposure = val

    def read(self, restart_times=10):
        ret, frame = self.cap.read()

        if not ret:
            if restart_times != 0:
                print("Unable to read video frame")
                success = False
                for i in range(1, restart_times + 1):
                    print(f"reopen {i} times")
                    try:
                        cap.reStart()
                        success = True
                        break
                    except:
                        continue
                if not success:
                    print("reopen failed")

        #frame = np.mean(frame, axis=2)
        #frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        #print(np.max(frame))
        #print(np.shape(frame))
        
        return frame

    def reStart(self):
        self.release()
        time.sleep(0.5)
        self.open()

    def release(self):
        self.cap.release()

    def isOpened(self):
        return self.cap.isOpened()

        