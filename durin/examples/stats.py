from durin import Durin
import time
import sys
import numpy as np

time_steps = 10000
N_sensor_values = 9 + 3 + 1 + 1         # imu + position + voltage + one beacon
all_stats = np.zeros((time_steps, N_sensor_values), dtype = int)

if __name__ == "__main__":
    
    with Durin("durin0.local") as durin:

        for i in range(time_steps):
            (obs, dvs, cmd) = durin.read()
            
            # Collect all relevant sensor data
            imu_values = [obs.imu[i] for i in range(9)]
            position = [obs.position[i] for i in range(3)]
            sensor_values = imu_values + position + obs.voltage + obs.uwb[0]
            print(sensor_values)

            # Add sensor values to the all_stats array
            for sensor_idx, sensor_value in enumerate(sensor_values):
                all_stats[sensor_idx, i] = sensor_value


    
    # Caluculate statistics
    statistic_quantities = (["Acce x mean", "Acce x variance"],
                            ["Acce y mean", "Acce y variance"],
                            ["Acce z mean", "Acce z variance"],
                            ["Gyro x mean", "Gyro x variance"],
                            ["Gyro y mean", "Gyro y variance"],
                            ["Gyro z mean", "Gyro z variance"],
                            ["Magn x mean", "Magn x variance"],
                            ["Magn y mean", "Magn y variance"],
                            ["Magn z mean", "Magn z variance"],
                            ["Position x mean", "Position x variance"],
                            ["Position y mean", "Position y variance"],
                            ["Position z mean", "Position z variance"],
                            ["Voltage mean", "Voltage variance"],
                            ["UWB mean", "UWB variance"])

    for j in range(len(statistic_quantities)):
        print(statistic_quantities[j][0], np.mean(all_stats[j]), statistic_quantities[j][1], np.var(all_stats[j]))






