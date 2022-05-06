import logging
from queue import Empty
import time

from durin.actuator import *
from durin.durin import *
from durin.joystick import Gamepad


logging.getLogger().setLevel(logging.DEBUG)


with Durin("172.16.223.95") as durin:
    with Gamepad() as gamepad:
        x = y = r = 0
        while True:
            # (obs, dvs) = durin.read()
            output = gamepad.read()
            if output is not None:
                x, y, r = output
                print(f"Moving x {x} y {y} r {r}")
                durin(Move(x, y, r))
            time.sleep(0.01)
