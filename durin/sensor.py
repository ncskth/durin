from abc import ABC, abstractmethod
import logging
import multiprocessing
import time
from typing import Generic, NamedTuple, Tuple, TypeVar

import numpy as np
from durin.io import SENSORS

from durin.io.network import UDPLink
from durin.io.runnable import RunnableConsumer
from durin.io.ringbuffer import RingBuffer

T = TypeVar("T")


class Observation(NamedTuple):
    tof: np.ndarray = np.zeros((8, 8, 8))
    tof_frequency: float = 0
    charge: float = 0
    voltage: float = 0
    imu: np.ndarray = np.zeros((3, 3))
    imu_frequency: float = 0
    uwb: float = 0
    uwb_frequency: float = 0
    status_frequency: float = 0

    def __repr__(self) -> str:
        tof_str = " ".join([f"{x.mean():.0f}±{x.std():.0f}" for x in self.tof])
        return f"Durin {self.battery}%\n\tIMU: {self.imu}\n\tTOF: {tof_str}"


class Sensor(ABC, Generic[T]):
    @abstractmethod
    def read(self) -> T:
        pass


class DurinSensor(RunnableConsumer, Sensor[Observation]):

    _BUFFER_LENGTH = 50

    def __init__(self, link: UDPLink):
        self.link = link
        context = multiprocessing.get_context("spawn")

        self.tof = context.Array("f", 8 * 8 * 8)
        self.tof_ringbuffer = context.Array("d", self._BUFFER_LENGTH)
        self.tof_ringbuffer_idx = context.Value("i", 0)

        self.charge = context.Value("f", 0)
        self.voltage = context.Value("f", 0)
        self.status_ringbuffer = context.Array("d", self._BUFFER_LENGTH)
        self.status_ringbuffer_idx = context.Value("i", 0)

        self.imu = context.Array("d", 3 * 3)
        self.imu_ringbuffer = context.Array("d", self._BUFFER_LENGTH)
        self.imu_ringbuffer_idx = context.Value("i", 0)

        self.uwb = context.Value("d", 0)
        self.uwb_ringbuffer = context.Array("d", self._BUFFER_LENGTH)
        self.uwb_ringbuffer_idx = context.Value("i", 0)

        super().__init__(
            self.link.buffer,
            self.tof,
            self.tof_ringbuffer,
            self.tof_ringbuffer_idx,
            self.charge,
            self.voltage,
            self.status_ringbuffer,
            self.status_ringbuffer_idx,
            self.imu,
            self.imu_ringbuffer,
            self.imu_ringbuffer_idx,
            self.uwb,
            self.uwb_ringbuffer,
            self.uwb_ringbuffer_idx
        )

    def _read_buffer_frequency(self, buffer, index):
        buffer = RingBuffer(buffer.get_obj(), index.value)
        difference = buffer.get_newest() - buffer.get_oldest()
        return self._BUFFER_LENGTH / difference

    def read(self) -> Observation:
        tof = np.frombuffer(self.tof.get_obj(), dtype=np.float32).reshape((8, 8, 8))
        imu = np.frombuffer(self.imu.get_obj()).reshape((3, 3))
        return Observation(
            tof=tof,
            tof_frequency=self._read_buffer_frequency(self.tof_ringbuffer, self.tof_ringbuffer_idx),
            charge=self.charge.value,
            voltage=self.voltage.value,
            status_frequency=self._read_buffer_frequency(self.status_ringbuffer, self.status_ringbuffer_idx),
            imu=imu,
            imu_frequency=self._read_buffer_frequency(self.imu_ringbuffer, self.imu_ringbuffer_idx),
            uwb=self.uwb.value,
            uwb_frequency=self._read_buffer_frequency(self.uwb_ringbuffer, self.uwb_ringbuffer_idx),
        )

    def start(self):
        super().start()
        self.link.start()

    def stop(self):
        super().stop()
        self.link.stop()

    def consume(
        self,
        item,
        tof,
        tof_ringbuffer,
        tof_ringbuffer_idx,
        charge,
        voltage,
        status_ringbuffer,
        status_ringbuffer_idx,
        imu,
        imu_ringbuffer,
        imu_ringbuffer_idx,
        uwb,
        uwb_ringbuffer,
        uwb_ringbuffer_idx
    ):
        which = item.which()
        try:
            if which == "tofObservations":
                for obs in item.tofObservations.observations:
                    data = np.array(obs.ranges)
                    tof.get_obj()[obs.id * 64: (obs.id+1) * 64] = data
                self._update_frequency(tof_ringbuffer, tof_ringbuffer_idx)
            elif which == "systemStatus":
                charge.value = item.systemStatus.batteryPercent
                voltage.value = item.systemStatus.batteryMv
                self._update_frequency(status_ringbuffer, status_ringbuffer_idx)

            # TODO: Add more sensors
        except Exception as e:
            logging.warning("Error when receiving sensor data " + str(e))

    def _update_frequency(self, buffer_name, buffer_idx):
        buffer_obj = buffer_name.get_obj()
        buffer = RingBuffer(np.frombuffer(buffer_obj), buffer_idx.value)
        buffer.append(time.time())
        buffer_obj[:] = buffer.buffer
        buffer_idx.value = buffer.counter
        