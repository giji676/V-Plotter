import time
import subprocess
import numpy as np

from PyQt5.QtCore import QThread, pyqtSignal
from PIL import Image

from src.image_processing import dithering
from src.image_processing.wave import wave
from . import FunctionTypeEnum, constants


class WorkerThread(QThread):
    # Runs lengthy functions on a separate "worker thread" so the gui doesn't freeze
    # function_signal is "emited" to set the right function to run (eg. linkern, wave, dithering)
    update_signal = pyqtSignal(str)
    finish_signal = pyqtSignal()
    image_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.result = None
        self.image = None
        self.function_type = None
        self.wave_smooth = None

    def run(self):
        # Called by QThread automatically when WorkerThread.start() is called
        if self.function_type == FunctionTypeEnum.WAVE:
            self.image = self.wave(self.image)
            self.image_signal.emit()
        elif self.function_type == FunctionTypeEnum.LINKERN:
            self.linkern()
        elif self.function_type == FunctionTypeEnum.DITHER:
            self.image = self.dither(self.image)
            self.image_signal.emit()

    def wave(self, image: Image) -> Image:
        # Converts the image to waves
        f = open(constants.OUTPUT_COODINATES_PATH, "w")

        start_time = time.time()
        self.update_signal.emit("Starting conversion to wave")
        image = wave(image,
                     self.update_signal,
                     line_frequency=int(image.width/2),
                     lines=100,
                     color_range=20,
                     size_x=20)
        self.update_signal.emit(f"Finished in: {round(time.time() - start_time, 3)} seconds")
        self.finish_signal.emit()

        return image

    def linkern(self) -> None:
        # Runs the linkern.exe program
        linker_command = f"{constants.PATH_MAKER} -o {constants.CYC_PATH} {constants.TSP_PATH}"
        linker_result = subprocess.Popen(
            linker_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True,
        )

        # Continuous updates are emited through update_signal
        while linker_result.poll() is None:
            line = linker_result.stdout.readline()
            self.update_signal.emit(line)

        # Finished result/output emited through finish_signal
        self.result = linker_result

        # Emit a signal with the output
        self.finish_signal.emit()

    def dither(self, image) -> Image:
        start_time = time.time()
        self.update_signal.emit("Starting dithering")
        image = dithering.applyDithering(image, constants.TSP_PATH)
        self.result = f"\nTotal run time: {time.time() - start_time} seconds\n"
        self.finish_signal.emit()
        return image

    def getResult(self) -> subprocess.CompletedProcess:
        return self.result

