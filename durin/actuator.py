from abc import ABC, abstractmethod
from dataclasses import dataclass
import ipaddress
from queue import Full
from typing import ByteString, TypeVar
import struct

from .network import TCPLink, UDPLink
from .common import *


T = TypeVar("T")


@dataclass
class Command:
    pass

    @abstractmethod
    def encode() -> ByteString:
        pass


class PowerOff(Command):
    def __init__(self):
        self.cmd_id = 1

    def encode(self):
        data = bytearray([0] * 1)
        data[0] = self.cmd_id

        return data


class Move(Command):
    def __init__(self, vel_x, vel_y, rot):
        self.cmd_id = 2
        self.vel_x = int(vel_x)
        self.vel_y = int(vel_y)
        self.rot = int(rot)

    def encode(self):
        data = bytearray([0] * 7)
        data[0] = self.cmd_id
        data[1:3] = bytearray(
            struct.pack("<h", self.vel_x)
        )  # short (int16) little endian
        data[3:5] = bytearray(
            struct.pack("<h", self.vel_y)
        )  # short (int16) little endian
        data[5:7] = bytearray(
            struct.pack("<h", self.rot)
        )  # short (int16) little endian

        return data


class MoveWheels(Command):
    def __init__(self, m1, m2, m3, m4):
        self.cmd_id = 3
        self.m1 = int(m1)
        self.m2 = int(m2)
        self.m3 = int(m3)
        self.m4 = int(m4)

    def encode(self):
        data = bytearray([0] * 9)
        data[0] = self.cmd_id
        data[1:3] = bytearray(struct.pack("<h", self.m1))  # short (int16) little endian
        data[3:5] = bytearray(struct.pack("<h", self.m2))  # short (int16) little endian
        data[5:7] = bytearray(struct.pack("<h", self.m3))  # short (int16) little endian
        data[7:9] = bytearray(struct.pack("<h", self.m4))  # short (int16) little endian

        return data


class PollAll(Command):
    def __init__(self):
        self.cmd_id = 16

    def encode(self):
        data = bytearray([0] * 1)
        data[0] = self.cmd_id

        return data


class PollSensor(Command):
    def __init__(self, sensor_id):
        self.cmd_id = 17
        self.sensor_id = int(sensor_id)

    def encode(self):
        data = bytearray([0] * 2)
        data[0] = self.cmd_id
        data[1:2] = self.sensor_id.to_bytes(
            1, "little"
        )  # integer (uint8) little endian

        return data


class StreamOn(Command):
    def __init__(self, host, port, period):
        self.cmd_id = 18
        self.host = host
        self.port = port
        self.period = period

    def encode(self):
        data = bytearray([0] * 9)
        data[0] = self.cmd_id
        host = self.host.split(".")
        data[1] = int(host[0])
        data[2] = int(host[1])
        data[3] = int(host[2])
        data[4] = int(host[3])
        data[5:7] = self.port.to_bytes(2, "little")
        data[7:9] = self.period.to_bytes(2, "little")
        return data


class StreamOff(Command):
    def __init__(self):
        self.cmd_id = 19

    def encode(self):
        data = bytearray([0] * 1)
        data[0] = self.cmd_id

        return data


class DurinActuator:
    def __init__(self, tcp_link: TCPLink):
        self.tcp_link = tcp_link

    def __call__(self, action: Command, timeout: float = 0.05):
        command_bytes = action.encode()
        reply = []
        if command_bytes[0] == 0:
            return reply

        try:
            self.tcp_link.send(command_bytes, timeout=timeout)
        except Full:
            pass

        return None

    def read(self):
        reply = self.tcp_link.read()
        if reply is not None:
            return decode(reply)
        else:
            return None
