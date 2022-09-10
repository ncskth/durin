import multiprocessing
import time
from durin.io.runnable import RunnableProducer


class MockProducer(RunnableProducer):
    def __init__(self, queue):
        self.has_processed = multiprocessing.get_context("spawn").Event()
        super().__init__(queue, self.has_processed)

    def produce(self, has_processed):
        has_processed.set()
        return "bob"


def test_consumer():
    q = multiprocessing.get_context("spawn").Queue(1)
    c = MockProducer(q)
    c.start()
    time.sleep(1)
    c.stop()
    assert q.get() == "bob"
    assert c.has_processed.is_set()
