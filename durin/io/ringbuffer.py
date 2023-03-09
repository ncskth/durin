import numpy as np


class RingBuffer(object):
    def __init__(self, array: np.ndarray, counter: int = 0):
        self.size = len(array)
        self.buffer = array
        self.counter = counter

    def append(self, data):
        self.buffer[self.counter] = data
        self.counter += 1
        self.counter = self.counter % self.size
        return self.buffer

    def get_oldest(self):
        return self.buffer[self.counter]

    def get_newest(self):
        return self.buffer[(self.counter - 1 ) % self.size]

