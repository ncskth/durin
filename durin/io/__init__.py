from pathlib import Path
from typing import List

import capnp
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

schema = capnp.load(str((Path(__file__).parent.parent / "schema.capnp").absolute()))

def decode(buffer) -> List[schema.DurinBase]:
    # TODO: Use packed version later
    return next(schema.DurinBase.from_bytes(buffer).gen)
