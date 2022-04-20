from abc import abstractmethod
import ipaddress
import logging
import subprocess
import socket
from typing import Optional

from durin.controller import dvs


class Streamer:
    @abstractmethod
    def start_stream(self, host: str, port: int):
        pass

    @abstractmethod
    def stop_stream(self):
        pass


class AEStreamer(Streamer):
    def __init__(self) -> None:
        self.aestream = None
        # Test that cameras exist
        self.camera_string = dvs.identify_inivation_camera()
        # Test that aestream exists
        if subprocess.run(["which", "aestream"]).returncode > 0:
            raise ImportError("aestream could not be found")

    def start_stream(self, host: str, port: int):
        if self.aestream is not None:
            self.aestream.terminate()
        else:
            command = f"aestream input {self.camera_string} output spif {host} {port}"
            self.aestream = subprocess.Popen(command.split(" "))
            logging.info(f"Sending DVS to {host}:{port}")

    def stop_stream(self):
        if self.aestream:
            self.aestream.terminate()


class DVSServer:
    def __init__(
        self, port: int, buffer_size: int = 32, streamer: Optional[Streamer] = None
    ) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("0.0.0.0", port))
        self.sock.listen(1)
        self.buffer_size = buffer_size
        self.streamer = streamer if streamer is not None else AEStreamer()
        self.is_streaming = False

    def listen(self):
        self.is_streaming = True
        connection, address = self.sock.accept()
        while self.is_streaming:
            msg = connection.recv(self.buffer_size)
            if msg:
                self._parse_command(msg)

    def close(self):
        self.is_streaming = False
        self.sock.close()

    def _parse_command(self, data):
        if data[0] == 0:  # Start streaming
            host_ip = ipaddress.ip_address(data[1:5])
            port = int.from_bytes(data[5:7], "little")
            logging.debug(f"Streaming to {host_ip}:{port}")
            self.streamer.start_stream(str(host_ip), port)
        else:  # Stop streaming
            logging.debug(f"Terminating streaming")
            self.streamer.stop_stream()


if __name__ == "__main__":
    server = DVSServer(3000)
    server.listen()
