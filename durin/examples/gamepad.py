"""
This is the code for controlling the robot with a gamepad. It doesn't have the option to take the obstacle out. 
If you don't want obstacle avoidance use gamepad.py instead or if you want to be able to handle during the simulation 
the activation and the deactivation of this algorithm try gamepad_with_avoidance.py.
"""

import threading
import time
import pygame
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from durin import DurinUI, SetSensorPeriod, GetSystemInfo
from controller import TurnigyController
from durin.io.command import Move
#if you want to run this on windows you shouulr use this two import:
    # from .controller import TurnigyController
    # from durin.io.command import Move

MAX_FWD = 300
MAX_SIDE = 300
MAX_ROT = 90



if __name__ == "__main__":
    with DurinUI("durin13.local") as durin:
        is_running = True

        # Setup iniziale - ottieni le info del sistema
        durin(GetSystemInfo())
        gotSystemInfo = False

        while not gotSystemInfo:
            try:
                (obs, dvs, cmd) = durin.read()
                ip = cmd.systemInfo.ip
                mac = cmd.systemInfo.mac
                id = cmd.systemInfo.id
                uptime_ms = cmd.systemInfo.uptimeMs
                firmware_version = getattr(cmd.systemInfo, "firmwareVersion", "<not available>")
                print(f"SystemInfo -> id={id}, ip={ip}, mac={mac}, uptimeMs={uptime_ms}, firmwareVersion={firmware_version}")
                print(f"SystemInfo raw -> {cmd.systemInfo}")
                durin.set_ip_mac_id(ip, mac, id)
                gotSystemInfo = True
            except:
                pass

        controller = TurnigyController()
        controller.open()

        thread = threading.Thread(target=controller.read_loop, daemon=True)
        thread.start()

        # Loop principale - controlla il robot con il gamepad
        try:
            while is_running:
                (obs, dvs, cmd) = durin.read()
                
                vel_x = int(controller.get_forward() * MAX_FWD)
                vel_y = int(controller.get_side() * MAX_SIDE)
                rot   = int(controller.get_rotation() * MAX_ROT)

                #print(vel_x, vel_y, rot)
                durin(Move(vel_x, vel_y, rot))

                # Disegna la dashboard con i dati dei sensori
                durin.render_sensors(obs)
                
                # Legge input da tastiera/gamepad e aggiorna la finestra
                is_running = durin.read_user_input(allow_movement=False)

                time.sleep(0.02)
        finally:
            controller.close()
