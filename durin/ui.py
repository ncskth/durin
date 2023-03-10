import math
import time

import sdl2.ext

import numpy as np
from durin.actuator import Move

from durin.durin import Durin
from durin.io.gamepad import Gamepad

TOF_WIDTH = 8  # 8*8
TOF_HEIGHT = 8

DVS_HEIGHT = 480
DVS_WIDTH = 640

import numpy as np

# test

SENSOR_PLACEMENTS = [
    (0.97, 0.5),
    (0.97, 0.03),
    (0.5, 0.03),
    (0.97, 0.97),
    (0.5, 0.97),
    (0.02, 0.97),
    (0.03, 0.03),
    (0.02, 0.5),
]

MAX_WHEEL = 600


def to_rgba(value):
    alpha = 255
    red = green = blue = value
    return (alpha << 24) | (red << 16) | (green << 8) | blue


def tof_sensor_to_pixels(matrix, size: int = 128):
    pixels = np.empty((size, size))
    width = math.ceil(size / len(matrix))
    for idr, row in enumerate(matrix):
        for idx, element in enumerate(row):
            pixels[
                idr * width : (idr + 1) * width, idx * width : (idx + 1) * width
            ] = to_rgba(element)
    return pixels.T


class DurinUI(Durin):
    """
    **Graphical** Interface to the Durin robot (as opposed to the native durin.Durin class).
    Note that the evaluation may be slower than the native class, due to graphics and user I/O overheads.

    Example:

    >>> with DurinUI(10.0.0.1) as durin:
    >>>   while True:
    >>>     data, dvs, cmd = durin.read()
    >>>     durin.render_sensors(data)
    >>>     durin.read_user_input()
    >>>     durin(Move(x, y, rot))

    Arguments:
        durin_ip (str): The IPv4 address of the Durin microcontroller
        device (str): The PyTorch device to use for storing tensors. Defaults to cpu
        stream_command (Optional[StreamOn]): The command sent to the Durin microcontroller upon start. Can be customized, but uses sensible values by default.
        sensor_frequency (int): The update frequency of the sensor information in ms. Defaults to 15ms.
        disable_dvs (bool): Disables connection to DVS. Useful if necessary libraries are not installed. Defaults to False.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resources = sdl2.ext.Resources(__file__)
        self.gamepad = Gamepad()

        self.vertical = 0
        self.horizontal = 0
        self.tau = 0.9999
        self.rot = 0

    def __enter__(self):
        sdl2.ext.init()

        self.window = sdl2.ext.Window("Durin Dashboard", size=(1000, 900))
        self.window.show()

        factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
        bg = factory.from_image(self.resources.get_path("durin_birdseye.jpg"))
        renderer = factory.create_sprite_render_system(self.window)
        renderer.render(bg)

        self.pixels = sdl2.ext.pixelaccess.pixels2d(renderer)
        self.matrix = np.random.randint(255, size=(8, 8))

        self.gamepad.start()
        return super().__enter__()

    def __exit__(self, e, b, t):
        self.window.close()
        self.gamepad.stop()
        return super().__exit__(e, b, t)

    def read_user_input(self, allow_movement: bool = True, sleep_interval: float=0.02):
        """
        Reads user input and sends commands to Durin based on the input

        Arguments:
            allow_movement (bool): Whether to send (True) or withold (False) commands to Durin
            sleep_interval (float): A pause between reading user input (seconds). Deaults to 0.02. May be 0.
        """
        events = sdl2.ext.get_events()

        # Gamepad
        if not self.gamepad.queue.empty():
            x, y, r = self.gamepad.queue.get()
            self.horizontal = x
            self.vertical = y
            self.rot = r

        # Keyboard
        for event in events:
            if event.type == sdl2.SDL_QUIT or (
                event.type == sdl2.SDL_KEYDOWN
                and event.key.keysym.sym == sdl2.SDLK_ESCAPE
            ):
                return False
            elif event.type == sdl2.SDL_KEYDOWN:
                if (
                    event.key.keysym.sym == sdl2.SDLK_UP
                    or event.key.keysym.sym == sdl2.SDLK_w
                ):
                    self.vertical = 500
                elif (
                    event.key.keysym.sym == sdl2.SDLK_LEFT
                    or event.key.keysym.sym == sdl2.SDLK_a
                ):  # Left
                    self.horizontal = -500
                elif (
                    event.key.keysym.sym == sdl2.SDLK_RIGHT
                    or event.key.keysym.sym == sdl2.SDLK_d
                ):  # Right
                    self.horizontal = 500
                elif (
                    event.key.keysym.sym == sdl2.SDLK_DOWN
                    or event.key.keysym.sym == sdl2.SDLK_s
                ):
                    self.vertical = -500

                if event.key.keysym.sym == sdl2.SDLK_BACKSPACE:
                    self.horizontal = 0
                    self.vertical = 0
            elif event.type == sdl2.SDL_KEYUP:
                if (
                    event.key.keysym.sym == sdl2.SDLK_UP
                    or event.key.keysym.sym == sdl2.SDLK_w
                    or event.key.keysym.sym == sdl2.SDLK_DOWN
                    or event.key.keysym.sym == sdl2.SDLK_s
                ):
                    self.vertical = 0
                elif (
                    event.key.keysym.sym == sdl2.SDLK_LEFT
                    or event.key.keysym.sym == sdl2.SDLK_a
                    or event.key.keysym.sym == sdl2.SDLK_RIGHT
                    or event.key.keysym.sym == sdl2.SDLK_d
                ):
                    self.horizontal = 0
            # elif event.type == sdl2.SDL_MOUSEMOTION:
            #     self.rot = int(self.rot + min(10, max(-10, event.motion.xrel)) * 2)

        if allow_movement:
            self(Move(self.horizontal, self.vertical, self.rot))

        time.sleep(sleep_interval) # Sleep to avoid sending too many commands

        return True

    def render_sensors(self, obs, size: int = 180):
        tofs = (np.tanh((obs.tof / 1000)) * 255).astype(np.int32)
        # tofs = np.cosh((obs.tof / 100) * 255).astype(np.int32)
        width, height = self.pixels.shape
        for idt, tof in enumerate(tofs):
            xr, yr = SENSOR_PLACEMENTS[idt]
            x = int((xr * (width - size)))
            y = int((yr * (height - size)))
            self.pixels[x : x + size, y : y + size] = tof_sensor_to_pixels(tof, size)

        self.window.refresh()
