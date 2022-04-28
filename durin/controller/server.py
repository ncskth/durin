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

        command = f"aestream input {self.camera_string} output udp {host} {port}"
        self.aestream = subprocess.Popen(command.split(" "))
        logging.info(f"Sending DVS to {host}:{port}")

    def stop_stream(self):
        if self.aestream:
            self.aestream.terminate()
            self.aestream = None


class DVSServer:
    def __init__(
        self, port: int, buffer_size: int = 32, streamer: Optional[Streamer] = None
    ) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logging.debug(f"Listening to 0.0.0.0 {port}")
        self.sock.bind(("0.0.0.0", port))
        self.sock.listen(1)
        self.buffer_size = buffer_size
        self.streamer = streamer if streamer is not None else AEStreamer()
        self.is_streaming = False
        self.is_connected = False

    def listen(self):
        self.is_streaming = True
        while self.is_streaming:
            connection, address = self.sock.accept()
            logging.debug("New client connection established")
            self.is_connected = True
            self._client_loop(connection)

    def close(self):
        self.is_streaming = False
        self.sock.close()

    def _client_loop(self, connection):
        try:
            while self.is_connected:
                msg = connection.recv(self.buffer_size)
                if msg:
                    self._parse_command(msg)
        except ConnectionResetError:
            pass

    def _parse_command(self, data):
        if data[0] == 0:  # Start streaming
            host_ip = ipaddress.ip_address(int.from_bytes(data[1:5], "little"))
            port = int.from_bytes(data[5:7], "little")
            logging.debug(f"Streaming to {host_ip}:{port}")
            self.streamer.start_stream(str(host_ip), port)
        else:  # Stop streaming
            logging.debug(f"Terminating streaming")
            self.streamer.stop_stream()
            self.is_connected = False


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    server = DVSServer(2300)
    try:
        server.listen()
    finally:
        server.close()
