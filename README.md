# Durin control system

This repository contains Python code that interfaces with the robot Durin.
Please note that this is only the reference implementation for our interface. See below.

## Installation

We require GCC-10, [pip](https://pypi.org/project/pip/), [PyTorch](https://pytorch.org/), and [AEStream](https://github.com/norse/aestream/).

On Debian-like systems (like Ubuntu), you can install Durin with the following commands:
```bash
sudo apt install gcc-10 python3-pip
pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cpu
pip install git+https://github.com/norse/aestream
pip install git+https://github.com/ncskth/durin
```

## Usage

The interface is meant to be used via Python. More examples can be found in the `durin/examples` folder.


```python
from durin.actuator import *
from durin.durin import *

# The ip address to Durin is 172.16.223.9X, where X is the number of the robot (1, 2, or 5).
durin_ip = "172.16.223.91"

with Durin(durin_ip) as durin:

    while True:
        # Get observation
        (obs, dvs) = durin.read()

        # Do clever things...

        # Move durin 100 units left with 0 forward/backward motion and 0 rotation
        command = Move(100, 0, 0)

        # Send command to Durin
        durin(command)

        # ... this loop continues forever!
        # You can exit it on your computer by pressing CTRL+C
```

## Sensory data

The `durin.read()` method will give you access to 

1. An `Observation` object containing
    * `.tof` Time of Flight sensors
    * `.bat` Battery value
2. A 640x480 DVS [PyTorch](pytorch.org) tensor
    * This tensor has buffered/stacked events since the last `.read()` command.

## Commands
The most important command is `Move(x, y, rotation)`. the `x`, `y`, `rotation` values should be in the interval between [-500, 500].

## Custom implementation
You can interface to the microcontroller (sensor + wheel actuation) and DVS microcamera with TCP and UDP.
A complete specification is available via Google Drive: https://docs.google.com/spreadsheets/d/11jD30J00-03ygZ6zJaVTnjJRQKfczT-wMIdBdpYMxD4/edit?usp=sharing

## Contact

Reach out to Juan or Jens if you need anything

