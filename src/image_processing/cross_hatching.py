import math
import time
import ctypes
import random
import numpy as np

from PIL import Image, ImageFilter, ImageDraw
from PyQt5.QtCore import pyqtSignal
from numpy.core.shape_base import atleast_3d

class CrossHatching:
    def __init__(self, image: Image, update_signal, layers: int, spacing: float):
        self.image = image.convert("L")
        self.update_signal = update_signal
        self.layers = layers
        self.spacing = spacing

        self.color_scaler = 255/(self.layers+1)
        self.starting_angle = random.randint(0, 360)
        self.angle_delta = 360/(self.layers+1)

        self.output_image = Image.new("RGB", (self.image.width, self.image.height), color="white")
        self.image_draw = ImageDraw.Draw(self.output_image)

        self.lib = ctypes.CDLL("dlls/image_processing.dll")
        self.lib.crossHatch.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_int),
                                           ctypes.c_int, ctypes.c_int,
                                           ctypes.c_int, ctypes.c_int,
                                           ctypes.c_int,
                                           ctypes.c_float, ctypes.c_float]
        self.lib.crossHatch.restype = ctypes.POINTER(ctypes.c_int)
        self.lib.freeMem.argtypes = [ctypes.POINTER(ctypes.c_int)]

    def c_crossHatch(self):
        img_arr = np.array(self.image, dtype=np.uint8)
        img_arr = img_arr.flatten()
        img_ptr = img_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        segment_count = ctypes.c_int(0)

        for layer in range(self.layers):
            self.update_signal.emit(f"Hatching {int((layer+1)/self.layers*100)}%")
            segments_ptr = self.lib.crossHatch(img_ptr, ctypes.byref(segment_count),
                                               self.image.width, self.image.height,
                                               self.layers, layer,
                                               self.spacing,
                                               self.starting_angle, self.angle_delta)

            for i in range(segment_count.value):
                base = i * 4
                x1 = segments_ptr[base + 0]
                y1 = segments_ptr[base + 1]
                x2 = segments_ptr[base + 2]
                y2 = segments_ptr[base + 3]
                self.image_draw.line(((x1, y1), (x2, y2)), (0,0,0))
            self.lib.freeMem(segments_ptr)
        return self.output_image
