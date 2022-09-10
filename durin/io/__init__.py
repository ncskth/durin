import numpy as np

PORT_TCP = 1337
PORT_UDP = 2300

SENSORS = {
    "tof_a": 128,
    "tof_b": 129,
    "tof_c": 130,
    "tof_d": 131,
    "misc": 132,
    "uwb": 133,
}


def decode(buffer):

    reply = ""
    sensor_id = buffer[0]

    # Decoding ToF Sensors
    if int(sensor_id) >= SENSORS["tof_a"] and int(sensor_id) <= SENSORS["tof_d"]:
        tof = np.zeros((2, 8, 8))
        tof[0] = np.frombuffer(buffer, dtype="<H", offset=1, count=64).reshape((8, 8))
        tof[1] = np.frombuffer(buffer, dtype="<H", offset=1 + 64 * 2, count=64).reshape(
            (8, 8)
        )
        reply = tof

    # Decoding Miscelaneous Sensors
    if int(sensor_id) == SENSORS["misc"]:
        charge = int.from_bytes(buffer[1:2], "little")
        voltage = int.from_bytes(buffer[2:4], "little")
        imu = np.frombuffer(buffer, dtype="<h", offset=4, count=9).reshape((3, 3))
        reply = (charge, voltage, imu)

    # Decoding UWB Sensors
    if int(sensor_id) == SENSORS["uwb"]:
        nb_beacons = int.from_bytes(buffer[1:2], "little")
        uwb = np.frombuffer(buffer, dtype="<f", offset=2, count=nb_beacons)
        reply = uwb

    return sensor_id, reply
