from durin.actuator import *
from durin.network import TCPLink

t = TCPLink("127.0.0.1", 2300)
t.start_com()

reply = t.send(MoveRobcentric(1, 2, 3).encode())
print(reply)

reply = t.send(MoveRobcentric(1, 2, 3).encode())
print(reply)

reply = t.send(MoveRobcentric(1, 2, 3).encode())
print(reply)

reply = t.send(MoveRobcentric(1, 2, 3).encode())
print(reply)

t.stop_com()
