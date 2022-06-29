import logging

from durin.actuator import *
from durin.durin import *

logging.getLogger().setLevel(logging.DEBUG)

with Durin("172.16.234.XX", disable_dvs=True) as durin:

    while True:
        
        # Move following a square-shaped trajectory
        durin(Move(100,0,0))
        time.sleep(1)
        durin(Move(0,100,0))
        time.sleep(1)
        durin(Move(-100,0,0))
        time.sleep(1)
        durin(Move(0,-100,0))
        time.sleep(1)