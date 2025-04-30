import math
import numpy as np

from PyQt5.QtCore import pyqtSignal
from PIL import Image, ImageOps, ImageDraw

TWO_PI = 2 * np.pi
HALF_PI = 0.5 * np.pi
IMAGE_SCALE_UP = 3

def wave(image: Image, update_signal: pyqtSignal, output_file: str, ystep=100, xstep=3, xsmooth=128, stroke_width=1):
    # xsmooth = 150 # Bigger => less freq
    image = ImageOps.invert(image.convert("L"))
    image = image.resize((image.width*IMAGE_SCALE_UP, image.height*IMAGE_SCALE_UP))

    output_image = Image.new("RGB", (image.width, image.height), color="white")
    draw = ImageDraw.Draw(output_image)

    ymult = 6
    scale_factor = 1.0 / IMAGE_SCALE_UP

    min_phase_incr = 10 * TWO_PI / (image.width / xstep)
    max_phase_incr =  TWO_PI * xstep / stroke_width

    scaled_y_step = image.height / ystep
    odd_row = False
    final_row = False
    reverse_row = False

    f = open(output_file, "w")
    l_x, l_y = None, None
    for y_ in np.arange(0, image.height, scaled_y_step):

        x_start_points = []
        y_start_points = []
        x_points = []
        y_points = []
        x_end_points = []
        y_end_points = []

        y = y_.item()
        odd_row = not odd_row

        if (y + scaled_y_step) >= image.height:
            final_row = True
        reverse_row = not odd_row

        if reverse_row:
            if y == 0:
                x_start_points.append((image.width + 0.1 * xstep))
                y_start_points.append(y + scaled_y_step/2)
            x_start_points.append(image.width)
            y_start_points.append(y + scaled_y_step/2)
        else:
            if y == 0:
                x_start_points.append(-(0.1 * xstep))
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
            x += xstep
            final_step = (x + xstep) >= image.width

            z = int(image.getpixel((x, y)))

            r = z / ystep * ymult

            df = z / xsmooth
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
                x_end_points.append(-(0.1 * xstep))
                y_end_points.append(y + scaled_y_step/2)
        else:
            x_end_points.append(image.width)
            y_end_points.append(y  + scaled_y_step/2)
            if final_row:
                x_end_points.append((image.width + 0.1 * xstep))
                y_end_points.append(y + scaled_y_step/2)
        if not final_row:
            if reverse_row:
                x_end_points.append(-(0.1 * xstep))
                y_end_points.append((y + scaled_y_step/2))
            else:
                x_end_points.append((image.width + 0.1 * xstep))
                y_end_points.append((y + scaled_y_step/2))

        for i, (x, y) in enumerate(zip(x_start_points, y_start_points)):
            f.write(f"{x} {y}\n")
            x, y = round(x), round(y)
            draw.line(((l_x, l_y),(x, y)), (0,0,0), width=stroke_width*IMAGE_SCALE_UP)
            l_x, l_y = x, y

        for i, (x, y) in enumerate(zip(x_points, y_points)):
            f.write(f"{x} {y}\n")
            x, y = round(x), round(y)
            draw.line(((l_x, l_y),(x, y)), (0,0,0), width=stroke_width*IMAGE_SCALE_UP)
            l_x, l_y = x, y

        for i, (x, y) in enumerate(zip(x_end_points, y_end_points)):
            f.write(f"{x} {y}\n")
            x, y = round(x), round(y)
            draw.line(((l_x, l_y),(x, y)), (0,0,0), width=stroke_width*IMAGE_SCALE_UP)
            l_x, l_y = x, y


    f.close()
    # output_image.show()
    return output_image
