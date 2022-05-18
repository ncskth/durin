from abc import ABC, abstractmethod
import time
from typing import Generic, Tuple, TypeVar

from .ringbuffer import RingBuffer
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


class DurinSensor(Sensor[Observation]):
    def __init__(self, link: UDPLink):
        self.link = link
        self.tof = np.zeros((8, 8 * 8))
        self.uwb = np.zeros((0,))
        self.charge = 0
        self.voltage = 0
        self.imu = np.zeros((3, 3))
        self.ringbuffer = RingBuffer(shape=(50,))
        self.timestamp_update = time.time()
        self.freq = 0

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

        # Update Hz
        time_now = time.time()
        times = self.ringbuffer.append(time_now - self.timestamp_update)
        self.freq = times.mean()
        self.timestamp_update = time_now

        return Observation(self.tof, (self.charge, self.voltage), self.imu, self.uwb)
