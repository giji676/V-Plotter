import os
import time
import subprocess
import numpy as np
from rembg import remove, new_session

from PIL import Image
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPixmap, QTransform
from PyQt5.QtWidgets import QWidget

from src.utils import constants, path_maker, to_steps


# Canvas that displays the image being processed
class ProcessCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 400, 400)
        self.scale_factor = 1.0
        self.setMouseTracking(True)
        self.dragging = False
        self.cropping = False
        self.start_pos = QPoint()
        self.cur_pos = QPoint()
        self.last_pos = QPoint()
        self.delta = QPoint()

        self.crop_start_pos = QPoint()
        self.crop_end_pos = QPoint()
        self.crop_cur_pos = QPoint()
        self.crop_pressed = False

        self.process_image_window = None
        self.settings = None

        self.image_scale = 1

        self.input_image = None
        self.processed_image = None

    def quantizeGrayscaleImage(self) -> None:
        if self.input_image is None:
            return
        # Sets the grayscale image colour range to <num_colors> - so instead of 255 colour values it only has <num_colors> amount
        num_colors = 10
        scaling_factor = 255 / (num_colors - 1)

        quantized_image = self.input_image.copy()

        for x in range(quantized_image.width()):
            for y in range(quantized_image.height()):
                original_pixel_value = quantized_image.pixelColor(x, y).red()

                scaled_value = int(
                    int(original_pixel_value / scaling_factor) * scaling_factor
                )

                quantized_pixel_color = QColor(
                    scaled_value, scaled_value, scaled_value)
                quantized_image.setPixelColor(x, y, quantized_pixel_color)

        self.input_image = quantized_image
        self.update()

    def loadImage(self, path: str) -> None:
        if not os.path.exists(path):
            return

        self.input_image = QImage(path)
        self.update()

    def makePath(self, linker_result: subprocess.CompletedProcess) -> None:
        # Converts the output of linkern program to usable files for this program
        # linker_result = self.linkern()

        if linker_result.returncode == 0:

            image = path_maker.pathMaker(
                constants.TSP_PATH, constants.CYC_PATH, constants.OUTPUT_COODINATES_PATH)

            image = image.convert("RGBA")
            data = image.tobytes("raw", "RGBA")

            self.input_image = QImage(
                data, image.size[0], image.size[1], QImage.Format_RGBA8888
            )
            self.update()

    def convertToSteps(self) -> None:
        # Converts the coordinates of the points to steps of the stepper motor based on the <settings>
        if not os.path.exists(constants.OUTPUT_COODINATES_PATH):
            return
        steps_output = to_steps.convertToSteps(
            self.settings, constants.OUTPUT_COODINATES_PATH, constants.OUTPUT_STEPS_PATH, fit=True, min_pen_pickup=self.process_image_window.cbx_min_pen_pickup.isChecked()
        )
        if steps_output:
            self.process_image_window.updateOutput(steps_output)

    # TODO: fix the qimageToPil so it works properly, get rid of qpixmapToImage2 after
    def qimageToPil(self, qimage):
        # Get image dimensions
        width = qimage.width()
        height = qimage.height()

        # Convert QImage to a format suitable for PIL
        qimage = qimage.convertToFormat(QImage.Format_RGBA8888)

        # Get the binary data from QImage
        ptr = qimage.constBits()
        ptr.setsize(height * width * 4)  # 4 bytes per pixel (RGBA)

        # Convert to numpy array and reshape
        arr = np.frombuffer(ptr, np.uint8).reshape(height, width, 4)

        # Convert numpy array to PIL Image
        return Image.fromarray(arr)

    def qpixmapToImage2(self, qimage) -> Image:
        # Convert QImage to numpy array (raw data)
        width = qimage.width()
        height = qimage.height()

        # Extract the pixel data from QImage
        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())

        # Create a numpy array from the QImage data
        arr = np.array(ptr).reshape((height, width, 4))  # 4 channels (RGBA)
        arr = arr[..., [2, 1, 0, 3]]  # Swap the Blue and Red channels

        # Convert numpy array to PIL Image
        pil_image = Image.fromarray(arr, 'RGBA')

        return pil_image

    def removeBg(self) -> None:
        # Removes the background of the image, and replaces it with white background instead of transparent
        if self.input_image is None:
            return

        image = self.qpixmapToImage2(self.input_image)

        session = new_session("u2net_lite", providers=["CPUExecutionProvider"])
        image = remove(image, session=session)

        jpg_image = Image.new("RGB", image.size, "white")
        jpg_image.paste(image, (0, 0), image)
        image = jpg_image

        image = image.convert("RGBA")
        data = image.tobytes("raw", "RGBA")
        self.input_image = QImage(
            data, image.size[0], image.size[1], QImage.Format_RGBA8888
        )
        self.update()

    def rotate90(self) -> None:
        if self.input_image is None:
            return

        self.input_image = self.input_image.transformed(QTransform().rotate(90))
        self.update()

    def grayscale(self) -> None:
        # Converts the image to grayscale
        if self.input_image is None:
            return

        self.input_image = self.input_image.convertToFormat(
            QImage.Format_Grayscale8)
        self.update()

    def scale(self) -> None:
        if self.input_image is None:
            return

        self.input_image = self.input_image.scaled(
            int(self.input_image.width() / self.image_scale),
            int(self.input_image.height() / self.image_scale),
        )
        self.update()

    def crop(self) -> None:
        if self.input_image is None:
            return
        self.cropping = not self.cropping

    def saveImage(self) -> None:
        if self.input_image is None:
            return
        self.input_image.save("test.png")

    def paintEvent(self, event) -> None:
        # QTs function, updates the canvas
        if self.input_image is None:
            return

        painter = QPainter(self)
        transform = QTransform()
        transform.scale(self.scale_factor, self.scale_factor)
        transform.translate(self.cur_pos.x(), self.cur_pos.y())
        painter.setTransform(transform)
        painter.drawPixmap(0, 0, QPixmap.fromImage(self.input_image))

        if self.cropping and self.crop_pressed:
            painter.drawRect(self.crop_start_pos.x(),
                             self.crop_start_pos.y(),
                             self.crop_end_pos.x(),
                             self.crop_end_pos.y())

    # Mouse events for moving the image around and zooming in
    def wheelEvent(self, event):
        # Zoom in/out with the mouse wheel
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 1 / 1.1
        self.scale_factor *= zoom_factor
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.cropping:
                self.crop_start_pos = event.pos() - self.last_pos
                self.crop_pressed = True
            else:
                self.dragging = True
                self.start_pos = event.pos() - self.last_pos * self.scale_factor

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.delta = event.pos()
            self.cur_pos = (self.delta - self.start_pos) / self.scale_factor
            self.last_pos = self.cur_pos
            self.update()
        elif self.cropping:
            self.delta = event.pos()
            self.crop_end_pos = (self.delta - self.crop_start_pos - self.last_pos) / self.scale_factor
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.dragging:
                self.dragging = False
            elif self.cropping:
                self.cropping = False
                self.crop_pressed = False
