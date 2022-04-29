from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ByteString, Callable, Generic, Tuple, TypeVar

import torch
import numpy as np
import aestream

from .network import UDPLink
from .common import *

T = TypeVar("T")


class Observation:
    def __init__(self, tof, bat, imu, uwb):
        self.tof = tof
        self.bat = bat
        self.imu = imu
        self.uwb = uwb


class Sensor(ABC, Generic[T]):
    @abstractmethod
    def read(self) -> T:
        pass


class DVSSensor(Sensor[torch.Tensor]):
    def __init__(self, shape: Tuple[int, int], device: str, port: int):
        self.source = aestream.UDPInput(shape, device, port)

    def start_stream(self) -> torch.Tensor:
        return self.source.start_stream()

    def stop_stream(self) -> torch.Tensor:
        return self.source.stop_stream()

    def read(self) -> torch.Tensor:
        return self.source.read()


class DurinSensor(Sensor[Observation]):
    def __init__(self, link: UDPLink):
        self.link = link
        self.tof = np.zeros((8, 8 * 8))
        self.uwb = np.zeros((0,))
        self.charge = 0
        self.voltage = 0
        self.imu = np.zeros((3, 3))

    def read(self) -> Observation:
        (sensor_id, data) = self.link.get()
        if sensor_id >= SENSORS["tof_a"] and sensor_id <= SENSORS["tof_d"]:
            idx = sensor_id - SENSORS["tof_a"]
            self.tof[:, idx * 16 : idx * 16 + 16] = data
        if sensor_id == SENSORS["misc"]:
            self.charge = data[0]
            self.voltage = data[1]
            self.imu = data[2]
        if sensor_id == SENSORS["uwb"]:
            self.uwb = data

        return Observation(self.tof, (self.charge, self.voltage), self.imu, self.uwb)
