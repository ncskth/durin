from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ByteString, TypeVar
from network import TCPLink, UDPLink
from common import *
from cli import *
import struct
import numpy as np


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
        data = bytearray([0] * 2)
        data[0] = self.cmd_id
        data[1] = 1 # id + byte_count
        
        return data


class MoveRobcentric(Command):

    def __init__(self, vel_x, vel_y, rot):
        self.cmd_id = 2
        self.vel_x = int(vel_x)
        self.vel_y = int(vel_y)
        self.rot = int(rot)

    def encode(self):
        data = bytearray([0] * 8)
        data[0] = self.cmd_id
        data[1] = 6 # id + byte_count + 3*2
        data[2:4] = bytearray(struct.pack("<h", self.vel_x)) #short (int16) little endian
        data[4:6] = bytearray(struct.pack("<h", self.vel_y)) #short (int16) little endian
        data[6:8] = bytearray(struct.pack("<h", self.rot)) #short (int16) little endian
        
        return data


class MoveWheels(Command):

    def __init__(self, m1, m2, m3, m4):
        self.cmd_id = 3
        self.m1 = int(m1)
        self.m2 = int(m2)
        self.m3 = int(m3)
        self.m4 = int(m4)

    def encode(self):
        data = bytearray([0] * 10)
        data[0] = self.cmd_id
        data[1] = 8 # id + byte_count + 4*2
        data[2:4] = bytearray(struct.pack("<h", self.m1)) #short (int16) little endian
        data[4:6] = bytearray(struct.pack("<h", self.m2)) #short (int16) little endian
        data[6:8] = bytearray(struct.pack("<h", self.m3)) #short (int16) little endian
        data[8:10] = bytearray(struct.pack("<h", self.m4)) #short (int16) little endian
        
        return data


class PollAll(Command):

    def __init__(self):
        self.cmd_id = 16

    def encode(self):
        data = bytearray([0] * 2)
        data[0] = self.cmd_id
        data[1] = 1 # id + byte_count
        
        return data


class PollSensor(Command):

    def __init__(self, sensor_id):
        self.cmd_id = 17
        self.sensor_id = int(sensor_id) 

    def encode(self):
        data = bytearray([0] * 3)
        data[0] = self.cmd_id
        data[1] = 3 # id + byte_count + 4*2
        data[2:3] = self.sensor_id.to_bytes(1, 'little') # integer (uint8) little endian
        
        return data


class StreamOn(Command):

    def __init__(self, host, port, period):
        self.cmd_id = 18
        self.host = host
        self.port = port
        self.period = period

    def encode(self):
        host = self.host.split('.')
        byte_count = len(host)+2

        data = bytearray([0] * (1+byte_count))
        data[0] = self.cmd_id
        data[1] = 10 # id + byte_count + 4 (host) + 2 (port) +2 (period)
        data[2] = int(host[0])
        data[3] = int(host[1])
        data[4] = int(host[2])
        data[5] = int(host[3])
        data[6:8] = self.port.to_bytes(2, 'little')
        data[8:10] = self.period.to_bytes(2, 'little')
        
        return data


class StreamOff(Command):

    def __init__(self):
        self.cmd_id = 19

    def encode(self):
        data = bytearray([0] * 2)
        data[0] = self.cmd_id
        data[1] = 1 # id + byte_count
        
        return data


class Request(Command):

    def __init__(self, cli_in):
        self.cli_in = cli_in
        self.cmdlist = available_cmds()
        self.cmd_id = 0

    def encode(self):
        data = bytearray([0] * 1)
        command, arg_array, isvalid = parse_line(self.cli_in)
        if isvalid:
            
            self.cmd_id = int(self.cmdlist[[command in list for list in self.cmdlist].index(True)][0])
            
            if command == "power_off":
                data = PowerOff().encode()                
                
            if command == "move_robcentric":
                data = MoveRobcentric(arg_array[0], arg_array[1], arg_array[2]).encode()

            if command == "move_wheels":
                data = MoveWheels(arg_array[0], arg_array[1], arg_array[2], arg_array[3]).encode()

            if command == "poll_all":
                data = PollAll().encode()

            if command == "poll_sensor":
                data = PollSensor(arg_array[0]).encode()

            if command == "start_stream":
                data = StreamOn().encode()

            if command == "stop_stream":
                data = StreamOff().encode()
                

        return data


class DurinActuator():
    def __init__(self, tcp_link: TCPLink, udp_link: UDPLink):
        self.tcp_link = tcp_link
        self.udp_link = udp_link

    def __call__(self, action: Command):
        command_bytes = action.encode()
        reply = []
        if command_bytes[0] == 0:
            return reply

        if type(action) == StreamOn:
            self.udp_link.start_com((action.host, action.port))  
            
        if type(action) == StreamOff: 
            self.udp_link.stop_com()

        buffer = self.tcp_link.send(command_bytes)
        _ , reply = decode(buffer)
        return reply

            
                

    def write(self, action):
        self.tcp_link.send(action)

