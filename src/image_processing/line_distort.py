import math
import ctypes
import numpy as np

from PyQt5.QtCore import pyqtSignal
from PIL import Image, ImageOps, ImageDraw

TWO_PI = 2 * np.pi
HALF_PI = 0.5 * np.pi
IMAGE_SCALE_UP = 3

class LineDistortParams(ctypes.Structure):
    _fields_ = [
        ("image", ctypes.POINTER(ctypes.c_uint8)),
        ("segments_count_ptr", ctypes.POINTER(ctypes.c_int)),
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
        ("rows", ctypes.c_int),
        ("max_y_ptr", ctypes.POINTER(ctypes.c_int))
    ]

class SegmentArray(ctypes.Structure):
    _fields_ = [
        ("segment_arr", ctypes.POINTER(ctypes.c_double)),
        ("segment_count", ctypes.c_int),
        ("segments_allocated", ctypes.c_int),
    ]

class LineDistort:
    def __init__(self, update_signal: pyqtSignal, output_file: str, rows=1):
        self.map_array = np.array([0,0,0,2,5,5,5,7,1,0,
                                   0,1,2,3,4,5,5,4,3,2,
                                   10,2,2,4,7,5,6,4,1,1], dtype=np.uint8).flatten()
        self.lib = ctypes.CDLL("dlls/image_processing.dll")

        # line_distort
        self.lib.line_distort.argtypes = [ctypes.POINTER(LineDistortParams)]
        self.lib.line_distort.restype = ctypes.POINTER(SegmentArray)

        # free_segmnets_array
        self.lib.free_segments_array.argtypes = [ctypes.POINTER(SegmentArray),
                                             ctypes.c_int]

    def c_lineDistort(self):
        img_ptr = self.map_array.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        segments_array_count = ctypes.c_int(0)
        max_y = ctypes.c_int(0)

        params = LineDistortParams(
            image=img_ptr,
            segments_array_count_ptr=ctypes.pointer(segments_array_count),
            width=10,
            height=3,
            rows=1,
            max_y_ptr=ctypes.pointer(max_y),
        )
        segment_arrays_ptr = self.lib.line_distort(ctypes.byref(params))
        output_image = Image.new("RGB", (10, max_y.value), color="white")
        draw = ImageDraw.Draw(output_image)

        l_x, l_y = None, None
        for i in range(0, segments_array_count.value, 2):
            x_segment = segment_arrays_ptr[i+0]
            y_segment = segment_arrays_ptr[i+1]
            for j in range(x_segment.segment_count):
                x = x_segment.segment_arr[j]
                y = y_segment.segment_arr[j]
                if not l_x is None and not l_y is None:
                    draw.line(((round(l_x), round(l_y)),
                                    (round(x), round(y))),
                                   (0,0,0), width=1)
                l_x = x
                l_y = y
        self.lib.free_segments_array(segment_arrays_ptr, segments_array_count.value)
        """ TODO: write coords to file """
        return output_image
