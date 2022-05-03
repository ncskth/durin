import logging

from durin.actuator import *
from durin.durin import *
from durin.visuals import *

import pdb

logging.getLogger().setLevel(logging.DEBUG)


p_visual, dvs_np = launch_visual()
p_visual.start()

with Durin("172.16.223.91") as durin:

    count = 0
    timestamp = time.time()
    while True:
        (obs, dvs) = durin.read()
        # dvs_np[:,:] = np.transpose(np.random.randint(0,2,(640,480)))
        dvs_np[:,:] = np.transpose(dvs.numpy())
        if count == 0: 
            print(dvs_np[:,:])
            count += 1
        
        current = time.time()
        if current - timestamp > 0.033:
            time.sleep(current - timestamp - 0.033)
            timestamp = current
        # print("OBS: ", dvs.sum(), obs.imu.mean())

p_visual.join()