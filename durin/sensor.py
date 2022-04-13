from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ByteString, Callable, Generic, Tuple, TypeVar

import torch
import aestream

from durin.network import UDPBuffer

T = TypeVar("T")


@dataclass
class Observation:
    pass


class Sensor(ABC, Generic[T]):
    @abstractmethod
    def read(self) -> T:
        pass


class DVSSensor(Sensor[torch.Tensor]):
    def __init__(self, shape: Tuple[int, int], port: int):
        self.source = aestream.UDPInput(shape, port)

    def read(self) -> torch.Tensor:
        return self.source.read()


class DurinSensor(Sensor[Observation]):
    def __init__(self, reader: Callable[[None], Observation]):
        self.reader = reader

    def read(self) -> Observation:
        return self.reader()


# class MockSensor(Sensor[...]):
#     pass
