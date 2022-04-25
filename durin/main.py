import time, pdb

from dataclasses import dataclass
from typing import List, Optional
from durin import Durin
from examples import *
from actuator import *
from cli import parse_args
from visuals import *

import multiprocessing 


if __name__ == "__main__":

    args = parse_args()

    # This starts the visualization of ToF sensor data
    p_visual, px_np = launch_visual()
    p_visual.start()
    

    with Durin(args.host, args.tcp) as durin:

        if args.mode == "cli":
            while True:
                cli_command = input()
                reply = durin(Request(cli_command))
                print(type(reply))
                print(reply)

            

        elif args.mode == "brain":

            pdb.set_trace()
            example_moving(durin)
            example_polling(durin)
            example_streaming(durin)
            example_streaming(durin, px_np, 10)

                
        else:
            print("Wrong Mode")


    p_visual.join()
