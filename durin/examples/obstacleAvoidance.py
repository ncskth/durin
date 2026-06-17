"""Gamepad control example with sensor-based obstacle avoidance enabled."""

from durin import DurinUI, SetSensorPeriod, GetSystemInfo
import time
import sys
import numpy as np
from collections import deque
start = 0
window_size = 5 
recent_readings = []  
# sliding history for dynamic detection
history = deque(maxlen=5)

if __name__ == "__main__":

    # We start a connectioen to the robot
    # and can now read from and write to the robot via the variable "durin"
    # Notice the UI class, which differs from the (more efficient) standalone Durin interface
    with DurinUI("durin13.local") as durin:
    #with DurinUI("172.16.222.124") as durin:
        # Loop until the user quits
        is_running = True
        durin(GetSystemInfo())  # Ask to get IP address, MAC address and Durin ID
        gotSystemInfo = False


        while not gotSystemInfo:
            """ Wait until IP address, MAC address, and Durin ID are read"""
            try:
                (obs, dvs, cmd) = durin.read()
                ip = cmd.systemInfo.ip
                mac = cmd.systemInfo.mac
                id = cmd.systemInfo.id
                durin.set_ip_mac_id(ip,mac,id)
                gotSystemInfo = True

            except:
                pass
        
        # this function is only for the beginning of the program, you could also save 
        # the references number on the computer and load them at the beginning of the program, 
        # but I wanted to have a function that automatically saves the reference matrices for each sensor
        
        calibration_readings = []  # Store readings for baseline calculation (all 8 sensors)
        floor_matrices = None  # Initialize baseline matrices (8x8x8)

        while is_running:
            """
            OBSTACLE DETECTION ALGORITHM:
            1. Calibration (frames 0-99): Build baseline matrices from all 8 sensors,
               filtering out unreliable pixels (< 70 valid readings).
            2. Baseline Update (frames 100+): Maintain slowly-updated baseline (alpha=0.99)
               to adapt to long-term environmental changes.
            3. Dynamic History: Track short-term minima and frame-to-frame ratios to
               detect both static deviations and rapid approach events.
            4. Detection Rules: Flag pixels where (distance < baseline - delta) AND
               (distance < recent_minimum + epsilon) OR (ratio < gamma indicating rapid change).
            5. Neighbor Validation: Confirm detections only if ≥4 neighbors also detect
               the obstacle (spatial consistency).
            6. Distance Filter: Report only obstacles within max_distance (50 cm default).
            """

            # Read sensor data from the robot
            # - obs = Robot sensor observations - sensor outputs
            # - dvs = Robot DVS data (if any) - not working
            # - cmd = Robot responses to commands
        
            (obs, dvs, cmd) = durin.read()
            if start < 100:  # Calibration phase
                # Store all 8 sensor matrices
                valid_reading = np.copy(obs.tof)  # All 8 sensors
                # Mark invalid pixels as NaN (where status > 1)
                for sensor_idx in range(8):
                    invalid_pixels = obs.tof_status[sensor_idx] > 1
                    valid_reading[sensor_idx][invalid_pixels] = np.nan
                calibration_readings.append(valid_reading)
                
                # Debug: print how many valid readings each pixel got
                if start == 99:
                    valid_counts = np.sum(~np.isnan(np.array(calibration_readings)), axis=0)
                    print(f"Valid reading counts per pixel (all 8 sensors):\n{valid_counts}")
                
                # Once calibration is done, calculate baseline using only valid readings
                if start == 99:
                    calibration_array = np.array(calibration_readings)
                    # count validity per sensor
                    valid_counts = np.sum(~np.isnan(calibration_array), axis=0)
                    # any pixel with <70 valid readings is treated as unreliable
                    min_valid = 70
                    unreliable_mask = valid_counts < min_valid
                    unreliable_per_sensor = np.sum(unreliable_mask, axis=(1, 2))
                    for s in range(8):
                        if unreliable_per_sensor[s] > 0:
                            print(f"  Sensor {s}: {unreliable_per_sensor[s]} unreliable pixels")
                    
                    # Use nanmedian to ignore NaN values (invalid pixels)
                    floor_matrices = np.nanmedian(calibration_array, axis=0)
                    # mask out unreliable pixels
                    floor_matrices[unreliable_mask] = np.nan
                    
                    # Fill missing values (NaN) with average of neighbors for each sensor
                    for sensor_idx in range(8):
                        for line in range(8):
                            for col in range(8):
                                if np.isnan(floor_matrices[sensor_idx][line][col]):
                                    neighbors = []
                                    # Collect valid neighbors
                                    if line > 0 and not np.isnan(floor_matrices[sensor_idx][line-1][col]):
                                        neighbors.append(floor_matrices[sensor_idx][line-1][col])
                                    if line < 7 and not np.isnan(floor_matrices[sensor_idx][line+1][col]):
                                        neighbors.append(floor_matrices[sensor_idx][line+1][col])
                                    if col > 0 and not np.isnan(floor_matrices[sensor_idx][line][col-1]):
                                        neighbors.append(floor_matrices[sensor_idx][line][col-1])
                                    if col < 7 and not np.isnan(floor_matrices[sensor_idx][line][col+1]):
                                        neighbors.append(floor_matrices[sensor_idx][line][col+1])
                                    # Fill with average of neighbors if available
                                    if neighbors:
                                        floor_matrices[sensor_idx][line][col] = np.mean(neighbors)
                    
                    # re-count problems after fill
                    num_problems = np.sum(np.isnan(floor_matrices))
                    if num_problems > 0:
                        print(f"Remaining {num_problems} baseline pixels are NaN after interpolation")
                    
                    print("Calibration complete. Baseline matrices (all 8 sensors):")
                    for s in range(8):
                        print(f"\nSensor {s}:")
                        print(floor_matrices[s])

            start += 1
            #print(start)

            # Store readings from all 8 sensors
            current_reading = obs.tof  # All 8 sensor matrices
            recent_readings.append(current_reading)

            # Keep only the last 'window_size' readings (for temporal noise filtering)
            if len(recent_readings) > window_size:
                recent_readings.pop(0)

            # Calculate the average of the readings (used for current distance)
            average_reading = np.mean(recent_readings, axis=0)

            # Dynamic update: history of recent frames
            history.append(current_reading)
            if len(history) > history.maxlen:
                history.popleft()

            # Slowly update baseline after calibration (all 8 sensors)
            if start >= 100 and floor_matrices is not None:
                alpha = 0.99
                floor_matrices = alpha * floor_matrices + (1 - alpha) * current_reading

            # Only start detecting obstacles after calibration is complete
            if start >= 100 and floor_matrices is not None:
                # compute short–term minimum and frame‑to‑frame ratio (all sensors)
                if len(history) >= 2:
                    hist_arr = np.stack(history)
                    M = np.min(hist_arr, axis=0)
                    prev = history[-2]
                    # safe ratio with zeros
                    with np.errstate(divide='ignore', invalid='ignore'):
                        G = np.where(prev > 0, history[-1] / prev, 1.0)
                        G = np.nan_to_num(G, nan=1.0, posinf=1.0, neginf=1.0)
                else:
                    M = np.copy(current_reading)
                    G = np.ones_like(current_reading)

                # debug initial snapshot
                if start == 100:
                    print("\n=== DEBUG INFO ===")
                    print("Baseline matrices (floor_matrices) - first sensor as example:")
                    print(floor_matrices[0])
                    print("\nCurrent reading (obs.tof[0]):")
                    print(obs.tof[0])
                    print("=" * 40 + "\n")

                # parameter thresholds
                delta = 150  # distance diff threshold
                gamma = 0.9  # rapid-change ratio
                epsilon = 50  # slack for min-history
                max_distance = 500  # Maximum distance to report (50 cm in mm)

                # Process all 8 sensors
                for sensor_idx in range(8):
                    for line in range(8):
                        for colum in range(8):
                            if obs.tof_status[sensor_idx][line][colum] <= 1 and floor_matrices[sensor_idx][line][colum] > 0 and not np.isnan(floor_matrices[sensor_idx][line][colum]):
                                # R is the copy for pixel and M is the copy of everything
                                R = current_reading[sensor_idx][line][colum]
                                # detection rules
                                # control if the current reading is at least 150mm closer than the baseline (free floor reference)
                                # AND if the current reading is at least 50mm closer than the recent minimum (dynamic history reference),
                                cond1 = (R < floor_matrices[sensor_idx][line][colum] - delta) and (R < M[sensor_idx][line][colum] + epsilon)
                                # OR if the current reading has rapidly decreased compared to the previous frame (ratio < gamma) -> catch fast moving obstacles
                                cond2 = G[sensor_idx][line][colum] < gamma
                                if cond1 or cond2:
                                    # verify neighbors
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
                                            print(obstacle_distance)
                                            print(f"obstacle detected with a distance of {obstacle_distance:.1f} mm by sensor {sensor_idx} line {line} column {colum}")

            # We can now update our display with the observations
            durin.render_sensors(obs) # create ui

            # Read user input and quit, if asked
            is_running = durin.read_user_input()

            time.sleep(0.02)

    