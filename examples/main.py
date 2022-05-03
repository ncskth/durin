import logging

from durin.actuator import *
from durin.durin import *

logging.getLogger().setLevel(logging.DEBUG)

with Durin("172.16.223.91") as durin:

    while True:
        (obs, dvs) = durin.read()

        # ...
        
        print("OBS: ", dvs.sum(), obs.imu.mean())