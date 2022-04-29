import argparse
import os
import sys
import numpy as np

from .actuator import *
from .common import *


def parse(command: str, actuator: DurinActuator):
    try:
        out = eval(command)
        if isinstance(out, Command):
            reply = actuator(out)
            print(reply)
        else:
            print(f"Unknown command {out}")
    except Exception as e:
        print(e)
    return True


def run_cli(actuator, stdin=sys.stdin.fileno()):
    print("Durin robot control environment")
    print("Available commands:")
    print("\t Move x y a")
    # TODO: Print list of commands
    sys.stdin = os.fdopen(stdin)

    try:
        while True:
            command = input("> ")

            if not parse(command, actuator):
                return
    except KeyboardInterrupt:
        print()


#### Figure out:


def parse_args():
    parser = argparse.ArgumentParser(description="Connect to Durin and exert control")

    parser.add_argument(
        "mode", type=str, help="Operating Mode: 'cli' or 'brain'", default="cli"
    )
    parser.add_argument(
        "--host", type=str, help="Durin's IP address", default="127.0.0.1"
    )
    parser.add_argument("--tcp", type=str, help="Durin's TCP port", default=2300)

    return parser.parse_args()


def show_content(filepath):
    with open(filepath) as fp:
        line = fp.readline()
        cnt = 1
        while line:
            print(f"cmd {line.strip()}")
            line = fp.readline()
            cnt += 1


def parse_line(cli_in):

    cmd_id = 0
    command = ""
    arg_nb = 0
    arg_array = []
    isvalid = False

    # List of available commands
    filepath = "commands.txt"

    # Ignore 'enter'
    if len(cli_in) > 0:

        # Break line into 'words' (i.e. command + arguments) and count arguments
        cli_in = cli_in.split()
        command = cli_in[0]
        arg_nb = len(cli_in) - 1
        arg_array = cli_in[1 : arg_nb + 1]

        # Check if line command matches any available command
        if command == "list":
            show_content(filepath)
        else:
            with open(filepath) as fp:
                while True:
                    line = fp.readline()
                    if not line:
                        break
                    line = line.split()

                    # Check if requested command matches current available one
                    if command == line[1]:
                        # Check if #args makes sense
                        if len(line) == 2 + len(arg_array):
                            cmd_id = line[0]
                            isvalid = True
                            break
            if cmd_id == 0:
                cli_in = []
                print("Wrong Command/Arguments ...\n")

    arg_array = np.array(arg_array, dtype=float)

    return command, arg_array, isvalid
