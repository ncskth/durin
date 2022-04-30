import usb.core

INIVATION_VENDOR_ID = 5419


def identify_inivation_camera():
    camera = usb.core.find(idVendor=5418)
    if camera is None:
        raise RuntimeError("No inivation camera connected")
    else:
        return f"inivation {camera.bus} {camera.address} dvx"


if __name__ == "__main__":
    print(identify_inivation_camera())
