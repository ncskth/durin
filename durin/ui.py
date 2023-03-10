import pygame
import math
import os
import random
import sys
import ctypes
import time

import numpy as np
from durin.actuator import Move

from durin.durin import Durin
from durin.io.gamepad import Gamepad


# Constants
surface_width = 200
surface_height = 200
sleep_interval = 0.02

SENSOR_PLACEMENTS = [
    (0.45, 0.4),
    (0.41, 0.03),
    (0.25, 0.02),
    (0.41, 0.7),
    (0.25, 0.78),
    (0.02, 0.7),
    (0.02, 0.03),
    (0.02, 0.4),
]

SENSOR_ROTATIONS = [180, 180+45, -90, 180-45, 90, 45, -45, 0]

# A distance (in % of screen size) constant related to the layout.
d= 0.02
x=0.68

TITLE_PLACEMENT = (x, 0.1)

IP_PLACEMENT = (x, 0.1 + 3* d)

BATTERY_PLACEMENT = (x,0.1 + 8*d)

IMU_PLACEMENT = (x+2*d, 0.1 +14*d)  # Upper left corner

IMU_INTEG_PLACEMENT = (x, 0.1 + 19*d)

POSITION_PLACEMENT = [(x,0.1+26*d), (x+2*d,0.1+26*d), (x+ 4*d, 0.1+26*d)]

UWB_PLACEMENT = (x, 0.1+32*d)              # Upper left corner





