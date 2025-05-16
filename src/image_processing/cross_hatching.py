import math
import time
import ctypes
import random
import numpy as np

from PIL import Image, ImageFilter, ImageDraw
from PyQt5.QtCore import pyqtSignal
from numpy.core.shape_base import atleast_3d

class CrossHatchParams(ctypes.Structure):
    _fields_ = [
        ("image", ctypes.POINTER(ctypes.c_uint8)),
        ("segment_count_ptr", ctypes.POINTER(ctypes.c_int)),
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
        ("layers", ctypes.c_int),
        ("layer", ctypes.c_int),
        ("spacing", ctypes.c_int),
        ("starting_angle", ctypes.c_float),
        ("delta_angle", ctypes.c_float),
    ]

class CrossHatching:
    def __init__(self, image: Image, update_signal, output_file: str, layers: int, spacing: float):
        self.image = image.convert("L")
        self.update_signal = update_signal
        self.layers = layers
        self.spacing = spacing
        self.output_file = output_file

        self.color_scaler = 255/(self.layers+1)
        self.starting_angle = random.randint(0, 360)
        self.angle_delta = 360/(self.layers+1)

        self.output_image = Image.new("RGB", (self.image.width, self.image.height), color="white")
        self.image_draw = ImageDraw.Draw(self.output_image)

        self.lib = ctypes.CDLL("dlls/image_processing.dll")

        # crossHatch
        self.lib.crossHatch.argtypes = [ctypes.POINTER(CrossHatchParams)]
        self.lib.crossHatch.restype = ctypes.POINTER(ctypes.c_int)

        # writeSegmentsToFile
        self.lib.writeSegmentsToFile.argtypes = [ctypes.POINTER(ctypes.c_int),
                                                ctypes.c_int, ctypes.c_int,
                                                ctypes.c_char_p]

        # freeMem
        self.lib.freeMem.argtypes = [ctypes.POINTER(ctypes.c_int)]

    def c_crossHatch(self):
        img_arr = np.array(self.image, dtype=np.uint8).flatten()
        img_ptr = img_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        segment_count = ctypes.c_int(0)
        output_file = self.output_file.encode("utf-8")

        params = CrossHatchParams(
            image=img_ptr,
            segment_count_ptr=ctypes.pointer(segment_count),
            width=self.image.width,
            height=self.image.height,
            layers=self.layers,
            layer=0,
            spacing=self.spacing,
            starting_angle=ctypes.c_float(self.starting_angle),
            delta_angle=ctypes.c_float(self.angle_delta)
        )

        for layer in reversed(range(self.layers)):
            params.layer = layer
            self.update_signal.emit(f"Hatching {int((self.layers-layer)/self.layers*100)}%")
            segments_ptr = self.lib.crossHatch(ctypes.byref(params))

            self.lib.writeSegmentsToFile(segments_ptr, segment_count.value, 4, output_file)

            for i in range(segment_count.value):
                base = i * 4
                x1 = segments_ptr[base + 0]
                y1 = segments_ptr[base + 1]
                x2 = segments_ptr[base + 2]
                y2 = segments_ptr[base + 3]

                self.image_draw.line(((x1, y1), (x2, y2)), (0,0,0))
            self.lib.freeMem(segments_ptr)
        return self.output_image
