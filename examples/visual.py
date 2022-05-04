import logging

from durin.actuator import *
from durin.durin import *
from durin.visuals import *

import pdb

logging.getLogger().setLevel(logging.DEBUG)


p_visual, dvs_np, tof_np = launch_visual()
p_visual.start()

with Durin("172.16.223.91", stream_command=StreamOn("172.16.223.60", 4501, 100)) as durin:

    count = 0
    timestamp = time.time()
    while True:
        (obs, dvs) = durin.read()
        # dvs_np[:,:] = np.transpose(np.random.randint(0,2,(640,480)))
        if dvs.sum() > 100:
            dvs_np[:,:] = dvs.numpy()
        tof_np[:,:] = obs.tof[:,7*8:8*8]
        # print(obs.tof[:,7*8:8*8])

        current = time.time()
        if current - timestamp > 0.033:
            time.sleep(current - timestamp - 0.033)
            timestamp = current

p_visual.join()