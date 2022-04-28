import argparse

from durin.actuator import *
from durin.durin import Durin


def parse(command: str, durin: Durin):
    try:
        out = eval(command)
        if isinstance(out, Command):
            durin(out)
        else:
            print(f"Unknown command {out}")
    except Exception as e:
        print(e)
    return True


def main(args):
    durin = Durin(args.host, args.port)

    print("Durin robot control environment")
    print("Available commands:")
    print("\t Move x y a")

    try:
        while True:
            command = input("> ")
            if not parse(command, durin):
                return
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Durin control interface")
    parser.add_argument("host", type=str, help="IP address to durin")
    parser.add_argument(
        "--port", type=int, default="4000", help="Port to use on Durin. Defaults to 4000", 
    )
    args = parser.parse_args()
    main(args)
