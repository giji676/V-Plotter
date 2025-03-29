import math
import random

from PIL import Image, ImageDraw


class Stippling:
    def __init__(self, image: Image):
        self.image = image.convert("L")

    def stipple(self):
        points = self.generateRandomPoints(30)
        self.drawPixels(points)
        self.drawLines(points)

    def eucDist(self, x1, y1, x2, y2) -> float:
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def drawLines(self, arr):
        image_width = self.image.width
        image_height = self.image.height
        img = Image.new("RGB", (self.image.width, self.image.height), color="white")
        draw = ImageDraw.Draw(img)
        colors = [
            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            for _ in arr
        ]

        regions = [[-1] * image_width for _ in range(image_height)]

        for y in range(image_height):
            for x in range(image_width):
                min_dist = float("inf")
                best_index = -1

                for i, (px, py) in enumerate(arr):
                    dist = self.eucDist(x, y, px, py)
                    if dist < min_dist:
                        min_dist = dist
                        best_index = i

                img.putpixel((x, y), colors[best_index])
                regions[y][x] = best_index

        # Detect Voronoi edges
        edges = set()
        for y in range(1, image_height - 1):
            for x in range(1, image_width - 1):
                neighbors = {
                    regions[y + dy][x + dx]
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                }
                if len(neighbors) > 1:
                    edges.add((x, y))

        # Draw edges in black
        for x, y in edges:
            img.putpixel((x, y), (0, 0, 0))

        # Draw original points in red
        for px, py in arr:
            draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill=(255, 0, 0))

        img.show()

    def generateRandomPoints(self, n):
        arr = []
        i = 0
        while i < n:
            x = random.randint(0, self.image.width - 1)
            y = random.randint(0, self.image.height - 1)
            if random.randint(0, 100) > self.image.getpixel((x, y)):
                arr.append((x, y))
                i += 1

        return arr

    def drawPixels(self, arr):
        img = Image.new("RGB", (self.image.width, self.image.height), color="white")
        draw = ImageDraw.Draw(img)

        for x, y in arr:
            draw.point((x, y), fill=(0, 0, 0))
        img.show()
