import math
import ctypes
import numpy as np

from PyQt5.QtCore import pyqtSignal
from PIL import Image, ImageOps, ImageDraw

TWO_PI = 2 * np.pi
HALF_PI = 0.5 * np.pi
IMAGE_SCALE_UP = 3

class WaveParams(ctypes.Structure):
    _fields_ = [
        ("image", ctypes.POINTER(ctypes.c_uint8)),
        ("segments_array_count_ptr", ctypes.POINTER(ctypes.c_int)),
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
        ("ystep", ctypes.c_int),
        ("xstep", ctypes.c_double),
        ("xsmooth", ctypes.c_double),
        ("stroke_width", ctypes.c_double),
        ("horizontal", ctypes.c_bool),
    ]

class SegmentArray(ctypes.Structure):
    _fields_ = [
        ("segment_arr", ctypes.POINTER(ctypes.c_double)),
        ("segment_count", ctypes.c_int),
        ("segments_allocated", ctypes.c_int),
    ]

class Wave:
    def __init__(self, image: Image,
                 update_signal: pyqtSignal,
                 output_file: str,
                 ystep=100,
                 xstep=3,
                 xsmooth=128,
                 stroke_width=1,
                 horizontal=True):
        # xsmooth = 150 # Bigger => less freq
        self.image = ImageOps.invert(image.convert("L"))
        self.image = self.image.resize((self.image.width*IMAGE_SCALE_UP, self.image.height*IMAGE_SCALE_UP))

        self.output_image = Image.new("RGB", (self.image.width, self.image.height), color="white")
        self.draw = ImageDraw.Draw(self.output_image)

        self.update_signal = update_signal
        self.output_file = output_file
        self.ystep = ystep
        self.xstep = xstep
        self.xsmooth = xsmooth
        self.stroke_width = stroke_width
        self.horizontal = horizontal

        self.lib = ctypes.CDLL("dlls/image_processing.dll")

        # wave
        self.lib.wave.argtypes = [ctypes.POINTER(WaveParams)]
        self.lib.wave.restype = ctypes.POINTER(SegmentArray)

        # write_segments_to_file
        self.lib.write_segments_to_file.argtypes = [ctypes.POINTER(SegmentArray),
                                                 ctypes.c_int,
                                                 ctypes.c_char_p]

        # free_segments_array
        self.lib.free_segments_array.argtypes = [ctypes.POINTER(SegmentArray),
                                                 ctypes.c_int]

    def c_wave(self):
        # xsmooth = 150 # Bigger => less freq
        img_arr = np.array(self.image, dtype=np.uint8).flatten()
        img_ptr = img_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        segments_array_count = ctypes.c_int(0)

        params = WaveParams(
            image=img_ptr,
            segments_array_count_ptr=ctypes.pointer(segments_array_count),
            width=self.image.width,
            height=self.image.height,
            ystep=self.ystep,
            xstep=ctypes.c_double(self.xstep),
            xsmooth=ctypes.c_double(self.xsmooth),
            stroke_width=ctypes.c_double(self.stroke_width),
            horizontal=self.horizontal
        )

        segment_arrays_ptr = self.lib.wave(ctypes.byref(params))
        self.lib.write_segments_to_file(segment_arrays_ptr, segments_array_count.value, self.output_file.encode("utf-8"))

        l_x, l_y = None, None
        for i in range(0, segments_array_count.value, 2):
            x_segment = segment_arrays_ptr[i+0]
            y_segment = segment_arrays_ptr[i+1]
            for j in range(x_segment.segment_count):
                x = x_segment.segment_arr[j]
                y = y_segment.segment_arr[j]
                if not l_x is None and not l_y is None:
                    self.draw.line(((round(l_x), round(l_y)),
                                    (round(x), round(y))),
                                   (0,0,0), width=int(self.stroke_width*IMAGE_SCALE_UP))
                l_x = x
                l_y = y
        self.lib.free_segments_array(segment_arrays_ptr, segments_array_count.value)
        return self.output_image

    def wave(self):
        min_phase_incr = 10 * TWO_PI / (self.image.width / self.xstep)
        max_phase_incr =  TWO_PI * self.xstep / self.stroke_width

        scaled_y_step = self.image.height / self.ystep
        ymult = IMAGE_SCALE_UP * 2

        odd_row = False
        final_row = False
        reverse_row = False

        f = open(self.output_file, "w")
        l_x, l_y = None, None
        max_len = 0
        for y_ in np.arange(0, self.image.height, scaled_y_step):
            x_start_points = []
            y_start_points = []
            x_points = []
            y_points = []
            x_end_points = []
            y_end_points = []

            y = y_.item()
            odd_row = not odd_row

            if (y + scaled_y_step) >= self.image.height:
                final_row = True
            reverse_row = not odd_row

            if reverse_row:
                if y == 0:
                    x_start_points.append((self.image.width + 0.1 * self.xstep))
                    y_start_points.append(y + scaled_y_step/2)
                x_start_points.append(self.image.width)
                y_start_points.append(y + scaled_y_step/2)
            else:
                if y == 0:
                    x_start_points.append(-(0.1 * self.xstep))
                    y_start_points.append(y + scaled_y_step/2)
                x_start_points.append(0)
                y_start_points.append(y + scaled_y_step/2)


            phase = 0.0
            last_phase = 0
            last_ampl = 0
            final_step = False

            x = 1
            last_x = 1

            while not final_step:
                x += self.xstep
                final_step = (x + self.xstep) >= self.image.width

                z = int(self.image.getpixel((x, y)))

                r = z / self.ystep * ymult

                df = z / self.xsmooth
                df = max(df, min_phase_incr)
                df = min(df, max_phase_incr)

                phase += df

                delta_x = x - last_x
                delta_ampl = r - last_ampl
                delta_phase = phase - last_phase

                if not final_step:
                    if delta_phase > HALF_PI:
                        vertex_count = math.floor(delta_phase / HALF_PI)
                        integer_part = (vertex_count * HALF_PI) / delta_phase

                        delta_x_truncate = delta_x * integer_part

                        x_per_vertex =  delta_x_truncate / vertex_count
                        ampl_per_vertex = (integer_part * delta_ampl) / vertex_count

                        for _ in range(int(vertex_count)):
                            last_x = last_x + x_per_vertex
                            last_phase = last_phase + HALF_PI
                            last_ampl = last_ampl + ampl_per_vertex
                            if l_x == None and l_y == None:
                                l_x = last_x
                                l_y = scaled_y_step/2 + (y + np.sin(last_phase) * last_ampl)

                            x_points.append(last_x)
                            y_points.append(scaled_y_step/2 + (y + np.sin(last_phase) * last_ampl))
            if reverse_row:
                x_points.reverse()
                y_points.reverse()
            if reverse_row:
                x_end_points.append(0)
                y_end_points.append(y + scaled_y_step/2)
                if final_row:
                    x_end_points.append(-(0.1 * self.xstep))
                    y_end_points.append(y + scaled_y_step/2)
            else:
                x_end_points.append(self.image.width)
                y_end_points.append(y  + scaled_y_step/2)
                if final_row:
                    x_end_points.append((self.image.width + 0.1 * self.xstep))
                    y_end_points.append(y + scaled_y_step/2)
            if not final_row:
                if reverse_row:
                    x_end_points.append(-(0.1 * self.xstep))
                    y_end_points.append((y + scaled_y_step/2))
                else:
                    x_end_points.append((self.image.width + 0.1 * self.xstep))
                    y_end_points.append((y + scaled_y_step/2))

            for i, (x, y) in enumerate(zip(x_start_points, y_start_points)):
                f.write(f"{x} {y}\n")
                x, y = round(x), round(y)
                self.draw.line(((l_x, l_y),(x, y)), (0,0,0), width=int(self.stroke_width*IMAGE_SCALE_UP))
                l_x, l_y = x, y

            for i, (x, y) in enumerate(zip(x_points, y_points)):
                f.write(f"{x} {y}\n")
                x, y = round(x), round(y)
                self.draw.line(((l_x, l_y),(x, y)), (0,0,0), width=int(self.stroke_width*IMAGE_SCALE_UP))
                l_x, l_y = x, y

            for i, (x, y) in enumerate(zip(x_end_points, y_end_points)):
                f.write(f"{x} {y}\n")
                x, y = round(x), round(y)
                self.draw.line(((l_x, l_y),(x, y)), (0,0,0), width=int(self.stroke_width*IMAGE_SCALE_UP))
                l_x, l_y = x, y

            total = len(x_start_points) + len(x_points) + len(x_end_points)
            if (total > max_len):
                max_len = total

        f.close()
        return self.output_image
