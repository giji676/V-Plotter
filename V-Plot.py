import os
import time
import sys

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QSplashScreen

from src.utils import constants
from src.window import ProcessImage, ConfigureMachine


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        tab_widget = QTabWidget(self)

        self.tab_configure_machine = ConfigureMachine()
        self.tab_process_image = ProcessImage()

        self.tab_process_image.image_canvas.settings = self.tab_configure_machine.settings
        # vvvv temp
        self.tab_process_image.image_canvas.loadImage(r"C:\Users\tvten\Desktop\TS_.png")

        tab_widget.addTab(self.tab_process_image, "Process Image")
        tab_widget.addTab(self.tab_configure_machine, "Configure Machine")

        self.setCentralWidget(tab_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = QSplashScreen()
    splash.setPixmap(QPixmap(constants.SPLASH_PATH).scaled(400, 400))
    splash.show()

    with open(constants.STYLE_PATH, "r") as ss:
        app.setStyleSheet(ss.read())

    if not os.path.exists(constants.GENERATED_FILES):
        os.makedirs(constants.GENERATED_FILES)

    window = MyWindow()
    splash.close()

    window.setWindowIcon(QIcon(constants.ICON_PATH))
    window.setWindowTitle("V-Plot")
    window.showMaximized()

    sys.exit(app.exec_())
