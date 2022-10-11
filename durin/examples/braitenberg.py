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
            # - Take the center pixel of the 2nd sensor in a (8, 8) matrix
            left_tof = obs.tof[1, 3, 3]
            # - Take the center pixel of the 7th sensor in a (8, 8) matrix
            right_tof = obs.tof[6, 3, 3]

            # We normalize the ToF information to [0;1] and flip it numerically
            # (so, close = high values, far = low values)
            input_tensor = torch.tanh(torch.tensor([left_tof, right_tof]) / 1e3) * -1 + 1

            # We then run the network (in inference mode)
            with torch.inference_mode():
                # Update the network with the input and read the output
                output, network_state = network(input_tensor, network_state)
                output = output * 100 # Scale the output to fit motor range [0;500]
                left, right = output  # Separate left and right outputs
                command = MoveWheels(left, right, right, left)
                durin(command)  # Send the command to Durin
