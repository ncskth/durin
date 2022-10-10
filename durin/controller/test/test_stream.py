from multiprocessing import Process
import multiprocessing
from time import sleep
from durin.controller import server
from durin.io import network
from durin.io.command import StreamOff, StreamOn


class MockStreamer(server.Streamer):
    def __init__(self, queue: multiprocessing.Queue) -> None:
        self.queue = queue

    def start_stream(self, host: str, port: int):
        self.queue.put(f"{host}:{port}")

    def stop_stream(self):
        self.queue.put("stop")


def test_handshake():
    q = multiprocessing.get_context("spawn").Queue(10)
    serv = server.DVSServer(3000, streamer=MockStreamer(q))
    serv.start()
    sleep(0.2)
    b = network.TCPLink("0.0.0.0", 3000)
    b.start()
    sleep(0.2)
    b.send(StreamOn("0.0.0.0", 3001, 1).encode(), 10)
    sleep(0.2)
    assert q.get(timeout=1) == "[0, 0, 0, 0]:3001"

    b.send(StreamOff().encode(), 10)
    sleep(0.2)
    assert q.get() == "stop"
    serv.stop()
    b.stop()
