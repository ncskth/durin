import logging
from typing import Optional

from durin.actuator import StreamOn
from durin.actuator import DurinActuator
from durin.io.network import TCPLink, UDPLink
from durin.sensor import DurinSensor
import durin.io

DURIN_CONTROLLER_PORT_TCP = 1337
DURIN_CONTROLLER_PORT_UDP = 1338

DURIN_DVS_PORT_TCP = 2300


class Durin:
    """
    Interface to the Durin robot.
    This class first establishes connection to the controller and DVS system on board the robot.
    Afterwards, commands can be sent to the robot and sensory data can be `.read` from the robot.

    Note that the sensor observation is described in the sensor.Observation class.
    The DVS output is a 640x480 PyTorch tensor (if the aestream dependency is installed).

    Example:

    >>> with Durin(10.0.0.1) as durin:
    >>>   while True:
    >>>     observation, dvs = durin.read()
    >>>     ...
    >>>     durin(Move(x, y, rot))

    Arguments:
        durin_ip (str): The IPv4 address of the Durin microcontroller
        device (str): The PyTorch device to use for storing tensors. Defaults to cpu
        stream_command (Optional[StreamOn]): The command sent to the Durin microcontroller upon start. Can be customized, but uses sensible values by default.
        sensor_frequency (int): The update frequency of the sensor information in ms. Defaults to 15ms.
        enable_control (bool): Enables Durin sensors and control. Useful for testing without sending commands. Defaults to True.
        enable_dvs (bool): Enables Durin DVS data. Requires the aestream dependency AND a mounted DVS camera on Durin. Defaults to False.
    """

    def __init__(
        self,
        durin_ip: str,
        device: str = "cpu",
        stream_command: Optional[StreamOn] = None,
        sensor_frequency: int = 15,
        enable_control: bool = True,
        enable_dvs: bool = False,
    ):
        if stream_command is not None:
            self.stream_command_control = stream_command
            self.stream_command_dvs = StreamOn(stream_command.host, DURIN_DVS_PORT_TCP + 1)
        else:
            response_ip = durin.io.network.get_ip(durin_ip)
            self.stream_command_control = StreamOn(
                response_ip, DURIN_CONTROLLER_PORT_UDP
            )
            self.stream_command_dvs = StreamOn(response_ip, DURIN_DVS_PORT_TCP + 1)

        # Controller
        self.enable_control = enable_control
        if self.enable_control:
            tcp_link = TCPLink(durin_ip, DURIN_CONTROLLER_PORT_TCP)
            udp_link = UDPLink(self.stream_command_control.host, self.stream_command_control.port)
            self.sensor = DurinSensor(udp_link)
            self.actuator = DurinActuator(tcp_link)
            
        # DVS
        self.enable_dvs = enable_dvs
        if self.enable_dvs:
            import durin.dvs as dvs

            self.dvs_client = TCPLink(durin_ip, DURIN_DVS_PORT_TCP)
            self.dvs = dvs.DVSSensor((640, 480), device, DURIN_DVS_PORT_TCP + 1)
        else:
            logging.debug("DVS output disabled")

    def __enter__(self):
        # Controller
        if self.enable_control:
            self.sensor.start()
            self.actuator.start()
            # Start streaming
            self(self.stream_command_control)

            logging.debug(
                f"Durin Controller receiving on {self.stream_command_control.host}:{self.stream_command_control.port}"
            )

        # DVS
        if self.enable_dvs:
            self.dvs.start_stream()
            self.dvs_client.start()
            self.dvs_client.send(self.stream_command_dvs.encode(), 1000)
            logging.debug(
                f"Durin DVS receiving on {self.stream_command_dvs.host}:{self.stream_command_dvs.port + 1}"
            )

        return self

    def __exit__(self, e, b, t):
        if self.enable_control:
            self.sensor.stop()
            self.actuator.stop()
        if self.enable_dvs:
            self.dvs_client.stop()
            self.dvs.stop_stream()

    def __call__(self, command):
        if self.enable_control:
            return self.actuator(command)
        else:
            logging.warn(f"Command {command} sent, but Durin controls are disabled")

    def update_frequency(self) -> float:
        return 1 / self.sensor.freq / 6

    def read(self):
        """
        Retrieves sensor data from Durin

        Returns:
            Tuple of Observation, DVS tensors, and Command reply
        """
        dvs = self.dvs.read() if self.enable_dvs else None
        obs = self.sensor.read() if self.enable_control else None
        cmd = self.actuator.read() if self.enable_control else None
        return (obs, dvs, cmd)
