from typing import ByteString, Tuple
from durin.actuator import Action, Actuator, DurinActuator
from durin.sensor import DVSSensor, DurinSensor, Observation, Sensor
from durin.network import UDPBuffer

import torch


class Durin(Actuator[Action], Sensor[Tuple[Observation, torch.Tensor]]):
    def __init__(self, host, port):
        self.udp_buffer = UDPBuffer(host, port)
        self.sensor = DurinSensor(self.udp_buffer.get)
        self.actor = DurinActuator(
            lambda action: self.udp_buffer.send(self._encode_package(action))
        )
        self.dvs = DVSSensor((128, 128), port + 1)

    def __enter__(self):
        self.buffer.start_buffering()

    def __exit__(self, e, b, t):
        self.buffer.stop_buffering()

    def apply(self, action: Action) -> None:
        return self.actor(action)

    def _encode_package(self, action: Action) -> ByteString:
        return b""

    def read(self) -> Tuple[Observation, torch.Tensor]:
        durin = self.sensor.read()
        dvs = self.dvs.read()
        return (durin, dvs)


class MockDuring(Durin):
    pass
