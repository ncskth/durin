from typing import Tuple
import torch
import aestream

from durin.sensor import Sensor


class DVSSensor(Sensor[torch.Tensor]):
    def __init__(self, shape: Tuple[int, int], device: str, port: int):
        self.source = aestream.UDPInput(shape, device, port)

    def start_stream(self) -> torch.Tensor:
        return self.source.start_stream()

    def stop_stream(self) -> torch.Tensor:
        return self.source.stop_stream()

    def read(self) -> torch.Tensor:
        return self.source.read()
