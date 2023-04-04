from durin import *
import time
import sys


if __name__ == "__main__":

    # We start a connectioen to the robot
    # and can now read from and write to the robot via the variable "durin"
    # Notice the UI class, which differs from the (more efficient) standalone Durin interface
    with DurinUI("durin1.local") as durin:
        # Loop until the user quits
        is_running = True

        # The sensor frequencies in Hz
        sensor_frequencies = (["Imu", 50],
                              ["Position", 50],
                              ["SystemStatus", 1],
                              ["Uwb", 50],
                              ["Tof", 50],
                              )

        
        for sensor in sensor_frequencies:
            durin(SetSensorPeriod(sensor[0],1000/sensor[1]))    # Frequency (Hz) to period (ms)

        
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


        while is_running:

            # Read a value from durin
            # - obs = Robot sensor observations
            # - dvs = Robot DVS data (if any)
            # - cmd = Robot responses to commands
            (obs, dvs, cmd) = durin.read()

            # We can now update our display with the observations
            durin.render_sensors(obs)

            # Read user input and quit, if asked
            is_running = durin.read_user_input()

            time.sleep(0.005)