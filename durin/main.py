from dataclasses import dataclass
from typing import List, Optional

from durin import Durin

host = ""
port = 0

with Durin(host, port) as durin:
    while True:
        obs = durin.read()
        # ...
        durin.act(...)
