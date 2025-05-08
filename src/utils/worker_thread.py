import time
import subprocess

from PyQt5.QtCore import QThread, pyqtSignal
from PIL import Image, ImageFilter

from src.image_processing import dithering
from src.image_processing.wave import wave
from src.image_processing.cross_hatching import CrossHatching
from . import path_maker, constants


class WorkerThread(QThread):
    # Runs lengthy functions on a separate "worker thread" so the gui doesn't freeze
    # function_signal is "emited" to set the right function to run (eg. linkern, wave, dithering)
    update_signal = pyqtSignal(str)
    image_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.func = None
        self.args = ()
        self.kwargs = {}
        self.result = None
        self.image = None

    def run(self):
        if self.func:
            self.func(*self.args, **self.kwargs)

    def set_task(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def wave(self, image: Image, update_signal: pyqtSignal, ystep, xstep, xsmooth, stroke_width):
        # Converts the image to waves
        benchmark = False
        if benchmark:
            times = []
            img = None
            for _ in range(5):
                start_time = time.time()
                self.update_signal.emit("Starting conversion to wave")
                img = wave(image,
                           update_signal,
                           constants.OUTPUT_COODINATES_PATH,
                           ystep=ystep,
                           xstep=xstep,
                           xsmooth=xsmooth,
                           stroke_width=stroke_width)
                time_took = time.time() - start_time
                times.append(time_took)
                self.update_signal.emit(f"Finished in: {round(time_took, 3)} seconds")
            self.update_signal.emit(f"Average time: {round(sum(times)/len(times), 3)} seconds")
            image = img
        else:
            start_time = time.time()
            self.update_signal.emit("Starting conversion to wave")
            img = wave(image,
                       update_signal,
                       constants.OUTPUT_COODINATES_PATH,
                       ystep=ystep,
                       xstep=xstep,
                       xsmooth=xsmooth,
                       stroke_width=stroke_width)
            time_took = time.time() - start_time
            self.update_signal.emit(f"Finished in: {round(time_took, 3)} seconds")
            image = img

        self.image = image
        self.image_signal.emit()

    def crossHatch(self, image, update_signal, layers, spacing):
        self.update_signal.emit("Starting cross-hatching")
        cross_hatching = CrossHatching(image, update_signal, layers, spacing)
        image = cross_hatching.crossHatch()
        self.image = image.filter(ImageFilter.GaussianBlur(radius=0.2))
        self.update_signal.emit("Finished cross-hatching")
        self.image_signal.emit()

    def linkern(self) -> None:
        # Runs the linkern.exe program
        linker_command = f"{constants.PATH_MAKER} -o {constants.CYC_PATH} {constants.TSP_PATH}"
        linkern_result = subprocess.Popen(
            linker_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True,
        )

        # Continuous updates are emited through update_signal
        while linkern_result.poll() is None:
            line = linkern_result.stdout.readline()
            self.update_signal.emit(line)
        self.makePath(linkern_result)

    def makePath(self, linker_result: subprocess.CompletedProcess) -> None:
        # Converts the output of linkern program to usable files for this program
        if linker_result.returncode == 0:

            image = path_maker.pathMaker(
                constants.TSP_PATH, constants.CYC_PATH, constants.OUTPUT_COODINATES_PATH)
            self.image = image
            self.image_signal.emit()

    def dither(self, image: Image):
        start_time = time.time()
        self.update_signal.emit("Starting dithering")
        self.image = dithering.applyDithering(image, constants.TSP_PATH)
        self.update_signal.emit("Finished dithering")
        self.update_signal.emit(f"\nTotal run time: {time.time() - start_time} seconds\n")
        self.image_signal.emit()
