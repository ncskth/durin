import ipaddress
import logging
from queue import Empty, Full
import socket
import multiprocessing
from typing import ByteString, Tuple

from .common import *


class TCPLink:
    """ """

    def __init__(self, host: str, port: str, buffer_size: int = 1024):
        self.address = (host, int(port))
        # Buffer towards Durin
        self.buffer_send = multiprocessing.Queue(buffer_size)
        # Buffer receiving replies
        self.buffer_receive = multiprocessing.Queue(buffer_size)
        self.process = multiprocessing.Process(
            target=self._tcp_loop,
            args=(self.buffer_send, self.buffer_receive, self.address),
        )

    def start_com(self):
        self.process.start()

    # Send Command to Durin and wait for response
    def send(self, command: ByteString):
        self.buffer_send.put(command)
        return self.buffer_receive.get()

    def stop_com(self):
        logging.debug(f"TCP control communication stopped")
        self.process.terminate()
        self.process.join()

    @staticmethod
    def _tcp_loop(
        queue_send: multiprocessing.Queue,
        queue_receive: multiprocessing.Queue,
        address: Tuple[str, int],
    ):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(address)
        except ConnectionRefusedError as e:
            raise ConnectionRefusedError(f"Cannot reach Durin at {address}")

        logging.debug(f"TCP control communication connected to {address}")

        try:
            while True:
                command = queue_send.get()
                sock.send(command)
                data = sock.recv(512)
                queue_receive.put(data)
        except ConnectionResetError as e:
            raise ConnectionResetError("TCP control communication ended by Durin")


class UDPLink:
    """
    An UDPBuffer that silently buffers messages received over UDP into a queue.
    """

    def __init__(self, package_size: int = 512, buffer_size: int = 2):
        self.buffer_size = buffer_size
        self.package_size = package_size
        self.buffer = multiprocessing.Queue(self.buffer_size)
        self.thread = multiprocessing.Process(
            target=self._loop_buffer,
            args=(self.buffer,),
        )

    def start_com(self, host: str, ip: int):
        self.thread.start()
        self.buffer.put((host, ip))  # Put address in queue

    def _loop_buffer(self, message_queue):
        count = 0
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        address = message_queue.get()
        sock.bind(address)

        logging.debug(f"UDP control receiving on {address}")

        try:
            while True:
                print("RECEIVING")
                buffer, _ = sock.recvfrom(self.package_size)
                print("BUFFER", buffer)
                sensor_id, reply = decode(buffer)
                print("RECEIVE", sensor_id, reply)
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
                    f"Could not connect to DVS controller at {self.address}", e
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
