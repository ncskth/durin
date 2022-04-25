import time, pdb

from dataclasses import dataclass
from typing import List, Optional
from durin import Durin
from examples import *
from actuator import *
from cli import parse_args



if __name__ == "__main__":

    args = parse_args()
    

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

                
        else:
            print("Wrong Mode")

