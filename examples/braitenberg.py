import norse
import torch

from durin import *

if __name__ == "__main__":

    # First, we create a small simple Braitenberg vehicle with Norse
    # - https://en.wikipedia.org/wiki/Braitenberg_vehicle
    network = norse.torch.LICell(p=norse.torch.LIParameters(tau_mem_inv=100))
    # Prepare an empty (default) neuron state for later updating
    network_state = None

    # We start a connection to the robot
    # and can now read from and write to the robot via the variable "durin"
    # Notice the UI class, which differs from the (more efficient) standalone Durin interface
    with DurinUI("durin5.local") as durin:
        # Loop until the user quits
        is_running = True
        while is_running:

            # Read a value from durin
            # - obs = Robot sensor observations
            # - dvs = Robot DVS data (if any)
            # - cmd = Robot responses to commands
            (obs, dvs, cmd) = durin.read()

            # We can now update our display with the observations
            durin.render_sensors(obs)

            # Read user input and quit, if asked (but without allowing the user to move)
            is_running = durin.read_user_input(allow_movement=False)

            # We can now update our neural network and send the actuator signal to Durin
            left_tof = obs.tof[1].mean()
            right_tof = obs.tof[6].mean()
            input_tensor = torch.tensor([left_tof, right_tof])

            # We normalize the ToF information to [0;1] and flip it numerically
            input_tensor = torch.tanh(input_tensor / 1e4) * -1 + 1

            # We then run the network (in inference mode)
            with torch.inference_mode():
                output, network_state = network(input_tensor, network_state)
                output = output * 30 # Scale the output
                left, right = output
                durin(Move(0, output.mean() * (left - right).sign(), left - right))
