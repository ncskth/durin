import logging

from durin.actuator import *
from durin.durin import *

logging.getLogger().setLevel(logging.DEBUG)

with Durin("172.16.223.95") as durin:

    while True:
        (obs, dvs, cmd) = durin.read()

        # ...
        
        # print("OBS: ", dvs.sum(), obs.imu.mean())

        time.sleep(0.5)