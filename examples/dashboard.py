import logging
from multiprocessing import Process
import time
import sys

import torch

from durin import *

from PySide6.QtCore import Qt

from PySide6.QtGui import QImage

from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QPushButton, QWidget

logging.getLogger().setLevel(logging.DEBUG)


ip = "172.16.222.94"


app = QApplication()

widget = QWidget()
vertical = QVBoxLayout(widget)

label = QLabel(f"Durin at {ip}", alignment=Qt.AlignCenter)
vertical.addWidget(label)

close_button = QPushButton(text="Close")
close_button.clicked.connect(app.closeAllWindows)
vertical.addWidget(close_button)



widget.show()

gui_thread = Process(target=app.exec)
gui_thread.start()

time.sleep(2)

# while True:
#     label.setText("Hello")

#     try:
#         time.sleep(0.1)
#     except KeyboardInterrupt:
#         pass

# with Durin("172.16.222.94") as durin:
#     while True:
#         (obs, dvs) = durin.sense()

#         print("OBS: ", dvs.sum(), obs.imu.mean())

#         time.sleep(0.5)

gui_thread.terminate()