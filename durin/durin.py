import logging
import multiprocessing
import sys
from typing import Optional, Tuple

from .actuator import DurinActuator
from .sensor import DurinSensor, Observation
from .network import TCPLink, UDPLink
from .common import *
from .cli import *

DURIN_CONTROLLER_PORT_TCP = 1337
DURIN_CONTROLLER_PORT_UDP = 4305

DURIN_DVS_PORT_TCP = 2301


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
        sensor_frequency (int): The update frequency of the sensor information in ms. Defaults to 10ms.
        spawn_cli (bool): Whether to spawn a background command line interface (CLI) in the terminal for manual interaction. Defaults to True.
        disable_dvs (bool): Disables connection to DVS. Useful if necessary libraries are not installed. Defaults to False.
    """

    def __init__(
        self,
        durin_ip: str,
        device: str = "cpu",
        stream_command: Optional[StreamOn] = None,
        sensor_frequency: int = 15,
        spawn_cli: bool = True,
        disable_dvs: bool = False
    ):
        if stream_command is not None:
            self.stream_command = stream_command
        else:
            response_ip = get_ip()
            self.stream_command = StreamOn(
                response_ip, DURIN_CONTROLLER_PORT_UDP, sensor_frequency
            )

        # Controller
        self.tcp_link = TCPLink(durin_ip, DURIN_CONTROLLER_PORT_TCP)
        self.udp_link = UDPLink()
        self.sensor = DurinSensor(self.udp_link)
        self.actuator = DurinActuator(self.tcp_link)

        # DVS
        self.disable_dvs = disable_dvs
        if not disable_dvs:
            import dvs
            ip_list = durin_ip.split(".")
            dvs_ip = ".".join(ip_list[:-1]) + f".{int(ip_list[-1]) + 10}"
            self.dvs_client = dvs.DVSClient(dvs_ip, DURIN_DVS_PORT_TCP)
            self.dvs = dvs.DVSSensor((640, 480), device, self.stream_command.port + 1)
        else:
            logging.debug("DVS output disabled")

        # CLI
        self.spawn_cli = spawn_cli
        std_in = sys.stdin.fileno()
        self.cli_process = multiprocessing.Process(
            target=run_cli, args=(self.actuator, std_in)
        )

    def __enter__(self):
        # Controller
        self.tcp_link.start_com()
        logging.debug(f"Durin Controller sending to {self.tcp_link.address}")
        self.udp_link.start_com(self.stream_command.host, self.stream_command.port)
        self(self.stream_command)
        logging.debug(
            f"Durin Controller receiving on {self.stream_command.host}:{self.stream_command.port}"
        )

        # DVS
        if not self.disable_dvs:
            self.dvs.start_stream()
            logging.debug(f"Durin DVS sending to {self.dvs_client.address}")
            self.dvs_client.start_stream(
                self.stream_command.host, self.stream_command.port + 1
            )
            logging.debug(
                f"Durin DVS receiving on {self.stream_command.host}:{self.stream_command.port + 1}"
            )

        # CLI
        if self.spawn_cli:
            self.cli_process.start()
        return self

    def __exit__(self, e, b, t):
        self.tcp_link.stop_com()
        self.udp_link.stop_com()
        if not self.disable_dvs:
            self.dvs_client.stop_stream()
            self.dvs.stop_stream()

        if self.spawn_cli:
            self.cli_process.kill()
            self.cli_process.join()

    def __call__(self, command):
        return self.actuator(command)

    def update_frequency(self) -> float:
        return 1 / self.sensor.freq / 6

    def read(self):
        """
        Retrieves sensor data from Durin

        Returns:
            Tuple of Observation, DVS tensors, and Command reply
        """
        durin = self.sensor.read()
        dvs = self.dvs.read() if self.disable_dvs is not None else None
        cmd = self.actuator.read()
        return (durin, dvs, cmd)
