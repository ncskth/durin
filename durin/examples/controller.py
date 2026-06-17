"""Standalone joystick reader used to debug the gamepad axes."""

import threading
import pygame
import time



class TurnigyController:
    def __init__(self, deadzone=0.1):
        self.deadzone = deadzone
        self.running = False
        self.lock = threading.Lock()
        self.js = None

        self.forward = 0.0
        self.side = 0.0
        self.rotation = 0.0

    def _axes_valid(self, axis0, axis1, axis3):
        return not (axis0 <= -0.99 and axis1 <= -0.99 and axis3 <= -0.99)

    def open(self):
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            raise RuntimeError("No joystick found. Connect and power on the controller.")

        self.js = pygame.joystick.Joystick(0)
        self.js.init()

        print("Joystick:", self.js.get_name())
        print("Assi:", self.js.get_numaxes())

        self.running = True

    def close(self):
        self.running = False
        pygame.quit()

    def read_loop(self):
        while self.running:
            try:
                if not pygame.get_init() or not pygame.joystick.get_init() or self.js is None:
                    with self.lock:
                        self.forward = 0.0
                        self.side = 0.0
                        self.rotation = 0.0
                    time.sleep(0.01)
                    continue

                pygame.event.pump()

                # Right stick
                axis0 = self.js.get_axis(0)
                axis1 = self.js.get_axis(1)
                # Left stick
                axis3 = self.js.get_axis(3)

                if not self._axes_valid(axis0, axis1, axis3):
                    with self.lock:
                        self.forward = 0.0
                        self.side = 0.0
                        self.rotation = 0.0
                    time.sleep(0.01)
                    continue

                with self.lock:
                    self.forward = axis0
                    self.side = axis1
                    self.rotation = -axis3
            except pygame.error:
                with self.lock:
                    self.forward = 0.0
                    self.side = 0.0
                    self.rotation = 0.0
                time.sleep(0.01)
                continue

            time.sleep(0.01)


    def _dz(self, v):
        return 0 if abs(v) < self.deadzone else v

    def get_forward(self):
        with self.lock:
            return self._dz(self.forward)

    def get_side(self):
        with self.lock:
            return self._dz(self.side)

    def get_rotation(self):
        with self.lock:
            return self._dz(self.rotation)