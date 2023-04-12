from djitellopy import Tello
import cv2, math, time
import threading

class Drone:
    def __init__(self,
                 fly=True):
        self.tello = Tello()
        self.tello.connect()
        self.tello.streamon()
        self.frame_read = self.tello.get_frame_read()
        self._frame = None
        self.is_writing = False
        self.want_to_read = False
        self.is_sending_command = False
        self.start_detection = False
        def update_frame():
            while True:
                if not self.want_to_read:
                    self.is_writing = True
                    self._frame = self.frame_read.frame
                    self.is_writing = False
                else:
                    time.sleep(0.05)

        self.camera_thread = threading.Thread(target=update_frame, args=())
        self.camera_thread.start()
        self.fly=fly
        if fly:
            self.tello.takeoff()

    @property
    def frame(self):
        self.want_to_read = True
        while self.is_writing:
            time.sleep(0.05)
        frame = self._frame
        self.want_to_read = False
        return frame

    def fly_to_start(self, outdoor):
        if not self.fly:
            print('Not flying, can\'t move!!!')
            return
        if outdoor:
            self.tello.move_up(100)
            self.tello.move_back(500)
        if not outdoor:
            self.tello.move_up(100)

    def fly_to_finish(self, outdoor, closed):
        if not self.fly:
            print('Not flying, can\'t move!!!')
            return
        if outdoor:
            self.tello.move_down(30)
            time.sleep(2)
            self.tello.move_forward(300)
        else:
            self.tello.move_back(300)
        self.tello.end()



