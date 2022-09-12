import multiprocessing

from inputs import get_gamepad, UnpluggedError

from durin.io.runnable import RunnableProducer


JOYSTICK_MIN = 21
JOYSTICK_MAX = 232
JOYSTICK_ABS = JOYSTICK_MAX - JOYSTICK_MIN
JOYSTICK_MID = JOYSTICK_ABS / 2


class Gamepad(RunnableProducer):
    def __init__(self, timeout: float = 0.05):
        context = multiprocessing.get_context("spawn")
        self.queue = context.Queue(maxsize=1)
        self.timeout = timeout
        self.values = multiprocessing.Array("f", 3)
        self.tau = 0.99

        super().__init__(self.queue, self.values)

    @staticmethod
    def norm(x):
        if x == 0:
            return int(x)
        else:
            return int(((x - JOYSTICK_MID - JOYSTICK_MIN) / JOYSTICK_ABS) * 1000)

    def produce(self, values):
        array = values.get_obj()

        # Register gamepad events
        try:
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
        except UnpluggedError:
            pass
        return Gamepad.norm(array[0]), Gamepad.norm(array[1]), Gamepad.norm(array[2])
