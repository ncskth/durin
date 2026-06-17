"""
This is the code for obstacle avoidance with the gamepad.
It doesn't have the option to take the obstacle out. If you don't want obstacle avoidance use gamepad.py instead or if you want to be able to 
handle during the simulation the activation and the deactivation of this algorithm try gamepad_with_avoidance.py.
"""

from durin import DurinUI, SetSensorPeriod, GetSystemInfo
import time
import threading
import sys
import warnings
import numpy as np
from collections import deque
from durin.io.command import Move
import pygame
from controller import TurnigyController # you should use from .controller import TurnigyController if you want to run this on windows

start = 0
window_size = 5 
recent_readings = []  
history = deque(maxlen=5)
delta = 150 
gamma = 0.9  
epsilon = 50  
max_distance = 300 

MAX_FWD = 300
MAX_SIDE = 300
MAX_ROT = 90

SENSORS_FRONT = {7, 0, 1}
SENSORS_LEFT = {1, 2, 3}
SENSORS_BACK = {3, 4, 5}
SENSORS_RIGHT = {5, 6, 7}

def mark_blocked_direction(sensor_idx, blocked_dirs):
    if sensor_idx in SENSORS_FRONT:
        blocked_dirs["front"] = True  
    if sensor_idx in SENSORS_LEFT:
        blocked_dirs["left"] = True
    if sensor_idx in SENSORS_BACK:
        blocked_dirs["back"] = True 
    if sensor_idx in SENSORS_RIGHT:
        blocked_dirs["right"] = True

    return blocked_dirs


def calibration(obs, calibration_readings, floor_matrices, start):
    valid_reading = np.copy(obs.tof)
    invalid_pixels = obs.tof_status > 1
    valid_reading[invalid_pixels] = np.nan
    calibration_readings.append(valid_reading)

    if start == 99:
        calibration_array = np.array(calibration_readings)
        valid_counts = np.sum(~np.isnan(calibration_array), axis=0)

        min_valid = 70
        unreliable_mask = valid_counts < min_valid

        floor_matrices = np.full(valid_counts.shape, np.nan, dtype=np.float64)
        valid_any = valid_counts > 0
        if np.any(valid_any):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                median_all = np.nanmedian(calibration_array, axis=0)
            floor_matrices[valid_any] = median_all[valid_any]
        floor_matrices[unreliable_mask] = np.nan

        for sensor_idx in range(8):
            for line in range(8):
                for col in range(8):
                    if np.isnan(floor_matrices[sensor_idx][line][col]):
                        neighbors = []
                        if line > 0 and not np.isnan(floor_matrices[sensor_idx][line - 1][col]):
                            neighbors.append(floor_matrices[sensor_idx][line - 1][col])
                        if line < 7 and not np.isnan(floor_matrices[sensor_idx][line + 1][col]):
                            neighbors.append(floor_matrices[sensor_idx][line + 1][col])
                        if col > 0 and not np.isnan(floor_matrices[sensor_idx][line][col - 1]):
                            neighbors.append(floor_matrices[sensor_idx][line][col - 1])
                        if col < 7 and not np.isnan(floor_matrices[sensor_idx][line][col + 1]):
                            neighbors.append(floor_matrices[sensor_idx][line][col + 1])
                        if neighbors:
                            floor_matrices[sensor_idx][line][col] = np.mean(neighbors)

        num_problems = np.sum(np.isnan(floor_matrices))
        if num_problems > 0:
            pass
    return floor_matrices   

