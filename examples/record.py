import logging
import time

import torch

from durin.actuator import *
from durin.common import SENSORS
from durin.durin import Durin
from durin.visuals import launch_visual

# logging.getLogger().setLevel(logging.DEBUG)

def cmd(x):
    x = torch.sin(torch.as_tensor(x)) * 200
    return Move(0, x, 0)

with Durin("172.16.223.95") as durin:

    tensors = []
    time_start = time.time()

    while True:
        (obs, tensor, cmd) = durin.read()
        tensors.append(tensor)

        # Pause to loop at 200Hz
        time.sleep(0.005)
        
        time_now = time.time()
        diff = time_now - time_start
        durin(cmd(diff))
        if time_now - time_start >= 10:
            break
    
    video = torch.stack(tensors)
    torch.save(video, "moving.dat")
