from multiprocessing import Process
import multiprocessing
from time import sleep
from durin.controller import server
from durin.io import network
from durin.io.command import StreamOn


class MockStreamer(server.Streamer):
    def __init__(self, queue: multiprocessing.Queue) -> None:
        self.queue = queue

    def start_stream(self, host: str, port: int):
        self.queue.put(f"{host}:{port}")

    def stop_stream(self):
        self.queue.put("stop")


def start_server(port: int):
    q = multiprocessing.Queue(10)
    a = server.DVSServer(port, streamer=MockStreamer(q))
    p = Process(target=a.listen, )
    p.daemon = True
    p.start()
    return a, p, q


def test_handshake():
    serv, proc, q = start_server(3000)
    sleep(0.2)
    b = network.TCPLink("localhost", 3002)
    b.send(StreamOn("0.0.0.0", 3001, 1), 10)
    sleep(0.2)
    assert q.get() == "0.0.0.0:3001"

    b.stop_stream()
    sleep(0.2)
    assert q.get() == "stop"
    
    serv.close()
    proc.terminate()
    proc.join()
