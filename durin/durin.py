from durin.actuator import Actuator
from durin.sensor import Sensor


class Durin(Actuator, Sensor):
    def __init__(self, host, port):
        # Start receiving thread in background
        pass


class MockDuring(Durin):
    pass
