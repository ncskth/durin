import ipaddress
import logging
import socket


class DVSClient:
    def __init__(self, host: str, port: int) -> None:
        self.sock = None
        self.address = (host, port)

    def _init_connection(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.address)

    def _send_message(self, message: bytes):
        logging.debug("Sending to server: ", message)
        try:
            self.sock.send(message)
        except (BrokenPipeError, AttributeError):
            self._init_connection()
            self.sock.send(message)

    def start_stream(self, host: str, port: int):
        data = bytearray([0] * 7)
        data[0] = 0x0
        data[1:5] = int(ipaddress.ip_address(host)).to_bytes(4, "little")
        data[5:7] = port.to_bytes(2, "little")
        self._send_message(data)

    def stop_stream(self):
        if self.sock is not None:
            self._send_message(bytes([1]))
            self.sock.close()
            self.sock = None
