import os
import sys
import time

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")

from image_processing.stippling import Stippling

from PIL import Image
from rembg import new_session, remove

class Test:
    def __init__(self):
        self.pil_image = Image.open(r"C:\Users\tvten\Desktop\TS_NO_BG.png")

    def scale(self) -> None:
        self.pil_image = self.pil_image.resize((int(self.pil_image.width/2), int(self.pil_image.height/2)))

    def test_rembg(self, image: Image) -> None:
        if image is None:
            return
        session = new_session("u2net_lite", providers=["CPUExecutionProvider"])

        try:
            start_time = time.time()
            image = remove(image, session=session)
            #image = remove(image)

            end_time = time.time()
            exec_time = end_time - start_time
            print(f"Finishd in {exec_time}")
        except Exception as e:
            print("❌ Error occurred in rembg:", e)

        jpg_image = Image.new("RGB", image.size, "white")
        jpg_image.paste(image, (0, 0))
        image = jpg_image
        image.show()

    def test_stippling(self) -> None:
        stippling = Stippling(self.pil_image)
        assert stippling.eucDist(0,0,3,4) == 5.0

        stippling.stipple()


test = Test()
test.scale()
test.test_stippling()
#test.test_rembg(test.pil_image)
