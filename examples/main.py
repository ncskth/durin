import logging
import time

from durin import *

logging.getLogger().setLevel(logging.DEBUG)

with Durin("172.16.223.92") as durin:

    while True:
        (obs, dvs) = durin.read()

        #print("OBS: ", dvs.sum(), obs.imu.mean())
        print(durin.update_frequency())
