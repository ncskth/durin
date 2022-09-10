import multiprocessing
from queue import Empty
from typing import Optional, Tuple


from inputs import get_gamepad

from durin.io.runnable import RunnableProducer


class Gamepad(RunnableProducer):
    def __init__(self, timeout: float = 0.05):
        context = multiprocessing.get_context("spawn")
        self.queue = context.Queue(maxsize=1)
        self.timeout = timeout
        self.values = multiprocessing.Array("i", 3)

        super().__init__(self.queue, self.values)

    @staticmethod
    def norm(x):
        MIN = 21
        MAX = 232
        ABS = MAX - MIN
        MID = ABS / 2
        if x == 0:
            return x
        else:
            return ((x - MID - MIN) / ABS) * 1000

    def produce(self, values):
        array = values.get_obj()

        # Register gamepad events
        events = get_gamepad()
        for event in events:
            stick = event.code
            state = event.state
            if state > 0:
                if "ABS_X" in stick:
                    array[0] = state
                elif "ABS_Y" in stick:
                    array[1] = state
                elif "ABS_RX" in stick:
                    array[2] = state
        return Gamepad.norm(array[0]), Gamepad.norm(array[1]), Gamepad.norm(array[2])
