from abc import abstractmethod
from dataclasses import dataclass
from typing import ByteString, TypeVar
from pathlib import Path
from durin.io import SENSORS
from . import schema


def _wrap_base(message, field):
    base = schema.DurinBase.new_message()
    setattr(base, field, message)
    packed = base.to_bytes_packed()
    return packed


@dataclass
class Command:
    pass

    @abstractmethod
    def encode() -> ByteString:
        pass


class PowerOff(Command):
    def __init__(self):
        self.cmd_id = 1

    def encode(self):
        return _wrap_base(schema.PowerOff.new_message(), "powerOff")


class SetLed(Command):
    def __init__(self, red: int, green: int, blue: int):
        self.red = red
        self.green = green
        self.blue = blue

    def encode(self):
        return _wrap_base(
            schema.SetLed.new_message(ledR=self.red, ledG=self.green, ledB=self.blue),
            "setLed",
        )


class Move(Command):
    def __init__(self, vel_x: int, vel_y: int, rot: int):
        """
        Moves Durin

        Arguments:
            vel_x (int): Velocity in the x axis
            vel_y (int): Velocity in the y axis
            rot (int): Degrees per second
        """
        self.cmd_id = 2
        self.vel_x = int(vel_x)
        self.vel_y = int(vel_y)
        self.rot = int(rot)

    def encode(self):
        message = schema.SetRobotVelocity.new_message(
            velocityXMms=self.vel_x, velocityYMms=self.vel_y, rotationDegs=self.rot
        )
        return _wrap_base(message, "setRobotVelocity")

    def __repr__(self) -> str:
        return f"Move({self.vel_x}, {self.vel_y}, {-self.rot})"


class MoveWheels(Command):
    """
    Moves individual wheels on Durin. All units are in millimeters/second

    Arguments:
        front_left (float): Front left wheel
        front_right (float): Front right
        back_left (float): Back left wheel
        back_right (float): Back right wheel
    """

    def __init__(self, front_left, front_right, back_left, back_right):
        MAX_VALUE = 10000
        self.cmd_id = 3
        self.front_left = min(MAX_VALUE, int(front_left))
        self.front_right = min(MAX_VALUE, int(front_right))
        self.back_left = min(MAX_VALUE, int(back_left))
        self.back_right = min(MAX_VALUE, int(back_right))

    def encode(self):
        return _wrap_base(
            schema.SetWheelVelocity.new_message(
                wheelFrontLeftMms=self.front_left,
                wheelFrontRightMms=self.front_right,
                wheelBackLeftMms=self.back_left,
                wheelBackRightMms=self.back_right,
            ), "setWheelVelocity"
        )

    def __repr__(self) -> str:
        return f"MoveWheels({self.front_left}, {self.front_right}, {self.back_left}, {self.back_right})"


# class PollSensor(Command):
#     def __init__(self, sensor_id):
#         self.cmd_id = 17
#         self.sensor_id = int(sensor_id)

#     def encode(self):
#         data = bytearray([0] * 2)
#         data[0] = self.cmd_id
#         data[1:2] = self.sensor_id.to_bytes(
#             1, "little"
#         )  # integer (uint8) little endian

#         return data

class SetSensorPeriod(Command):

    _SUPPORTED_SENSORS = ["Tof", "Imu", "SystemStatus", "Position", "Uwb"]

    def __init__(self, sensor: str, period: int):
        """
        Sets how often a given sensor should report to the client in ms.
        """
        if not sensor in self._SUPPORTED_SENSORS:
            raise ValueError(f"Sensor '{sensor}' unsupported. Please choose from {self._SUPPORTED_SENSORS}")
        
        
        self.sensor = sensor
        self.period = period

    def encode(self):
        message_type = f"Set" + self.sensor + "StreamPeriod"

        message = getattr(schema, message_type).new_message()
        message.periodMs = self.period

        return _wrap_base(message, message_type[0].lower() + message_type[1:])


class StreamOn(Command):
    def __init__(self, host, port):
        self.cmd_id = 18
        self.host = host
        self.port = port

    def encode(self):
        enable_message = schema.EnableStreaming.new_message()
        udpOnly = enable_message.destination.init("udpOnly")
        udpOnly.ip = list(map(lambda x: int(x), self.host.split(".")))
        udpOnly.port = self.port
        return _wrap_base(enable_message, "enableStreaming")


class StreamOff(Command):
    def __init__(self):
        self.cmd_id = 19

    def encode(self):
        return _wrap_base(schema.DisableStreaming.new_message(), "disableStreaming")
