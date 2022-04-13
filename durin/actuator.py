from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from durin.network import UDPBuffer


T = TypeVar("T")


@dataclass
class Action:
    pass


class Actuator(ABC, Generic[T]):
    @abstractmethod
    def apply(self, action: T) -> None:
        pass


class DurinActuator(Actuator[Action]):
    def __init__(self, sender: Callable[[Action], None]):
        self.sender = sender

    def apply(self, action: Action):
        self.sender(action)
