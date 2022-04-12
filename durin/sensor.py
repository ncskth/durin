from abc import ABC, abstractmethod
from typing import ByteString, Generic, TypeVar

T = TypeVar("T")


class Sensor(ABC, Generic[T]):
    @abstractmethod
    def on_data(self, data: ByteString):
        pass

    @abstractmethod
    def read() -> T:
        pass

class DurinSensor(Sensor[...]):
    pass

class MockSensor(Sensor[...]):
    pass