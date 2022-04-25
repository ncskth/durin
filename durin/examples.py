import time
import pdb
import socket

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


def example_streaming(durin):      
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))

            ip_address = s.getsockname()[0]
            port_udp = 4300
            period = 500

            # Activating/deactivating continuous streaming of sensory data on UDP
            reply = durin(StreamOn(ip_address, port_udp, period))
            count = 0
            while count < 10:
                
                (obs, dvs) = durin.sense()
                print("ToF Sensors:")
                for i in range(8):
                    print(f"tof{i}:\n{obs.tof[:,i*8:i*8+8]}")
                print("Battery:")
                print(obs.bat)
                print("IMU:")
                print(obs.imu)
                print("UWB:")
                print(obs.uwb)
                count += 1
                time.sleep(0.1)
                print("\n\n\n")


            print("Waiting some time ... ")
            time.sleep(2)
            reply = durin(StreamOff())
