import logging

from durin.actuator import *
from durin.durin import *

import pdb

logging.getLogger().setLevel(logging.DEBUG)


# p_visual, dvs_np = launch_visual()
# p_visual.start()

with Durin("172.16.223.91") as durin:

    while True:
        (obs, dvs) = durin.read()
        pdb.set_trace()

        # ...
        
        print("OBS: ", dvs.sum(), obs.imu.mean())

# p_visual.join()