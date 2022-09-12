import numpy as np

from durin.io.ringbuffer import RingBuffer


def test_ringbuffer():
    b = RingBuffer(np.zeros((5, 2)))
    assert b.counter == 0
    assert b.buffer.mean() == 0
    for i in range(10):
        b.append(np.array([1, 2])).mean(0)

    assert np.allclose(b.buffer, np.array([[1, 2], [1, 2], [1, 2], [1, 2], [1, 2]]))
    assert b.buffer.mean() == 1.5
