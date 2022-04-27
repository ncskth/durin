from typing import Tuple
from actuator import DurinActuator
from sensor import DurinSensor, Observation, DVSSensor
from network import TCPLink, UDPLink
from common import *
from cli import *

import torch


class Durin():    

    def __init__(self, host, port_tcp):
        self.tcp_link = TCPLink(host, port_tcp)
        self.udp_link = UDPLink()
        self.sensor = DurinSensor(self.udp_link)
        self.actuator = DurinActuator(self.tcp_link, self.udp_link) 
        self.dvs = DVSSensor((128, 128), port + 1) 

    def __enter__(self):
        self.tcp_link.start_com()
        return self

    def __exit__(self, e, b, t):
        self.tcp_link.stop_com()

    def __call__(self, command):
        reply_bytes = self.actuator(command)
        return reply_bytes

    def sense(self) -> Tuple[Observation, torch.Tensor]:
        durin = self.sensor.read()
        dvs = self.dvs.read()
        return (durin, dvs)


