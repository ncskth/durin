import logging
from queue import Empty
import time

from durin.actuator import *
from durin.durin import *

from inputs import get_gamepad

logging.getLogger().setLevel(logging.DEBUG)


event_queue = multiprocessing.Queue(maxsize=1)


def norm(x):
    MIN = 21
    MAX = 232
    ABS = MAX - MIN
    MID = ABS / 2
    if x == 0:
        return x
    else:
        return ((x - MID - MIN) / ABS) * 1000


def read_gamepad(queue):
    x = 0
    y = 0
    r = 0

    while True:
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
        queue.put((norm(x), norm(y), norm(r)))


pad_thread = multiprocessing.Process(target=read_gamepad, args=(event_queue,))

with Durin("172.16.223.92", sensor_frequency=1000) as durin:
    try:
        pad_thread.start()
        x = y = r = 0
        while True:
            # (obs, dvs) = durin.read()
            try:
                x, y, r = event_queue.get(timeout=0.05)
            except Empty:
                pass
            print(f"Moving x {x} y {y} r {r}")
            durin(Move(x, y, r))
            time.sleep(0.01)
    finally:
        pad_thread.terminate()
        pad_thread.join()
