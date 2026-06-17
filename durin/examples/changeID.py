"""Example that connects over TCP and changes the robot node ID."""

import time

import durin.io as io
from durin.io.network import TCPLink
from durin.actuator import DurinActuator


def main():
    host, port = "172.16.222.110", 1337  # metti IP/porta del robot
    print(f"Connecting to {host}:{port}...")
    link = TCPLink(host, port)
    print(f"TCPLink created")
    act = DurinActuator(link)
    print(f"DurinActuator created")
    link.start()
    print(f"Link started")

    try:
        msg = io.schema.DurinBase.new_message() 
        msg.init("setNodeId").nodeId = 10
        link.send(msg.to_bytes_packed(), timeout=0.1)

        check = io.schema.DurinBase.new_message()
        check.init("getSystemInfo")
        link.send(check.to_bytes_packed(), timeout=0.1)

        reply = None
        deadline = time.time() + 2.0
        while time.time() < deadline:
            reply = act.read()
            if reply is not None:
                break
            time.sleep(0.02)

        print(reply)
    finally:
        link.stop()


if __name__ == "__main__":
    main()