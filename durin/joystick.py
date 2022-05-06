import multiprocessing
from queue import Empty
from typing import Optional, Tuple


from inputs import get_gamepad


class Gamepad:
    def __init__(self, timeout: float = 0.05):
        self.queue = multiprocessing.Queue(maxsize=1)
        self.timeout = timeout
        self.thread = multiprocessing.Process(
            target=self._read_gamepad, args=(self.queue,)
        )

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

    def read(self) -> Optional[Tuple[int, int, int]]:
        try:
            return self.queue.get(timeout=self.timeout)
        except Empty:
            return None

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, a, b, c):
        self.thread.kill()
        self.thread.terminate()
        self.thread.join()
        return self

    @staticmethod
    def _read_gamepad(queue):
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
            queue.put((Gamepad.norm(x), Gamepad.norm(y), Gamepad.norm(r)))
