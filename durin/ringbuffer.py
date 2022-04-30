import numpy as np


class RingBuffer(object):
    def __init__(self, shape=(50, 3)):
        self.size = shape[0]
        self.buffer = np.zeros(shape, dtype=np.float32)
        self.counter = 0

    def append(self, data):
        self.buffer[self.counter] = data
        self.counter += 1
        self.counter = self.counter % self.size
        return self.buffer


if __name__ == "__main__":
    b = RingBuffer((5, 2))
    print(b.append(np.array([1, 2])).mean(0))
    print(b.append(np.array([1, 2])).mean(0))
    print(b.append(np.array([1, 2])).mean(0))
    print(b.append(np.array([1, 2])).mean(0))
    print(b.append(np.array([1, 2])).mean(0))
    print(b.append(np.array([1, 2])).mean(0))
    print(b.append(np.array([1, 2])).mean(0))
    print(b.append(np.array([1, 2])).mean(0))
    print(b.append(np.array([1, 2])).mean(0))
    print(b.append(np.array([1, 2])).mean(0))

    buffers = [
        RingBuffer((5, 3)),
        RingBuffer((5, 3)),
        RingBuffer((5, 3)),
    ]
    print(buffers)
    buffers = [
        RingBuffer((5, 3)),
    ] * 3
    print(buffers)
