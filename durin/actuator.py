
import queue

from durin import io
from durin.io.command import *
from durin.io.network import TCPLink
from durin.controller import *

class DurinActuator:
    def __init__(self, tcp_link: TCPLink):
        self.tcp_link = tcp_link

    def __call__(self, action: Command, timeout: float = 0.05):
        command_bytes = action.encode()
        try:
            self.tcp_link.send(command_bytes, timeout=timeout)
        except queue.Full:
            pass

        return None

    def read(self):
        reply = self.tcp_link.read()
        if reply is not None:
            msg = io.decode(reply)
            return msg

        else:
            return None

    def start(self):
        self.tcp_link.start()

    def stop(self):
        self.tcp_link.stop()
