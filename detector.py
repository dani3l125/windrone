import numpy as np
import tflite_runtime.interpreter as tflite
import tensorflow as tf
import cv2 as cv

IMG_SIZE = (640, 480)
CONF = 0.3


class Model:
    def __init__(self,
                 model_file='detector.tflite',
                 ext_delegate=None,
                 num_threads=3):
        self.interpreter = tflite.Interpreter(
            model_path=model_file,
            experimental_delegates=ext_delegate,
            num_threads=num_threads)
        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # check the type of the input tensor
        self.floating_model = self.input_details[0]['dtype'] == np.float32

        # NxHxWxC, H:1, W:2
        self.height = self.input_details[0]['shape'][1]
        self.width = self.input_details[0]['shape'][2]

    def detect(self, img):
        '''
        receives an image in OpenCV format and returns array containing normalized x,y coordinates of the center
         and normalized width and height values for the most likely window.
        '''
        img = cv.resize(img, IMG_SIZE) #resize H,W
        tmp = img[:, :, 0]
        img[:, :, 0] = img[:, :, 2]
        img[:, :, 2] = tmp # BGR to RGB
        input_data = np.expand_dims(img, axis=0)
        if self.floating_model:
            input_data = (np.float32(input_data)/255 - 0.45) / 0.225
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        x = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        xywhs = x[:,tf.where(np.logical_and(x[4]>=0.2, np.logical_and((x[2]>0.15 * IMG_SIZE[1]), x[3]>(0.15 * IMG_SIZE[0]))))]
        if xywhs.shape[1] == 0:
            return None
        middle_window_index = tf.argmin(tf.abs(xywhs[0,:,:] - IMG_SIZE[1] / 2) + tf.abs(xywhs[1,:,:] - IMG_SIZE[0] / 2))

        return xywhs[:4,middle_window_index[0],0] / np.array((IMG_SIZE[1], IMG_SIZE[0], IMG_SIZE[1], IMG_SIZE[0])) # in [0,1]
