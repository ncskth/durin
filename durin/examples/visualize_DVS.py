import aestream
from durin import *
import numpy as np 
import argparse
import time
import cv2
import math
import time
import math
import numpy as np
from scipy import sparse
import cv2


args = argparse.ArgumentParser()
args.add_argument('-d', '--durin', default='durin0.local', help='Durin IP')
args.add_argument('-p', '--port', default='4001', help='Port to fetch events')
args.add_argument('-r', '--record', action='store_true', help='Record events in sparse tensor format')
args = args.parse_args()

# ---------------------Event Streaming--------------------------
# Start event streaming from durin# by running: ssh start@durin# 
# Stop event streaming from durin# by running: ssh stop@durin# 


if __name__ == "__main__":

    win_name = "Durin DVS"
    npz_filename = "sparse_data.npz"

    data = []
    timestamps = []
    acc = 0
    start_time = time.time()

    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)

    print("Press Ctrl+C to stop recording...")


    frame_viz = np.zeros((640,480, 3))
    data = []
    with aestream.UDPInput((640, 480), device = 'cpu', port=args.port) as stream:
        with Durin(args.durin) as durin:
            try:
                while True:
                    loop_start = time.time()

                    # Read frame from stream
                    frame = stream.read()
                    acc = 0.95 * acc + 0.05 * frame.sum()

                    # Store dense frame temporarily
                    data.append(frame)
                    timestamps.append(time.time() - start_time)

                    frame_viz = np.zeros((frame.shape[0], frame.shape[1], 3), dtype=frame.dtype)
                    frame_viz[:, :, 1] = frame  # green channel for visualization

                    image = frame_viz.transpose(1, 0, 2)
                    cv2.imshow(win_name, image)
                    cv2.waitKey(1)

                    # Print status
                    print(f'Accumulated events: {acc:5f}, Loop time (ms): {1000*(time.time()-loop_start):5f}', end='\r')

            except KeyboardInterrupt:
                if args.record:
                    print("\nStopping capture and processing sparse data...")

                    sparse_rows = []

                    for t_idx, frame in enumerate(data):
                        coo = sparse.coo_matrix(frame)
                        if len(coo.data) > 0:
                            # Column for timestamp
                            time_col = np.full(len(coo.data), timestamps[t_idx])
                            # Stack as [t, x, y, q]
                            frame_sparse = np.vstack([time_col, coo.row, coo.col, coo.data]).T
                            sparse_rows.append(frame_sparse)

                    # Combine all frames
                    sparse_data_np = np.vstack(sparse_rows)
                    print(f"Sparse data shape: {sparse_data_np.shape}")

                    # Create structured array with column names
                    dtype = [('t', 'f8'), ('x', 'i4'), ('y', 'i4'), ('q', 'f4')]
                    structured_array = np.zeros(sparse_data_np.shape[0], dtype=dtype)
                    structured_array['t'] = sparse_data_np[:,0]
                    structured_array['x'] = sparse_data_np[:,1]
                    structured_array['y'] = sparse_data_np[:,2]
                    structured_array['q'] = sparse_data_np[:,3]

                    # Save compressed
                    np.savez_compressed(npz_filename, sparse_data=structured_array)
                    print(f"Sparse data saved to '{npz_filename}' ({structured_array.nbytes / 1e6:.2f} MB uncompressed)")