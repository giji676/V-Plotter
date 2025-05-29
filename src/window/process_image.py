import os

from PIL import Image, ImageDraw, ImageOps
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import (QFileDialog, QGridLayout,
                             QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QSizePolicy, QSpacerItem,
                             QTextEdit, QWidget, QCheckBox, QComboBox,
                             QFrame, QRadioButton)

from src.utils import constants, svg_parser, WorkerThread
from .process_canvas import ProcessCanvas

# Image processing windows
class ProcessImage(QWidget):
    def __init__(self):
        super().__init__()
        self.createUIWidgets()
        self.setupUI()

    def createUIWidgets(self) -> None:
        # Creating the lables and inputs
        self.btn_open_image = QPushButton("Open Image")
        self.btn_clear_all = QPushButton("Clear All")
        self.txt_scale = QLineEdit("2")
        self.btn_rotate_90 = QPushButton("Rotate")
        self.btn_scale = QPushButton("Scale")
        self.btn_grayscale = QPushButton("Grayscale")
        self.btn_colourscale = QPushButton("Colour scale")
        self.btn_remove_bg = QPushButton("Remove BG")
        self.btn_convert_to_steps = QPushButton("Convert to steps")
        self.btn_save_as = QPushButton("Save As")
        self.btn_crop = QPushButton("Crop")
        self.cbx_min_pen_pickup = QCheckBox("Use Minimum Pen Pickup Distance")
        self.cmb_processing_selector = QComboBox()

        # TSP
        self.btn_dither = QPushButton("Dither")
        self.btn_make_path = QPushButton("Make Path")

        # WAVE
        self.lbl_ystep = QLabel("Lines")
        self.txt_ystep = QLineEdit("100")
        self.lbl_xstep = QLabel("X Step")
        self.txt_xstep = QLineEdit("3")
        self.lbl_xsmooth = QLabel("X Smooth")
        self.txt_xsmooth = QLineEdit("128")
        self.lbl_stroke_width = QLabel("Stroke Width")
        self.txt_stroke_width = QLineEdit("1")
        self.lbl_wave_dir = QLabel("Wave Direction")
        self.rbt_wave_horizontal = QRadioButton("Horizontal")
        self.rbt_wave_vertical = QRadioButton("Vertical")
        self.rbt_wave_horizontal.setChecked(True)
        self.btn_wave = QPushButton("Wave")

        # CROSS HATCHING
        self.lbl_layers = QLabel("Layers")
        self.txt_layers = QLineEdit("10")
        self.lbl_spacing = QLabel("Spacing")
        self.txt_spacing = QLineEdit("5")
        self.btn_cross_hatch = QPushButton("Cross-Hatch")

        # LINE DISTORT
        self.lbl_rows= QLabel("Rows")
        self.txt_rows= QLineEdit("50")
        self.lbl_distort_mult = QLabel("Distort Multiplier")
        self.txt_distort_mult = QLineEdit("0.8")
        self.btn_line_distort = QPushButton("Line-Distort")

    def setupUI(self) -> None:
        self.left_input_panel = QWidget()
        self.left_input_panel.setStyleSheet("background-color: #EEE;")
        self.image_canvas = ProcessCanvas()
        self.image_canvas.process_image_window = self

        self.cmb_processing_selector.addItems(["Select Processing Type", "TSP", "Wave", "Cross-Hatching", "Line-Distort"])
        self.cmb_processing_selector.currentTextChanged.connect(self.onProcessingChange)

        self.frames = {}
        self.frames["TSP"] = self.createTSPFrame()
        self.frames["Wave"] = self.createWaveFrame()
        self.frames["Cross-Hatching"] = self.createCrossHatchFrame()
        self.frames["Line-Distort"] = self.createLineDistortFrame()

        self.lbl_output = QLabel("Output")
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)

        # Connecting the inputs to their functions
        self.btn_open_image.clicked.connect(self.openImage)
        self.btn_clear_all.clicked.connect(self.clearAll)
        self.btn_rotate_90.clicked.connect(self.image_canvas.rotate90)
        self.btn_scale.clicked.connect(self.scaleImage)
        self.btn_grayscale.clicked.connect(self.image_canvas.grayscale)
        self.btn_dither.clicked.connect(self.startDither)
        self.btn_wave.clicked.connect(self.startWave)
        self.btn_cross_hatch.clicked.connect(self.startCrossHatch)
        self.btn_line_distort.clicked.connect(self.startLineDistort)
        self.btn_remove_bg.clicked.connect(self.image_canvas.removeBg)
        self.btn_colourscale.clicked.connect( self.image_canvas.quantizeGrayscaleImage)
        self.btn_make_path.clicked.connect(self.startLinkern)
        self.btn_convert_to_steps.clicked.connect(self.image_canvas.convertToSteps)
        self.btn_convert_to_steps.setObjectName("testBtn")
        self.btn_save_as.clicked.connect(self.image_canvas.saveAs)
        self.btn_crop.clicked.connect(self.image_canvas.crop)

        self.vertical_spacer = QSpacerItem(0, 20, QSizePolicy.Fixed, QSizePolicy.Expanding)

        # Adding the lables and inputs to the layout
        self.lyt_inputs = QGridLayout()
        self.lyt_inputs.addWidget(self.btn_open_image, 0, 0)
        self.lyt_inputs.addWidget(self.btn_save_as, 0, 1)
        self.lyt_inputs.addWidget(self.btn_clear_all, 1, 0)
        self.lyt_inputs.addWidget(self.btn_rotate_90, 1, 1)
        self.lyt_inputs.addWidget(self.btn_scale, 2, 0)
        self.lyt_inputs.addWidget(self.txt_scale, 2, 1)
        self.lyt_inputs.addWidget(self.btn_grayscale, 3, 0)
        self.lyt_inputs.addWidget(self.btn_colourscale, 3, 1)
        self.lyt_inputs.addWidget(self.btn_remove_bg, 4, 0)
        self.lyt_inputs.addWidget(self.btn_crop, 4, 1)
        self.lyt_inputs.addWidget(self.cmb_processing_selector, 5, 0, 1, 2)

        for frame in self.frames.values():
            self.lyt_inputs.addWidget(frame, 6, 0, 1, 2)
            frame.setVisible(False)

        self.lyt_inputs.addWidget(self.cbx_min_pen_pickup, 7, 0)
        self.lyt_inputs.addWidget(self.btn_convert_to_steps, 8, 0, 1, 2)

        self.lyt_inputs.addWidget(self.lbl_output, 9, 0)
        self.lyt_inputs.addWidget(self.output_text_edit, 10, 0, 1, 2)

        self.lyt_inputs.addItem(self.vertical_spacer)

        self.left_input_panel.setLayout(self.lyt_inputs)

        self.lyt_process_image_tab = QHBoxLayout()
        self.lyt_process_image_tab.addWidget(self.left_input_panel)
        self.lyt_process_image_tab.addWidget(self.image_canvas)
        self.lyt_process_image_tab.setStretchFactor(self.left_input_panel, 2)
        self.lyt_process_image_tab.setStretchFactor(self.image_canvas, 7)

        self.worker_thread = WorkerThread()
        self.worker_thread.update_signal.connect(self.updateOutput)
        self.worker_thread.image_signal.connect(self.imageOutput)

        self.setLayout(self.lyt_process_image_tab)

    def onProcessingChange(self, val):
        for frame in self.frames.values():
            frame.setVisible(False)

        if val in self.frames:
            self.frames[val].setVisible(True)

    def createWaveFrame(self) -> QFrame:
        frame = QFrame()

        lyt_frame = QGridLayout(frame)

        lyt_frame.addWidget(self.lbl_ystep, 0, 0)
        lyt_frame.addWidget(self.txt_ystep, 0, 1)
        lyt_frame.addWidget(self.lbl_xstep, 1, 0)
        lyt_frame.addWidget(self.txt_xstep, 1, 1)
        lyt_frame.addWidget(self.lbl_xsmooth, 2, 0)
        lyt_frame.addWidget(self.txt_xsmooth, 2, 1)
        lyt_frame.addWidget(self.lbl_stroke_width, 3, 0)
        lyt_frame.addWidget(self.txt_stroke_width, 3, 1)
        lyt_frame.addWidget(self.lbl_wave_dir, 4, 0)
        lyt_frame.addWidget(self.rbt_wave_horizontal, 4, 1)
        lyt_frame.addWidget(self.rbt_wave_vertical, 5, 1)
        lyt_frame.addWidget(self.btn_wave, 6, 0, 2, 2)

        return frame

    def createLineDistortFrame(self) -> QFrame:
        frame = QFrame()

        lyt_frame = QGridLayout(frame)

        lyt_frame.addWidget(self.lbl_rows, 0, 0)
        lyt_frame.addWidget(self.txt_rows, 0, 1)
        lyt_frame.addWidget(self.lbl_distort_mult, 1, 0)
        lyt_frame.addWidget(self.txt_distort_mult, 1, 1)
        lyt_frame.addWidget(self.btn_line_distort, 2, 0, 2, 2)

        return frame

    def createCrossHatchFrame(self) -> QFrame:
        frame = QFrame()

        lyt_frame = QGridLayout(frame)
        lyt_frame.addWidget(self.lbl_layers, 0, 0)
        lyt_frame.addWidget(self.txt_layers, 0, 1)
        lyt_frame.addWidget(self.lbl_spacing, 1, 0)
        lyt_frame.addWidget(self.txt_spacing, 1, 1)
        lyt_frame.addWidget(self.btn_cross_hatch, 2, 0, 2, 2)

        return frame

    def createTSPFrame(self) -> QFrame:
        frame = QFrame()

        lyt_frame = QGridLayout(frame)
        lyt_frame.addWidget(self.btn_dither, 0, 0)
        lyt_frame.addWidget(self.btn_make_path, 0, 1)

        return frame

    def startLinkern(self):
        if os.path.exists(constants.TSP_PATH):
            self.worker_thread.set_task(self.worker_thread.linkern)
            self.worker_thread.start()

    def startWave(self):
        if self.image_canvas.input_image is None:
            return
        image = self.image_canvas.qpixmapToImage2(self.image_canvas.input_image).convert("L")

        self.worker_thread.set_task(self.worker_thread.wave,
                                    image,
                                    self.worker_thread.update_signal,
                                    int(self.txt_ystep.text()),
                                    float(self.txt_xstep.text()),
                                    float(self.txt_xsmooth.text()),
                                    float(self.txt_stroke_width.text()),
                                    self.rbt_wave_horizontal.isChecked())

        self.worker_thread.start()

    def startLineDistort(self):
        if self.image_canvas.input_image is None:
            return
        image = self.image_canvas.qpixmapToImage2(self.image_canvas.input_image).convert("L")

        self.worker_thread.set_task(self.worker_thread.lineDistort,
                                    image,
                                    self.worker_thread.update_signal,
                                    int(self.txt_rows.text()),
                                    float(self.txt_distort_mult.text()))

        self.worker_thread.start()

    def startCrossHatch(self):
        if self.image_canvas.input_image is None:
            return
        image = self.image_canvas.qpixmapToImage2(self.image_canvas.input_image).convert("L")

        self.worker_thread.set_task(self.worker_thread.crossHatch,
                                    image,
                                    self.worker_thread.update_signal,
                                    int(self.txt_layers.text()),
                                    int(self.txt_spacing.text()))

        self.worker_thread.start()

    def startDither(self):
        if self.image_canvas.input_image is None:
            return

        image = self.image_canvas.qimageToPil(self.image_canvas.input_image).convert("L")
        #image = Image.fromqpixmap(self.image_canvas.input_image).convert("L")
        image = ImageOps.invert(image)

        self.worker_thread.set_task(self.worker_thread.dither, image)
        self.worker_thread.start()

    def updateOutput(self, output):
        self.output_text_edit.append(output)

    def imageOutput(self):
        image = self.worker_thread.image
        if image == None:
            return
        self.image_canvas.input_image = self.image_canvas.imageToQImage(image)
        self.image_canvas.update()

    def scaleImage(self) -> None:
        if self.image_canvas.input_image is None:
            return

        self.image_canvas.image_scale = float(self.txt_scale.text())
        self.image_canvas.scale()

    def clearAll(self) -> None:
        self.image_canvas.input_image = None
        self.image_canvas.scale_factor = 1.0
        self.image_canvas.update()
        self.output_text_edit.clear()

    def openImage(self) -> None:
        # Opens the windows for opening the image
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_filter = "Images (*.png *.jpg *.jpeg *.bmp *.svg)"
        self.input_image, _ = QFileDialog.getOpenFileName(
            self, "Open Image File", "", file_filter, options=options
        )

        if ".svg" in self.input_image:
            self.parseSvg(self.input_image)
            return

        self.image_canvas.loadImage(self.input_image)

    def parseSvg(self, path) -> None:
        image = svg_parser.parseSvg(path, self.updateOutput)
        if image == None:
            return

        image = image.convert("RGBA")
        data = image.tobytes("raw", "RGBA")

        self.image_canvas.input_image = QImage(
            data, image.size[0], image.size[1], QImage.Format_RGBA8888
        )
        self.image_canvas.update()

    def gcodePlotter(self) -> Image:
        f = open(constants.OUTPUT_COODINATES_PATH, "r")
        max_x, max_y = 0, 0

        # Find max x and y
        for line in f:
            line = line.strip()

            if line == "PENUP" or line == "PENDOWN":
                continue

            line = line.split()
            x, y = float(line[0]), float(line[1])

            if x > max_x:
                max_x = x
            if y > max_y:
                max_y = y
        f.close()
        max_x, max_y = int(max_x) + 1, int(max_y) + 1

        image = Image.new("RGB", (max_x, max_y), color="white")
        draw = ImageDraw.Draw(image)

        x, y = 0, 0
        pen_down = False
        flipped_image = []

        f = open(constants.OUTPUT_COODINATES_PATH, "r")

        # Flip the image horizontaly and draw the image
        for line in f:
            line = line.strip()

            if line == "PENUP":
                pen_down = False
                flipped_image.append(f"{line}\n")
            elif line == "PENDOWN":
                pen_down = True
                flipped_image.append(f"{line}\n")

            else:
                line = line.split()
                n_x, n_y = float(line[0]), float(line[1])
                if pen_down:
                    draw.line(((x, max_y - y), (n_x, max_y - n_y)),
                              fill=(0, 0, 0))
                flipped_image.append(f"{n_x} {max_y - n_y}\n")

                x, y = n_x, n_y

        f.close()
        f = open(constants.OUTPUT_COODINATES_PATH, "w")
        f.writelines(flipped_image)
        f.close()

        return image

