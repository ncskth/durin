from durin import Durin, DurinUI, Move 
import time
import sys
import numpy as np

save = True

time_steps = 10000
N_sensor_values = 9 + 3 + 1 + 2         # imu + position + voltage + one beacon (ID + distance)
all_stats = np.zeros((time_steps, N_sensor_values), dtype = object)
headers = ["Acce x","Acce y","Acce z","Gyro x","Gyro y","Gyro z","Magn x","Magn y","Magn z","Position x","Position y","Position z","Voltage","UWB ID","UWB distande"]
header=','.join(headers)
print(header)

if __name__ == "__main__":
    i = 0

    with Durin("durin1.local") as durin:

        while i < time_steps:
            (obs, dvs, cmd) = durin.read()

            if obs.voltage == 0:
                # In the "boot" process, all values are 0 in a number of while-iterations.
                # We do not want to include the 0-values
                continue
            
            print(i, "/", time_steps)
            
            # Collect all relevant sensor data
            imu_values = obs.imu.reshape((9,))
            position = obs.position.reshape((3,))
            voltage = np.array([obs.voltage]).reshape((1,))
            uwb = np.array([obs.uwb[0]]).reshape((2,))
            sensor_values = np.concatenate([imu_values, position, voltage, uwb])

            # Add sensor values to the all_stats array
            for sensor_idx, sensor_value in enumerate(sensor_values):
                all_stats[(i), sensor_idx] = sensor_value

            durin(Move(0,0,0))  # So that Durin does not sleep
            i += 1


    
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
                            ["UWB ID mean", "UWB ID variance"],
                            ["UWB distande mean", "UWB distande variance"])
    

    for j in range(len(statistic_quantities)):
        print(statistic_quantities[j][0], np.mean(all_stats[:,j]), statistic_quantities[j][1], np.var(all_stats[:,j]))

if save:
    # Save as a csv file
    np.savetxt('sensor statistics/stats.csv',all_stats,delimiter=',',header=','.join(headers), fmt='%d')




