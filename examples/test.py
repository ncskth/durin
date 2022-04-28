from time import sleep
from durin.actuator import *
from durin.network import DVSClient, TCPLink
from durin.sensor import DVSSensor

#c = DVSClient("172.16.223.239", 3000)
s = DVSSensor((640, 480), "cpu", 4301)
while True:
    print(s.read().sum())
    sleep(0.1)