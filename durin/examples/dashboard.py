from durin import *


if __name__ == "__main__":

    # We start a connection to the robot
    # and can now read from and write to the robot via the variable "durin"
    # Notice the UI class, which differs from the (more efficient) standalone Durin interface
    with DurinUI("durin1.local") as durin:
        # Loop until the user quits
        is_running = True

        sensor_frequencies = (["Tof", 1000],
                              ["Imu", 1000],
                              ["Position", 1000],
                              ["SystemStatus", 1000],
                              ["Uwb", 1000],
                              )

        for sensor in sensor_frequencies:
            durin(SetSensorPeriod(sensor[0],sensor[1]))

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
