import logging

from durin.actuator import *
from durin.durin import *
from durin.visuals import *

import pdb

logging.getLogger().setLevel(logging.DEBUG)


p_visual, dvs_np, tof_np, ev_count = launch_visual()
p_visual.start()

with Durin("172.16.224.XX", disable_dvs=True) as durin:

    
    tof_nb = 0 # Select a TimeOfFlight sensor (0 to 7)
    while True:
        (obs, dvs, cmd) = durin.read()        
        tof_np[:,:] = obs.tof[:,tof_nb*8:(tof_nb+1)*8]

p_visual.join()