import time
from durin import Durin, Move

if __name__ == "__main__":
    with Durin("durin1.local") as durin:
        while True:
            durin(Move(100, 0, 0))
            time.sleep(2)

