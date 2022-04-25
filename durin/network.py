import socket
import multiprocessing
from typing import ByteString
from common import *

class TCPLink:
    """
    
    """
    def __init__(self, host: str, port: str):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = (host, int(port))

    def start_com(self):
        print(f"TCP communication started with {self.address}")
        self.socket.connect(self.address)

    # Send Command to Durin and wait for response
    def send(self, command: ByteString):
        self.socket.send(command)
        # For PollAll we need to 'recv' more than once
        # @TODO: create a list of 'buffers'
        # 'decode' in 'common' needs to account for list of 'buffers' instead of a single buffer
        buffer = self.socket.recv(1024)

        return buffer


    def stop_com(self):
        print(f"TCP communication stopped with {self.address}")
        self.socket.close()
        
class UDPLink:
    """
    An UDPBuffer that silently buffers messages received over UDP into a queue.
    """

    def __init__(self, package_size: int = 1024, buffer_size: int = 1024):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.is_buffering = False 
        self.package_size = package_size
        self.buffer = multiprocessing.Queue(buffer_size)
        self.thread = multiprocessing.Process(target=self._loop_buffer)

    def start_com(self, address):
        print("Start UDP reception")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(address)
        self.thread.start()
        self.is_buffering = True

    def _loop_buffer(self):
        count = 0

        while True:
            try:
                buffer, _ = self.socket.recvfrom(512)
                sensor_id, reply = decode(buffer)
                self.buffer.put((sensor_id, reply), block=False)
            except:
                print("Problem receiving sensory data")
                break
            count += 1
            

    # get data from buffer
    def get(self):
        return self.buffer.get(block=False)

    def stop_com(self):
        self.is_buffering = False
        self.socket.close()
        self.thread.terminate()
        self.thread.join()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.thread = multiprocessing.Process(target=self._loop_buffer)


