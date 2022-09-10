from abc import abstractmethod
import multiprocessing
import queue
import time
from typing import Any


class Runnable:
    def __init__(self, *args):
        context = multiprocessing.get_context("spawn")
        self.event = context.Event()
        self.thread = context.Process(target=self._run_thread, args=(self.event, *args))

    @abstractmethod
    def run(self, *args):
        pass

    def _run_thread(self, *args):
        event = args[0]
        try:
            while not event.wait(0):
                self.run(*args[1:])
        except KeyboardInterrupt:
            pass

    def start(self):
        self.thread.start()

    def stop(self):
        self.event.set()
        self.thread.terminate()


class RunnableConsumer(Runnable):
    def __init__(self, queue, *args):
        super().__init__(*args)
        self.queue = queue

    @abstractmethod
    def consume(self, event, *args):
        pass

    def run(self, *args):
        try:
            item = self.queue.get(block=False)
            self.consume(item, *args)
        except queue.Empty:
            pass


class RunnableProducer(Runnable):
    def __init__(self, queue, args, blocking: bool = False):
        super().__init__(args)
        self.queue = queue
        self.blocking = blocking

    @abstractmethod
    def produce(self, *args) -> Any:
        pass

    def run(self, *args):
        try:
            value = self.produce(*args)
            if value is not None:
                self.queue.put(value, block=self.blocking)
        except queue.Full:
            pass
