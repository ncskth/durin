from abc import abstractmethod
import logging
import multiprocessing
import subprocess
import socket
from typing import Optional

from durin.controller import dvs
from durin.io import decode
from durin.io.network import TCPProducer
from durin.io.runnable import Runnable, RunnableConsumer

logging.getLogger().setLevel(logging.DEBUG)


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
        # Test that aestream exists
        if subprocess.run(["which", "aestream"]).returncode > 0:
            raise RuntimeError("No aestream binary found on path")
        # Test that cameras exist
        try:
            self.camera_string = dvs.identify_inivation_camera()
        except RuntimeError as e:
            logging.warning("No DVX camera found on startup", e)

    def start_stream(self, host: str, port: int):
        if self.aestream is not None:
            self.stop_stream()

        # Get the camera string
        try:
            self.camera_string = dvs.identify_inivation_camera()
            logging.debug(f"Camera found at {self.camera_string}")
        except Exception as e:
            logging.warning("No camera found", e)
            return

        host_ip = ".".join([str(i) for i in host])
        command = f"aestream input {self.camera_string} output udp {host_ip} {port}"
        self.aestream = subprocess.run(
            command.split(" "),
            capture_output=True,  # stderr=subprocess.STDOUT, stdout=subprocess.PIPE
        )

        logging.debug(f"Sending DVS to {host}:{port} with command\n\t{command}")

    def stop_stream(self):
        try:
            if self.aestream is not None:
                self.aestream.terminate()
                self.aestream.wait(1)
                self.aestream.kill()
                self.aestream.wait()
            subprocess.run(["pkill", "aestream"])  # Kill remaining aestream processes
            self.aestream = None
        except Exception as e:
            logging.warning("Error when closing aestream", e)


class DVSServer(Runnable):
    def __init__(self, port: int, streamer: Optional[Streamer] = None) -> None:
        super().__init__(port)
        context = multiprocessing.get_context("spawn")
        self.buffer = context.Queue(10)
        self.streamer = streamer if streamer is not None else AEStreamer()
        self.consumer = DVSCommandConsumer(self.buffer, self.streamer)
        self.clients = []
        self.is_streaming = True

    def run(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("0.0.0.0", port))
            sock.listen(1)
            connection, _ = sock.accept()
            self.close_clients()

            producer = TCPProducer(self.buffer, connection)
            producer.start()
            producer.thread.join()
        except TimeoutError:
            pass
        finally:
            sock.close()

    def start(self):
        super().start()
        self.consumer.start()

    def stop(self):
        super().stop()
        self.close_clients()
        self.consumer.stop()

    def close_clients(self):
        logging.debug(f"Closing {len(self.clients)} old clients")
        for thread in self.clients:
            thread.close()
        self.clients = []


class DVSCommandConsumer(RunnableConsumer):
    def consume(self, bs, streamer: AEStreamer):
        if bs is None or len(bs) == 0:
            return
        d = decode(bs)
        if d.which == "enableStreaming":
            destination = d.enableStreaming.destination.udpOnly
            ip = destination.ip
            port = destination.port
            streamer.start_stream(ip, port)
        elif d.which == "disableStreaming":
            streamer.stop_stream()
        else:
            logging.warn("Unknown command received", d.which)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    server = DVSServer(2300)
    try:
        server.start()
        server.thread.join()
    finally:
        server.stop()
