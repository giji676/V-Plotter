import numpy as np

scaled_colour_range = 10
pixel_wave_size = 40
amplitude_mult = pixel_wave_size / scaled_colour_range / 2

# returns array of the waves and their multipliers
def genWave(pixels: np.array):
    height, width = pixels.shape
    new_height, new_width = height * pixel_wave_size, width * pixel_wave_size

    wave_function_arr = []
    for y in range(height):
        wave_function_row_arr = []
        for x in range(width):
            n_x = x
            # Every other y level needs to start from the end so the other of the horizontal lines is: left-right-right-left...
            if y % 2 != 0:
                n_x = width - 1 - x
            amplitude = 0
            frequency = 0

            pixels[y, n_x] = round(pixels[y, n_x] / ((2**8)/scaled_colour_range))
            frequency = pixels[y, n_x]
            amplitude = pixels[y, n_x] * amplitude_mult

            wave_function_row_arr.append([frequency, amplitude])
        wave_function_arr.append(wave_function_row_arr)

    return wave_function_arr


# image getting turned into waves, and the sin function parameters getting saved to wave_function_arr successfully.
# now use the interpolation to smooth them
