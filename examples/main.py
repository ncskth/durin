import time
from durin.actuator import *
from durin.common import SENSORS

from durin.durin import Durin
from durin.visuals import launch_visual


if __name__ == "__main__":
    
    with Durin("localhost") as durin:
        # This starts the visualization of ToF sensor data
        p_visual, px_np = launch_visual()
        p_visual.start()

        while True:
            (obs, dvs) = durin.sense()
            if len(px_np) > 0:
                px_np[:,:]= obs.tof


            durin(PollSensor(SENSORS["misc"]))

            time.sleep(0.01)
