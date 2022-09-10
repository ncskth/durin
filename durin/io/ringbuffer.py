import numpy as np


class RingBuffer(object):
    def __init__(self, array: np.ndarray):
        self.size = len(array)
        self.buffer = array
        self.counter = 0

    def append(self, data):
        self.buffer[self.counter] = data
        self.counter += 1
        self.counter = self.counter % self.size
        return self.buffer
