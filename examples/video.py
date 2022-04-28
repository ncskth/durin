import logging
import time

import matplotlib.pyplot as plt

import torch

from durin.actuator import *
from durin.common import SENSORS
from durin.durin import Durin
from durin.visuals import launch_visual

## Example modified from: https://matplotlib.org/stable/tutorials/advanced/blitting.html

# Initialize our canvas
fig, ax = plt.subplots()
image = ax.imshow(torch.zeros(260, 346), cmap="gray", vmin=0, vmax=1)
plt.show(block=False)
plt.pause(0.1)
bg = fig.canvas.copy_from_bbox(fig.bbox)
ax.draw_artist(image)
fig.canvas.blit(fig.bbox)

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)

    with Durin("localhost", "172.16.223.239") as durin:

        while True:
            (obs, tensor) = durin.sense()

            # Redraw figure
            fig.canvas.restore_region(bg)
            image.set_data(tensor.T.numpy())
            ax.draw_artist(image)
            fig.canvas.blit(fig.bbox)
            fig.canvas.flush_events()

            # Pause to only loop 10 times per second
            plt.pause(0.01)

            time.sleep(0.01)
