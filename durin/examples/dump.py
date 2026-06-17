"""Minimal reader that prints raw observations from a Durin robot."""

import pygame
import time

pygame.init()
pygame.joystick.init()

js = pygame.joystick.Joystick(0)
js.init()

while True:
    pygame.event.pump()
    print([js.get_axis(i) for i in range(js.get_numaxes())])
    time.sleep(0.1)
