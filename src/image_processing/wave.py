import numpy as np
from PIL import Image, ImageDraw
from PyQt5.QtCore import pyqtSignal

# Alternate between red and black fill for every pixel for debug clarity
#fills = ((255,0,0), (0,0,0))
fills = ((0,0,0))

def waveAt(x, freq):
    return np.sin(x * np.pi*2 * freq)

def preCompute(color_range, size, sampling_rate_, amp_mult):
    pre_computed = []
    for i in range(color_range+1):
        temp = []
        sampling_rate = sampling_rate_
        if i <= 3:
            sampling_rate = 1
        for j in range(size * sampling_rate):
            temp.append(waveAt(j/(size*sampling_rate-1), int(i/2)) * i * amp_mult)
        pre_computed.append(temp)
    return pre_computed

def wave(image: Image,
         update_signal: pyqtSignal,
         line_frequency=400,
         lines=100,
         color_range=10,
         size_x=20) -> Image:
    og_width, og_height = image.width, image.height
    wave_aspect_ratio = (line_frequency * size_x)/og_width
    size_y = int(og_height * wave_aspect_ratio / lines)
    amp_mult = size_y/2/color_range
    img = image.resize((line_frequency, lines))

    pixels = np.array(img)
    height, width = pixels.shape
    new_height, new_width = height * size_y, width * size_x

    image = Image.new("RGB", (new_width, new_height), color="white")
    draw = ImageDraw.Draw(image)

    sample_per_wave = 5
    pre_computed = preCompute(color_range, size_x, sample_per_wave, amp_mult)

    for y in range(lines):
        update_signal.emit(f"{int(y/(lines-1) * 100)}%")
        for x in range(line_frequency):
            fill = fills[x%2]
            pixels[y, x] = round(pixels[y, x] / (256 / color_range))

            pixel = pixels[y, x]
            pre_computed_wave = pre_computed[pixel]
            for i_ in range(len(pre_computed_wave)-1):
                i = i_/(len(pre_computed_wave)/size_x)
                x_pos = x * size_x + i
                y_pos_local = pre_computed_wave[i_]
                y_pos = (y * size_y + size_y / 2) + y_pos_local

                x_pos_n = x * size_x + i + 1
                y_pos_local = pre_computed_wave[i_+1]
                y_pos_n = (y * size_y + size_y / 2) + y_pos_local
                draw.line(((x_pos, y_pos), (x_pos_n, y_pos_n)), fill=fill, width=2)
    return image
