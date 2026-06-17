import durin

def test_sensor_period():
    cmd = durin.SetSensorPeriod("tof", 10)
    cmd.encode() # TODO: Test this properly