import argparse
import os
import sys
import numpy as np
import functools
import time
import curses

from durin.actuator import Move

from durin.actuator import *


def parse(command: str, actuator: DurinActuator) -> str:
    try:
        out = eval(command)
        if isinstance(out, Command):
            reply = actuator(out)
            if reply is not None:
                return reply
            else:
                return "N/A"
        else:
            return f"Unknown command {out}"
    except Exception as e:
        return str(e)


def run_cli(actuator, stdin=sys.stdin.fileno()):
    # TODO: Print list of commands

    try:
        fd = os.fdopen(stdin)
        screen = curses.initscr()
        curses.noecho()
        curses.cbreak()

        initmsg = "Durin robot control environment\nAvailable commands:\n\tMove(x,y,a)"
        screen.addstr(0, 0, initmsg)

        vs = ""
        i = 3
        linestart = "> "
        while True:
            # Refresh
            screen.addstr(i, 2, f"{linestart}{vs} ")
            screen.addstr(i, 2, f"{linestart}{vs}")
            screen.refresh()

            key = screen.getch()

            if key == curses.KEY_ENTER or int(key) == 10:
                if len(vs) > 0:
                    val = parse(vs, actuator)
                    vs = ""
                    screen.addstr(i + 1, 0, str(val))
                    i += 2
            elif int(key) == 65:  # Up
                actuator(Move(0, 500, 0))
            elif int(key) == 66:  # Down
                actuator(Move(0, -500, 0))
            elif int(key) == 68:  # Left
                actuator(Move(-500, 0, 0))
            elif int(key) == 67:  # Right
                actuator(Move(500, 0, 0))
            elif key == curses.KEY_BACKSPACE or int(key) == 127:
                vs = vs[:-1]
                actuator(Move(0, 0, 0))
            else:
                vs = vs + chr(key)
    except (Exception, KeyboardInterrupt) as e:
        pass
    finally:
        curses.nocbreak()
        curses.echo()
        curses.endwin()


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


if __name__ == "__main__":

    run_cli(lambda x: None)
