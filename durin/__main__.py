import argparse

from durin.cli import run_cli
from durin.durin import Durin

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Durin control interface")
    parser.add_argument("host", type=str, help="IP address to durin")
    parser.add_argument(
        "--port",
        type=int,
        default="4000",
        help="Port to use on Durin. Defaults to 4000",
    )
    args = parser.parse_args()
    durin = Durin(args.host, args.port)
    run_cli(durin)
