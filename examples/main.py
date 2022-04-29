import logging
import time
from durin.actuator import *
from durin.common import SENSORS

from durin.durin import Durin
from durin.visuals import launch_visual


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)

    with Durin("172.16.222.92", "172.16.223.244") as durin:
        # This starts the visualization of ToF sensor data
        # p_visual, px = launch_visual()
        # p_visual.start()

        while True:
            (obs, dvs) = durin.sense()
            # if len(px) > 0:
            #     px = obs.imu

            # durin(PollSensor(SENSORS["misc"]))
            print("OBS: ", dvs.sum(), obs.imu.mean())

            time.sleep(0.1)
