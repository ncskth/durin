from abc import abstractmethod
import multiprocessing
from multiprocessing.sharedctypes import Value
import queue
import time
from typing import Any


class Runnable:
    def __init__(self, *args, context: str = "spawn", **kwargs):
        context = multiprocessing.get_context(context)
        self.event = context.Event()
        self.thread = context.Process(target=self._run_thread, args=(self.event, *args, *kwargs.values()))

    @abstractmethod
    def run(self, *args):
        pass

    def _run_thread(self, *args):
        event = args[0]
        try:
            while not event.wait(0):
                self.run(*args[1:])
        except ValueError:
            pass
        except KeyboardInterrupt:
            pass

    def start(self):
        self.thread.start()

    def stop(self):
        self.event.set()
        if self.thread.is_alive():
            self.thread.terminate()


class RunnableConsumer(Runnable):
    def __init__(self, queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue

    @abstractmethod
    def consume(self, item, *args):
        pass

    def run(self, *args):
        try:
            item = self.queue.get(block=False)
            if item is not None:
                self.consume(item, *args)
        except queue.Empty:
            pass


class RunnableProducer(Runnable):
    def __init__(self, queue, args, blocking: bool = False, **kwargs):
        super().__init__(args, **kwargs)
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
