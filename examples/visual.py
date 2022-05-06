import logging

from durin.actuator import *
from durin.durin import *
from durin.visuals import *

import pdb

logging.getLogger().setLevel(logging.DEBUG)


p_visual, dvs_np, tof_np, ev_count = launch_visual()
p_visual.start()

with Durin("172.16.223.95", stream_command=StreamOn("172.16.223.87", 4501, 100)) as durin:

    freq = 10 # Hz
    timestamp = time.time()
    acc = 0
    while True:
        (obs, dvs) = durin.read()


       
        if dvs.sum() > 100:
            dvs_np[:,:] = dvs.numpy()
        tof_np[:,:] = obs.tof[:,7*8:8*8]
        acc += dvs.sum()
        

        current = time.time()
        if current - timestamp > 1/freq:
            # time.sleep(current - timestamp - 1/freq)
            # print(f"Acc = {accum*freq} per s")
            ev_count.value = int(acc * freq)
            acc = 0
            timestamp = current

p_visual.join()