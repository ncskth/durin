import time

from durin import *

if __name__ == "__main__":

    # We start a connection to the robot
    # and can now read from and write to the robot via the variable "durin"
    #with Durin("durin5.local", enable_dvs=True) as durin:
    with Durin("durin0.local") as durin:

        # Loop forever
        while True:

            # Read a value from durin
            # - obs = Robot sensor observations
            # - dvs = Robot DVS data (if any)
            # - cmd = Robot responses to commands
            # (obs, dvs, cmd) = durin.read()
            # if dvs is not None:
            #     print(dvs.sum())

            # Move following a square-shaped trajectory
            durin(Move(100, 0, 0))
            time.sleep(1)
            durin(Move(0, 100, 0))
            time.sleep(1)
            durin(Move(-100, 0, 0))
            time.sleep(1)
            durin(Move(0, -100, 0))
            time.sleep(1)