def obstacleDetection(obs, floor_matrices, history, start):
    blocked_dirs = {
        "front": False,
        "left": False,
        "back": False,
        "right": False,
    }
    current_reading = obs.tof  
    recent_readings.append(current_reading)

    if len(recent_readings) > window_size:
        recent_readings.pop(0)

        history.append(current_reading)
        if len(history) > history.maxlen:
            history.popleft()

        if start >= 100 and floor_matrices is not None:
                alpha = 0.99
                floor_matrices = alpha * floor_matrices + (1 - alpha) * current_reading

        if start >= 100 and floor_matrices is not None:
            if len(history) >= 2:
                hist_arr = np.stack(history)
                M = np.min(hist_arr, axis=0)
                prev = history[-2]
                with np.errstate(divide='ignore', invalid='ignore'):
                    G = np.where(prev > 0, history[-1] / prev, 1.0)
                    G = np.nan_to_num(G, nan=1.0, posinf=1.0, neginf=1.0)
            else:
                M = np.copy(current_reading)
                G = np.ones_like(current_reading)

            for sensor_idx in range(8):
                for line in range(8):
                    for colum in range(8):
                        if obs.tof_status[sensor_idx][line][colum] <= 1 and floor_matrices[sensor_idx][line][colum] > 0 and not np.isnan(floor_matrices[sensor_idx][line][colum]):
                            R = current_reading[sensor_idx][line][colum]
                            cond1 = (R < floor_matrices[sensor_idx][line][colum] - delta) and (R < M[sensor_idx][line][colum] + epsilon)
                            cond2 = G[sensor_idx][line][colum] < gamma
                            if cond1 or cond2:
                                neighbors = []
                                if colum != 0:
                                    neighbors.append(floor_matrices[sensor_idx][line][colum - 1] - obs.tof[sensor_idx][line][colum - 1])
                                if colum != 7:
                                    neighbors.append(floor_matrices[sensor_idx][line][colum + 1] - obs.tof[sensor_idx][line][colum + 1])
                                if line != 0:
                                    neighbors.append(floor_matrices[sensor_idx][line - 1][colum] - obs.tof[sensor_idx][line - 1][colum])
                                if line != 7:
                                    neighbors.append(floor_matrices[sensor_idx][line + 1][colum] - obs.tof[sensor_idx][line + 1][colum])
                                confirmed_neighbors = sum(1 for n in neighbors if n > 100)
                                if confirmed_neighbors >= 4:
                                    obstacle_distance = R
                                    if obstacle_distance <= max_distance:
                                        blocked_dirs = mark_blocked_direction(sensor_idx, blocked_dirs)
                                        print(obstacle_distance)
                                        print(f"obstacle detected with a distance of {obstacle_distance:.1f} mm by sensor {sensor_idx} line {line} column {colum}")
    return blocked_dirs

if __name__ == "__main__":

    with DurinUI("durin25.local") as durin:
        is_running = True
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
                durin.set_ip_mac_id(ip,mac,id)
                gotSystemInfo = True

            except:
                pass
        
        calibration_readings = []  
        floor_matrices = None

        controller = TurnigyController()
        controller.open()

        thread = threading.Thread(target=controller.read_loop, daemon=True)
        thread.start()

        try:
            while is_running:

                (obs, dvs, cmd) = durin.read()
                if start < 100:
                    floor_matrices = calibration(obs, calibration_readings, floor_matrices, start)
                elif start == 100:
                    print("Calibration complete. Starting obstacle detection.")
                start += 1

                vel_x = int(controller.get_forward() * MAX_FWD)
                vel_y = int(controller.get_side() * MAX_SIDE)
                rot = int(controller.get_rotation() * MAX_ROT)
                blocked_dirs = obstacleDetection(obs, floor_matrices, history, start)

                if blocked_dirs["left"] and vel_x > 0:
                    vel_x = 0
                if blocked_dirs["right"] and vel_x < 0:
                    vel_x = 0
                if blocked_dirs["front"] and vel_y > 0:
                    vel_y = 0
                if blocked_dirs["back"] and vel_y < 0:
                    vel_y = 0

                durin(Move(vel_x, vel_y, rot))

                durin.render_sensors(obs)
                is_running = durin.read_user_input(allow_movement=False)

                time.sleep(0.02)
        finally:
            controller.close()

    