import logging
import time

from durin.actuator import *
from durin.durin import *

from inputs import get_gamepad

logging.getLogger().setLevel(logging.DEBUG)

def norm(x):
    MIN = 21
    MAX = 232
    ABS = MAX - MIN
    MID = ABS / 2
    if x == 0:
        return x
    else:
        return ((x - MID - MIN) / ABS) * 500

with Durin("172.16.223.91", sensor_frequency=50) as durin:

    x = 0
    y = 0
    r = 0
    time_sent = time.time()

    while True:
        # (obs, dvs) = durin.read()

        # Register gamepad events
        events = get_gamepad()
        for event in events:
            stick = event.code
            state = event.state
            if state > 0:
                if "ABS_X" in stick:
                    x = state
                elif "ABS_Y" in stick:
                    y = state
                elif "ABS_RX" in stick:
                    r = state

        time_current = time.time()
        if (time_current - time_sent > 0.5):
            print(f"Moving x {norm(x)} y {norm(y)} r {norm(r)}")
            durin(Move(norm(x), norm(y), norm(r)))
            time_sent = time_current