class DurinUI(Durin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gamepad = Gamepad()

        self.vertical = 0
        self.horizontal = 0
        self.tau = 0.9999
        self.rot = 0

    def __enter__(self):
        self.a = 0 # Just for debugging. Delete soon!

        pygame.init()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)
        self.big_font = pygame.font.SysFont(None, 34)


        # Set up the display
        # Get screen size
        info = pygame.display.Info()
        self.screen_width, self.screen_height = info.current_w, info.current_h-100

        self.screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)

        # Buffer screen:
        #self.back_buffer = pygame.Surface((self.screen_width, self.screen_height))

        # Make it fullscreen
        if sys.platform == "win32":
            HWND = pygame.display.get_wm_info()['window']
            SW_MAXIMIZE = 3
            ctypes.windll.user32.ShowWindow(HWND, SW_MAXIMIZE)
        
        # Durin Image
        self.image = pygame.image.load("durin/durin_birdseye.jpg")
        self.image = pygame.transform.scale(self.image, (1.75*self.screen_width//3, self.screen_height))


        self.image_surface = pygame.Surface(self.image.get_size())
        self.image_surface.blit(self.image, (0,0))

        # Create surfaces for ToF data.
        self.surfaces = []
        for o in range(8):
            surface = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
            self.surfaces.append(surface)

        pygame.display.update()
        #s"""



        return super().__enter__()
    
    def __exit__(self, e, b, t):
        pygame.quit()
        #self.gamepad.stop()
        return super().__exit__(e, b, t)
    
    def read_user_input(self, allow_movement: bool = True, sleep_interval: float=0.02):
        keys = pygame.key.get_pressed()

        # Gamepad
        if not self.gamepad.queue.empty():
            x, y, r = self.gamepad.queue.get()
            self.horizontal = x
            self.vertical = y
            self.rot = r
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Keyboard
            elif event.type == pygame.KEYDOWN:
                # Key pressed
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.vertical = 500
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.vertical = -500
                elif event.key == pygame.K_LEFT or event.key == pygame.K_d:
                    self.horizontal = -500
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_a:
                    self.horizontal = 500

            elif event.type == pygame.KEYUP:
                # Key released
                if event.key == pygame.K_UP or event.key == pygame.K_w or event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.vertical = 0
                elif event.key == pygame.K_LEFT or event.key == pygame.K_d or event.key == pygame.K_RIGHT or event.key == pygame.K_a:
                    self.horizontal = 0

        if allow_movement:
            self(Move(self.horizontal, self.vertical, self.rot))

        time.sleep(sleep_interval) # Sleep to avoid sending too many commands

        return True
        
    
    def render_sensors(self, obs, size: int = 180):

        self.screen.fill((0,0,0))   # Fill screen with black
        self.screen.blit(self.image_surface, (0,0))

        
        # Update ToF-sensors ######################
        tofs = (np.tanh((obs.tof / 1000)) * 255).astype(np.int32)

        # Rotated surfaces
        rotated_surfaces = []

        for o in range(len(self.surfaces)):
            surface = self.surfaces[o]

            square_size = surface_width//8
            for i in range(8):
                for j in range(8):

                    left = i * square_size
                    top = j * square_size
                    square_rect = pygame.Rect(left, top, square_size, square_size)

                    color_value = tofs[o][i][j]
                    color = (color_value, color_value, color_value)
                    pygame.draw.rect(surface, color, square_rect)


            rotation_angle = SENSOR_ROTATIONS[o]
            rotated_surface = pygame.transform.rotate(surface, rotation_angle)
            rotated_surfaces.append(rotated_surface)


        for i in range(8):
            self.screen.blit(rotated_surfaces[i], (SENSOR_PLACEMENTS[i][0]*self.screen_width,SENSOR_PLACEMENTS[i][1]*self.screen_height))
                
        # Update UWB ######################

        uwb = obs.uwb
        #self.render_text("Becon ID\t\t\tDistance (mm)", UWB_PLACEMENT[0])


        for i in range(10):
            if uwb[i][0] != 0:
                self.render_text(str(uwb[i][0]), (UWB_PLACEMENT[0], UWB_PLACEMENT[1] + i*d))
                self.render_text(str(uwb[i][1]), (UWB_PLACEMENT[0]+ 5*d, UWB_PLACEMENT[1]+i*d))
            else:
                break



        # Update IMU ######################
        imu = obs.imu
        #type = ["Acce", "Gyro", "Magn."]
        for type in range(3):
            for xyz in range(3):
                self.render_text(str(imu[type][xyz]), (IMU_PLACEMENT[0]+xyz*3*d, IMU_PLACEMENT[1]+type*d))
        

        # Update battery level and voltage ######################
        voltage = obs.voltage
        charge = obs.charge
        self.render_text(str(charge) + " %", BATTERY_PLACEMENT)
        self.render_text(str(voltage) + " mV", (BATTERY_PLACEMENT[0]+5*d,BATTERY_PLACEMENT[1]))


        # Update Durin position ######################
        for m in range(3):
            self.render_text(str(obs.position[m]), POSITION_PLACEMENT[m])

        
        self.render_static_texts()

        # Just for debugging.
        self.a += 1
        self.render_text("Time step (for debugging): " + str(self.a),(UWB_PLACEMENT[0],UWB_PLACEMENT[1]+10*d))

        # Update screen
        pygame.display.update()

        #self.clock.tick(100)

    
    def render_text(self, input_text, position, color="w", size = "small"):
        if color == "w":
            c = (255,255,255)
        elif color == "o":
            c = (255,183,91)
        elif color == "b":
            c = (100,100,255)
        elif color == "t":
            c = (255,143,161)

        if size == "small":
            text =  self.font.render(input_text, True, c)
        elif size == "big":
            text=  self.big_font.render(input_text, True, c)
        self.screen.blit(text, (position[0]*self.screen_width,position[1]*self.screen_height))

    def render_static_texts(self):
        # Static texts¨

        self.render_text("Durin Dashboard", TITLE_PLACEMENT, "t", "big")

        self.render_text("IP address", IP_PLACEMENT, "o")
        self.render_text("MAC address", (IP_PLACEMENT[0]+5*d,IP_PLACEMENT[1]), "o")
        self.render_text("Durin ID", (IP_PLACEMENT[0]+10*d,IP_PLACEMENT[1]), "o")

        self.render_text("Integrated IMU data", (IMU_INTEG_PLACEMENT), "o")



        self.render_text("UWB ID", (UWB_PLACEMENT[0],UWB_PLACEMENT[1]-2*d), "o")
        self.render_text("Distance (mm)", (UWB_PLACEMENT[0]+5*d,UWB_PLACEMENT[1]-2*d), "o")

        self.render_text("IMU data",(IMU_PLACEMENT[0]-2*d,IMU_PLACEMENT[1]-3*d), "o")
        self.render_text("x",(IMU_PLACEMENT[0],IMU_PLACEMENT[1]-d), "b")
        self.render_text("y",(IMU_PLACEMENT[0]+3*d,IMU_PLACEMENT[1]-d),"b")
        self.render_text("z",(IMU_PLACEMENT[0]+6*d,IMU_PLACEMENT[1]-d),"b")
        self.render_text("Acce",(IMU_PLACEMENT[0]-2*d,IMU_PLACEMENT[1]),"b")
        self.render_text("Gyro",(IMU_PLACEMENT[0]-2*d,IMU_PLACEMENT[1]+d),"b")
        self.render_text("Magn",(IMU_PLACEMENT[0]-2*d,IMU_PLACEMENT[1]+2*d),"b")

        self.render_text("Battery level",(BATTERY_PLACEMENT[0],BATTERY_PLACEMENT[1]-d), "o")
        self.render_text("Voltage",(BATTERY_PLACEMENT[0]+5*d,BATTERY_PLACEMENT[1]-d), "o")


        self.render_text("Durin coordinates",(POSITION_PLACEMENT[0][0],POSITION_PLACEMENT[0][1]-3*d), "o")
        self.render_text("x",(POSITION_PLACEMENT[0][0],POSITION_PLACEMENT[0][1]-d),"b")
        self.render_text("y",(POSITION_PLACEMENT[1][0],POSITION_PLACEMENT[0][1]-d),"b")
        self.render_text("z",(POSITION_PLACEMENT[2][0],POSITION_PLACEMENT[0][1]-d),"b")
    




