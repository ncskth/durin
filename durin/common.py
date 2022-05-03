from ctypes import *
import socket
import numpy as np
import datetime


BRAIN_IP = "127.0.0.1"
DURIN_IP = "127.0.0.1"
PORT_TCP = 1337
PORT_UDP = 2300


def available_cmds():

    cmdlist = []

    # List of available commands
    filepath = "commands.txt"

    with open(filepath) as fp:
        while True:
            line = fp.readline()
            if not line:
                break
            line = line.split()

            cmdlist.append(line)

    return cmdlist


def available_sensors():

    sensorsdict = {}

    # List of available commands
    filepath = "sensors.txt"

    with open(filepath) as fp:
        while True:
            line = fp.readline()
            if not line:
                break
            line = line.split()
            sensorsdict.update({line[1]: int(line[0])})

    return sensorsdict


# SENSORS = available_sensors()
SENSORS = {
    "tof_a": 128,
    "tof_b": 129,
    "tof_c": 130,
    "tof_d": 131,
    "misc": 132,
    "uwb": 133,
}


def decode(buffer):

    reply = "No reply expected"
    sensor_id = buffer[0]

    # Decoding ToF Sensors
    if int(sensor_id) >= SENSORS["tof_a"] and int(sensor_id) <= SENSORS["tof_d"]:
        tof = np.zeros((8, 16))
        tof[:, 0:8] = np.frombuffer(buffer, dtype="<H", offset=1, count=64).reshape(
            (8, 8)
        )
        tof[:, 8:16] = np.frombuffer(
            buffer, dtype="<H", offset=1 + 64 * 2, count=64
        ).reshape((8, 8))
        reply = tof

    # Decoding Miscelaneous Sensors
    if int(sensor_id) == SENSORS["misc"]:
        charge = int.from_bytes(buffer[1:2], "little")
        voltage = int.from_bytes(buffer[2:4], "little")
        imu = np.frombuffer(buffer, dtype="<h", offset=4, count=9).reshape((3, 3))
        reply = (charge, voltage, imu)

    # Decoding UWB Sensors
    if int(sensor_id) == SENSORS["uwb"]:
        nb_beacons = int.from_bytes(buffer[1:2], "little")
        uwb = np.frombuffer(buffer, dtype="<f", offset=2, count=nb_beacons)
        reply = uwb

    return sensor_id, reply


def get_ip():
    # Thanks to https://stackoverflow.com/a/28950776/999865
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP
