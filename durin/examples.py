import time
import pdb

from dataclasses import dataclass
from typing import List, Optional
from durin import Durin
from actuator import *

T_WAIT = 1
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
            reply = durin(MoveWheels(-1, 2, -3, 5))
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
            reply = durin(PollSensor(128))
            print(reply)
            time.sleep(T_WAIT)

            # Get sensory data from sensor 129
            print("Polling ToF[2:3]")
            reply = durin(PollSensor(129))
            print(reply)
            time.sleep(T_WAIT)

            # Get sensory data from sensor 130
            print("Polling ToF[4:5]")
            reply = durin(PollSensor(130))
            print(reply)
            time.sleep(T_WAIT)

            # Get sensory data from sensor 131
            print("Polling ToF[6:7]")
            reply = durin(PollSensor(131))
            print(reply)
            time.sleep(T_WAIT)

            # Get sensory data from sensor 132
            print("Polling BatteryCharge+Voltage) + IMU:")
            reply = durin(PollSensor(132))
            print(reply)
            time.sleep(T_WAIT)

            # Get sensory data from sensor 133
            print("Polling UWB")
            reply = durin(PollSensor(133))
            print(reply)
            time.sleep(T_WAIT)


def example_streaming(durin):      

            # Activating/deactivating continuous streaming of sensory data on UDP
            reply = durin(StreamOn('127.0.0.1', 4300, 2000))
            time.sleep(2.5)
            reply = durin(StreamOff())
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


            # Activating/deactivating continuous streaming of sensory data on UDP
            reply = durin(StreamOn('127.0.0.1', 4600, 500))
            time.sleep(2.5)
            count = 0
            while count < 10:
                

                data = durin.sense()
                count += 1
                time.sleep(0.1)

            reply = durin(StreamOff())