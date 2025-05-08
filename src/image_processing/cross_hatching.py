import math
import numpy as np
import random

from PIL import Image, ImageFilter, ImageDraw
from PyQt5.QtCore import pyqtSignal

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

    def crossHatch(self):
        for layer in range(self.layers-0, 0, -1):
            self.hatchLayer(layer)
            self.update_signal.emit(f"Hatching {int((self.layers-layer+1)/self.layers*100)}%")
        self.output_image = self.output_image.filter(ImageFilter.GaussianBlur(radius=0.5))
        return self.output_image

    """ TODO: instead of ploting points along the whole line, draw a line from start to end """
    def hatchLayer(self, layer):
        angle_deg = self.starting_angle + layer * self.angle_delta
        angle_rad = math.radians(angle_deg)

        # Direction of the hatching lines
        dx = math.cos(angle_rad)
        dy = math.sin(angle_rad)

        # Perpendicular direction for spacing
        pdx = -dy
        pdy = dx

        # Maximum distance to cover the image diagonally
        diag = int(math.hypot(self.image.width, self.image.height))

        for i in range(-diag, diag, int(self.spacing)):
            # Start point along the perpendicular direction
            cx = self.image.width // 2 + pdx * i
            cy = self.image.height // 2 + pdy * i

            # Trace in both directions from this center point
            line_points = self.trace_line((cx, cy), (dx, dy), diag)
            line_points += self.trace_line((cx, cy), (-dx, -dy), diag)

            for x, y in line_points:
                ix, iy = int(x), int(y)
                if not (0 <= ix < self.image.width and 0 <= iy < self.image.height):
                    continue
                if int(self.image.getpixel((ix, iy)) / self.color_scaler) <= layer:
                    self.image_draw.point((ix, iy), fill=(0, 0, 0))
        return self.image

    def trace_line(self, start, direction, length, step_size=0.5):
        x, y = start
        dx, dy = direction
        points = []

        for _ in range(int(length / step_size)):
            x += dx * step_size
            y += dy * step_size
            points.append((x, y))
        return points
