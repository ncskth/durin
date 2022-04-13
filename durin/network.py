import socket
import multiprocessing
from typing import ByteString


class UDPBuffer:
    """
    An UDPBuffer that silently buffers messages received over UDP into a queue.
    """

    def __init__(
        self, host: str, port: str, package_size: int = 1024, buffer_size: int = 10
    ):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = (host, int(port))
        self.package_size = package_size
        self.thread = None
        self.buffer = multiprocessing.Queue(buffer_size)
        self.thread = multiprocessing.Process(target=self._loop_buffer)

    def start_buffering(self):
        self.socket.bind(self.address)
        self.thread.start()

    def _loop_buffer(self):
        while True:
            data = self.socket.recv(self.package_size)
            self.buffer.put(data, block=False)

    def get(self):
        return self.buffer.get(block=True)

    def send(self, data: ByteString):
        self.socket.send(data)

    def stop_buffering(self):
        self.thread.terminate()
        self.thread.join()
