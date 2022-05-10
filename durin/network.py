import ipaddress
import logging
from queue import Empty, Full
import socket
import multiprocessing
from typing import ByteString, Optional, Tuple

from .common import *


class TCPLink:
    """ """

    def __init__(
        self,
        host: str,
        port: str,
        buffer_size_send: int = 3,
        buffer_size_receive: int = 1000,
    ):
        self.address = (host, int(port))
        # Buffer towards Durin
        self.buffer_send = multiprocessing.Queue(buffer_size_send)
        # Buffer receiving replies
        self.buffer_receive = multiprocessing.Queue(buffer_size_receive)

        # Create socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(self.address)
        except (ConnectionRefusedError, OSError) as e:
            raise ConnectionRefusedError(f"Cannot reach Durin at {self.address}")

        # Start threads
        self.process_send = multiprocessing.Process(
            target=self._tcp_send,
            args=(self.buffer_send, self.sock, self.address),
        )
        self.process_receive = multiprocessing.Process(
            target=self._tcp_receive, args=(self.buffer_receive, self.sock, 0.1)
        )

    def start_com(self):
        self.process_receive.start()
        self.process_send.start()

    # Send Command to Durin and wait for response
    def send(self, command: ByteString, timeout: float) -> None:
        try:
            self.buffer_send.put(command, block=False)
        except Full:
            return None

    def stop_com(self):
        logging.debug(f"TCP control communication stopped")
        for p in [self.process_send, self.process_receive]:
            p.terminate()
            p.join()
        self.sock.close()

    def read(self) -> Optional[ByteString]:
        try:
            return self.buffer_receive.get(block=False)
        except Empty:
            return None

    @staticmethod
    def _tcp_receive(
        queue_receive: multiprocessing.Queue, sock: socket.socket, timeout: float
    ):
        try:
            while True:
                data = sock.recv(512)
                queue_receive.put(data)
        except ConnectionResetError:
            raise ConnectionResetError("TCP control communication ended by Durin")

    @staticmethod
    def _tcp_send(
        queue_send: multiprocessing.Queue,
        sock: socket.socket,
        address: Tuple[str, int],
    ):
        try:
            while True:
                command = queue_send.get()
                sock.send(command)

        except ConnectionResetError:
            raise ConnectionResetError("TCP control communication ended by Durin")


class UDPLink:
    """
    An UDPBuffer that silently buffers messages received over UDP into a queue.
    """

    def __init__(self, package_size: int = 512, buffer_size: int = 2):
        self.buffer_size = buffer_size
        self.package_size = package_size
        self.buffer = multiprocessing.Queue(self.buffer_size)
        self.thread = None

    def start_com(self, host: str, ip: int):
        self.thread = multiprocessing.Process(
            target=self._loop_buffer,
            args=(self.buffer, host, ip),
        )
        self.thread.start()

    def _loop_buffer(self, message_queue, host, ip):
        count = 0
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        address = (host, ip)
        sock.bind(address)

        logging.debug(f"UDP control receiving on {address}")

        try:
            while True:
                buffer, _ = sock.recvfrom(self.package_size)
                sensor_id, reply = decode(buffer)
                try:
                    message_queue.put((sensor_id, reply), block=False)
                except Full:
                    pass  # Queue is full
                count += 1
        except KeyboardInterrupt:
            pass
        finally:
            try:
                sock.close()
            except:
                pass

    # get data from buffer
    def get(self):
        try:
            return self.buffer.get(block=False)
        except Empty:
            return (0, [])

    def stop_com(self):
        self.buffer.close()
        self.buffer = multiprocessing.Queue(self.buffer_size)
        self.thread.terminate()
        self.thread.join()


class DVSClient:
    def __init__(self, host: str, port: int) -> None:
        self.sock = None
        self.address = (host, port)

    def _init_connection(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.address)
        logging.debug(f"UDP DVS communication sending to {self.address}")

    def _send_message(self, message: bytes):
        try:
            self.sock.send(message)
        except (BrokenPipeError, AttributeError) as e:
            try:
                self._init_connection()
            except ConnectionRefusedError as e:
                raise ConnectionRefusedError(
                    f"Could not connect to DVS controller at {self.address}"
                )
            self._send_message(message)

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
