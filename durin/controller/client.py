import ipaddress
import logging
import socket


class DVSClient:
    def __init__(self, host: str, port: int) -> None:
        self.address = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.address)

    def _send_message(self, message: bytes):
        logging.debug("Sending to server: ", message)
        self.sock.send(message)

    def start_stream(self, host: str, port: int):
        data = bytearray([0] * 7)
        data[0] = 0x0
        data[1:5] = int(ipaddress.ip_address(host)).to_bytes(4, "little")
        data[5:7] = port.to_bytes(2, "little")
        self._send_message(data)

    def stop_stream(self):
        self._send_message(bytes([1]))
        self.sock.close()
