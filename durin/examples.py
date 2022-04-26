import time
import pdb
import socket
import numpy as np

from dataclasses import dataclass
from typing import List, Optional
from actuator import *
from common import *

T_WAIT = 0.1

def example_moving(durin):

    # Move Durin using robcentric command
    (vel_x, vel_y, rot) = (-1, 2, 3)
    print(f"move_robcentric {vel_x} {vel_y} {rot}")
    reply = durin(MoveRobcentric(vel_x, vel_y, rot))
    print(reply)
    time.sleep(T_WAIT)

    # Move Durin using robcentric command
    (m1, m2, m3, m4) = (-5, 0, 1, 9)
    print(f"move_wheels {m1} {m2} {m3} {m4}")
    reply = durin(MoveWheels(m1, m2, m3, m4))
    print(reply)
    time.sleep(T_WAIT)

    # Move Durin using robcentric command
    (vel_x, vel_y, rot) = (6,5,2)
    print(f"move_robcentric {vel_x} {vel_y} {rot}")
    reply = durin(MoveRobcentric(vel_x, vel_y, rot))
    print(reply)
    time.sleep(T_WAIT)

    # Powering durin off
    reply = durin(Request('power_off'))
    time.sleep(T_WAIT)

def example_polling(durin):

    # Get sensory data from sensor 128
    print("Polling ToF[0:1]:")
    reply = durin(PollSensor(SENSORS["tof_a"]))
    print(reply)
    time.sleep(T_WAIT)

    # Get sensory data from sensor 129
    print("Polling ToF[2:3]")
    reply = durin(PollSensor(SENSORS["tof_b"]))
    print(reply)
    time.sleep(T_WAIT)

    # Get sensory data from sensor 130
    print("Polling ToF[4:5]")
    reply = durin(PollSensor(SENSORS["tof_c"]))
    print(reply)
    time.sleep(T_WAIT)

    # Get sensory data from sensor 131
    print("Polling ToF[6:7]")
    reply = durin(PollSensor(SENSORS["tof_d"]))
    print(reply)
    time.sleep(T_WAIT)

    # Get sensory data from sensor 132
    print("Polling BatteryCharge+Voltage) + IMU:")
    reply = durin(PollSensor(SENSORS["misc"]))
    print(reply)
    time.sleep(T_WAIT)

    # Get sensory data from sensor 133
    print("Polling UWB")
    reply = durin(PollSensor(SENSORS["uwb"]))
    print(reply)
    time.sleep(T_WAIT)


def example_streaming(durin, px_np=[], duration=10):  

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))

    
    ip_address = s.getsockname()[0]
    port_udp = 4300
    period = 10

    print(f"UDP on {ip_address}:{port_udp} ... {period}")

    # Activating/deactivating continuous streaming of sensory data on UDP
    reply = durin(StreamOn(ip_address, port_udp, period))
    count = 0
    t_start = time.time()
    t_current = t_start
    while (t_current-t_start) < duration:

        t_current = time.time()
        
        (obs, dvs) = durin.sense()
        if len(px_np) > 0:
            px_np[:,:]= obs.tof
        count += 1


    print("Waiting some time ... ")
    time.sleep(2)
    reply = durin(StreamOff())
