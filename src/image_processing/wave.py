import numpy as np
from PIL import Image, ImageDraw
from PyQt5.QtCore import pyqtSignal
import multiprocessing as mp

# Alternate between red and black fill for every pixel for debug clarity
fills = ((0, 0, 0))

def waveAt(x, freq):
    return np.sin(x * np.pi * 2 * freq)

def preCompute(color_range, size, sampling_rate_, amp_mult):
    pre_computed = []
    for i in range(color_range+1):
        temp = []
        sampling_rate = sampling_rate_ if i > 3 else 1
        for j in range(size * sampling_rate):
            temp.append(waveAt(j/(size * sampling_rate - 1), int(i / 2)) * i * amp_mult)
        pre_computed.append(temp)
    return pre_computed

def process_row(y, pixels_row, pre_computed, size_x, size_y, line_frequency):
    """
    Processes a single row of pixels, drawing waveforms for each column.
    """
    img_row = Image.new("RGB", (size_x * line_frequency, size_y), color="white")
    draw = ImageDraw.Draw(img_row)

    start = 0
    end = line_frequency

    # Flips 0 : line_frequency to line_frequency : 0 in case o for-loop
    # to invert the start and finish of the row being processed
    increment = 1
    if y % 2 == 0:
        start, end = end-1, start-1
        increment = -1

    for x in range(start, end, increment):
        fill = fills[x % 2]

        # Ensure pixel is within 0-255 range
        pixels_row[x] = min(max(pixels_row[x], 0), 255)

        # Safely map pixel intensity to pre_computed index
        pixel = min(max(round(pixels_row[x] / (256 / len(pre_computed))), 0), len(pre_computed) - 1)

        pre_computed_wave = pre_computed[pixel]

        for i_abs in range(len(pre_computed_wave) - 1):
            # Adjusts the wave for the extra sampling rate
            # e.g if a wave of size_x=20 has sampling rate of 3,
            # we have 20*3=60 values, which needs to be mapped back to size_x number of x positions
            i = i_abs / (len(pre_computed_wave) / size_x)

            offset = 0
            if y % 2 == 0:
                offset = 1

            x_pos = (x+offset) * size_x + i*increment
            y_pos_local = pre_computed_wave[i_abs]
            y_pos = (size_y / 2) + y_pos_local

            x_pos_n = (x+offset) * size_x + (i*increment) + increment
            y_pos_local_n = pre_computed_wave[i_abs + 1]
            y_pos_n = (size_y / 2) + y_pos_local_n

            draw.line(((x_pos, y_pos), (x_pos_n, y_pos_n)), fill=fill, width=2)

    return y, img_row

def wave(image: Image, update_signal: pyqtSignal, line_frequency=400, lines=100, color_range=10, size_x=20) -> Image:
    """
    Applies wave transformation to an image using multiprocessing for speed.
    """
    og_width, og_height = image.width, image.height
    wave_aspect_ratio = (line_frequency * size_x) / og_width
    size_y = int(og_height * wave_aspect_ratio / lines)
    amp_mult = size_y / 2 / color_range
    img = image.resize((line_frequency, lines))

    pixels = np.array(img)
    new_height, new_width = lines * size_y, line_frequency * size_x

    sample_per_wave = 10
    pre_computed = preCompute(color_range, size_x, sample_per_wave, amp_mult)

    # Use multiprocessing pool to process each row in parallel
    with mp.Pool(processes=mp.cpu_count()) as pool:
        results = pool.starmap(process_row, [
            (y, pixels[y], pre_computed, size_x, size_y, line_frequency)
            for y in range(lines)
        ])

    # Merge processed rows into the final image
    final_image = Image.new("RGB", (new_width, new_height), color="white")
    for y, img_row in sorted(results):
        final_image.paste(img_row, (0, y * size_y))

        update_signal.emit(f"{int(y / (lines - 1) * 100)}%")

    return final_image
