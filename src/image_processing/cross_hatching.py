import math
import numpy as np
import random

from PIL import Image, ImageFilter, ImageDraw

class CrossHatching:
    def __init__(self, image: Image, layers: int, spacing: float):
        self.image = image.convert("L")
        self.layers = layers
        self.spacing = spacing

        self.color_scaler = 255/(self.layers+1)
        self.starting_angle = random.randint(0, 360)
        self.angle_delta = 360/(self.layers+1)

        self.output_image = Image.new("RGB", (self.image.width, self.image.height), color="white")
        self.draw_image = ImageDraw.Draw(self.output_image)

        for layer in range(self.layers-1, 0, -1):
            self.crossHatch(layer, self.draw_image)
        self.output_image = self.output_image.filter(ImageFilter.GaussianBlur(radius=0.5))
        self.output_image.show()

    def crossHatch(self, layer, image_draw):
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
                    image_draw.point((ix, iy), fill=(0, 0, 0))

    def trace_line(self, start, direction, length, step_size=0.5):
        x, y = start
        dx, dy = direction
        points = []

        for _ in range(int(length / step_size)):
            x += dx * step_size
            y += dy * step_size
            points.append((x, y))
        return points
