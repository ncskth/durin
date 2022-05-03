import logging
from multiprocessing import Process
import time
import sys

import torch

import PySimpleGUI as sg

from durin import *


# from PySide6.QtCore import Qt

# from PySide6.QtGui import QImage

# from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QPushButton, QWidget

logging.getLogger().setLevel(logging.DEBUG)


ip = "172.16.222.94"

# All the stuff inside your window.
layout = [  
    [sg.Text('Durin at {ip}')],
            [sg.Text('Enter something on Row 2'), sg.InputText()],
            [sg.Button('Ok'), sg.Button('Cancel')] ]

# Create the Window
window = sg.Window('Window Title', layout)
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
        break
    print('You entered ', values[0])

window.close()

# # while True:
# #     label.setText("Hello")

# #     try:
# #         time.sleep(0.1)
# #     except KeyboardInterrupt:
# #         pass

# # with Durin("172.16.222.94") as durin:
# #     while True:
# #         (obs, dvs) = durin.sense()

# #         print("OBS: ", dvs.sum(), obs.imu.mean())

# #         time.sleep(0.5)

# gui_thread.terminate()