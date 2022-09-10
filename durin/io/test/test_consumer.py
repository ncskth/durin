import multiprocessing
import time
from durin.io.runnable import RunnableConsumer


class MockConsumer(RunnableConsumer):
    def __init__(self, queue):
        self.has_processed = multiprocessing.get_context("spawn").Event()
        super().__init__(queue, self.has_processed)

    def consume(self, event, has_processed):
        print("setting")
        has_processed.set()


def test_consumer():
    q = multiprocessing.get_context("spawn").Queue(1)
    q.put(1)
    c = MockConsumer(q)
    c.start()
    time.sleep(1)
    c.stop()
    assert c.has_processed.is_set()
