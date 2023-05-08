from durin import DurinUI, SetSensorPeriod, GetSystemInfo
import time
import sys


if __name__ == "__main__":

    # We start a connectioen to the robot
    # and can now read from and write to the robot via the variable "durin"
    # Notice the UI class, which differs from the (more efficient) standalone Durin interface
    # the debug flag enables/disables some ugly data on the dashboard
    if len(sys.argv) == 2:
        debug = (sys.argv[1] == "debug")
    else:
        debug = False

    with DurinUI("durin1.local", debug=debug) as durin:
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

            time.sleep(0.02)

