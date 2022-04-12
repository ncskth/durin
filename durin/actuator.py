from abc import ABC, abstractmethod
from typing import Generic, TypeVar


T = TypeVar("T")


class Actuator(ABC, Generic[T]):
    @abstractmethod
    def apply(self, action: T) -> None:
        pass
