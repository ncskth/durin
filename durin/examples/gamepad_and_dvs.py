"""Combines gamepad control with DVS streaming and visualization."""

import argparse
import os
import sys
import threading
import time

import aestream
import cv2
import numpy as np

# Allow running this file directly from source without installing the package.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from controller import TurnigyController
from durin import DurinUI, GetSystemInfo
from durin.io.command import Move

MAX_FWD = 300
MAX_SIDE = 300
MAX_ROT = 90


def dvs_loop(port, stop_event, win_name):
    with aestream.UDPInput((640, 480), device="cpu", port=port) as stream:
        while not stop_event.is_set():
            frame = stream.read()
            frame_viz = np.zeros((frame.shape[0], frame.shape[1], 3), dtype=frame.dtype)
            frame_viz[:, :, 1] = frame
            image = frame_viz.transpose(1, 0, 2)
            cv2.imshow(win_name, image)
            if cv2.waitKey(1) & 0xFF == 27:
                stop_event.set()
                break


def parse_args():
    parser = argparse.ArgumentParser(description="Run gamepad control and DVS visualization together")
    parser.add_argument("-d", "--durin", default="durin13.local", help="Durin hostname or IP")
    parser.add_argument("-p", "--port", type=int, default=4001, help="DVS UDP port")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    win_name = "Durin DVS"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    stop_event = threading.Event()

    dvs_thread = threading.Thread(target=dvs_loop, args=(args.port, stop_event, win_name), daemon=True)
    dvs_thread.start()

    with DurinUI(args.durin) as durin:
        is_running = True

        durin(GetSystemInfo())
        gotSystemInfo = False
        while not gotSystemInfo:
            try:
                (obs, dvs, cmd) = durin.read()
                ip = cmd.systemInfo.ip
                mac = cmd.systemInfo.mac
                robot_id = cmd.systemInfo.id
                durin.set_ip_mac_id(ip, mac, robot_id)
                print(f"SystemInfo -> id={robot_id}, ip={ip}, mac={mac}")
                gotSystemInfo = True
            except Exception:
                pass

        controller = TurnigyController()
        controller.open()
        thread = threading.Thread(target=controller.read_loop, daemon=True)
        thread.start()

        try:
            while is_running and not stop_event.is_set():
                (obs, dvs, cmd) = durin.read()

                vel_x = int(controller.get_forward() * MAX_FWD)
                vel_y = int(controller.get_side() * MAX_SIDE)
                rot = int(controller.get_rotation() * MAX_ROT)

                durin(Move(vel_x, vel_y, rot))

                durin.render_sensors(obs)
                is_running = durin.read_user_input(allow_movement=False)

                time.sleep(0.02)
        finally:
            stop_event.set()
            controller.close()
            cv2.destroyAllWindows()
