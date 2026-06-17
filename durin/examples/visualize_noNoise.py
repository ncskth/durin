"""DVS visualization example that applies a light denoising filter."""

import argparse
import aestream
import os
import sys
import time
import cv2
import numpy as np
import subprocess
from scipy import sparse

# Allow running this file directly from source without installing the package.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

args = argparse.ArgumentParser()
args.add_argument('-d', '--durin', default='durin0.local', help='Durin IP')
args.add_argument('-p', '--port', type=int, default=4001, help='Port to fetch events')
args.add_argument('-r', '--record', action='store_true', help='Record events in sparse tensor format')
args.add_argument('--auto-stream', action='store_true', help='Start/stop DVS stream over SSH using start@<durin> and stop@<durin>')
args.add_argument('--noise-window', type=float, default=0.08, help='Keep pixels visible for this many seconds after the last event')
args.add_argument('--neighborhood-threshold', type=float, default=0.08, help='Time threshold for neighbors to be considered "hot"')
args.add_argument('--min-neighbors', type=int, default=1, help='Minimum hot neighbors required to keep a pixel (0=disable spatial filter)')
args = args.parse_args()


def apply_spatial_coherence_filter(frame, last_event_timestamp, current_time, neighborhood_threshold, min_neighbors):
    """
    Filter out isolated noise pixels by checking if they have hot neighbors.
    A pixel is kept only if it has at least min_neighbors pixels nearby that fired recently.
    
    Args:
        frame: Current event frame
        last_event_timestamp: Matrix of per-pixel last event times
        current_time: Current time
        neighborhood_threshold: Time threshold for neighbors to be considered "hot"
        min_neighbors: Minimum hot neighbors required to keep pixel
    
    Returns:
        filtered_frame: Frame with isolated noise removed
    """
    if min_neighbors == 0:
        return frame  # Disable spatial filter
    
    filtered_frame = frame.copy()
    h, w = frame.shape
    
    # Find pixels that are old (beyond noise_window) but check their neighbors
    for y in range(h):
        for x in range(w):
            if frame[y, x] == 0:
                continue
            
            # Count how many neighbors are "hot" (fired recently)
            hot_neighbors = 0
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue  # Skip self
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w:
                        time_since_neighbor = current_time - last_event_timestamp[ny, nx]
                        if time_since_neighbor <= neighborhood_threshold:
                            hot_neighbors += 1
            
            # If pixel doesn't have enough hot neighbors, it's isolated noise
            if hot_neighbors < min_neighbors:
                filtered_frame[y, x] = 0
    
    return filtered_frame


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
    
    # For Object Flow calculation (velocity of edges)
    prev_frame = None
    prev_time = None

    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)

    print("Press Ctrl+C to stop recording...")

    if args.auto_stream:
        try:
            subprocess.run(["ssh", f"start@{args.durin}"], check=True)
            print(f"DVS stream started on {args.durin}")
        except Exception as e:
            print(f"Unable to start DVS stream on {args.durin}: {e}")


    frame_viz = np.zeros((640,480, 3))
    last_event_timestamp = np.full((640, 480), -np.inf, dtype=np.float32)

    with aestream.UDPInput((640, 480), device='cpu', port=args.port) as stream:
        try:
            while True:
                loop_start = time.time()

                # Read frame from stream
                frame = stream.read()
                acc = 0.95 * acc + 0.05 * float(np.abs(frame).sum())

                # Keep only pixels that changed recently; this suppresses stale isolated noise.
                current_time = time.time() - start_time
                event_mask = (frame != 0)
                last_event_timestamp[event_mask] = current_time
                recent_mask = (current_time - last_event_timestamp) <= args.noise_window
                filtered_frame = np.where(recent_mask, frame, 0)

                # Apply spatial coherence filter: remove isolated noise pixels.
                filtered_frame = apply_spatial_coherence_filter(
                    filtered_frame,
                    last_event_timestamp,
                    current_time,
                    args.neighborhood_threshold,
                    args.min_neighbors,
                )

                # Compute Object Flow: measure velocity of warm regions between frames.
                flow_info = compute_object_flow(prev_frame, filtered_frame, prev_time, current_time)

                # Store for next iteration
                prev_frame = filtered_frame.copy()
                prev_time = current_time

                # Store dense frame temporarily
                data.append(frame)
                timestamps.append(time.time() - start_time)

                # Robust bipolar visualization: positive events in green, negative in red.
                pos = np.clip(filtered_frame, 0, None)
                neg = np.clip(-filtered_frame, 0, None)
                if pos.max() > 0:
                    pos = (pos / pos.max()) * 255.0
                if neg.max() > 0:
                    neg = (neg / neg.max()) * 255.0
                frame_viz = np.zeros((frame.shape[0], frame.shape[1], 3), dtype=np.uint8)
                frame_viz[:, :, 1] = pos.astype(np.uint8)
                frame_viz[:, :, 2] = neg.astype(np.uint8)

                image = frame_viz.transpose(1, 0, 2)
                cv2.imshow(win_name, image)
                cv2.waitKey(1)

                # Print status with velocity info.
                status_str = (
                    f'Accumulated events: {acc:5f}, Loop time (ms): {1000*(time.time()-loop_start):5f}, '
                    f'raw_nonzero: {int(np.count_nonzero(frame))}, filtered_nonzero: {int(np.count_nonzero(filtered_frame))}'
                )
                if flow_info is not None:
                    status_str += f', Speed: {flow_info["speed"]:.1f} px/s'
                print(status_str, end='\r')

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
        finally:
            if args.auto_stream:
                try:
                    subprocess.run(["ssh", f"stop@{args.durin}"], check=True)
                    print(f"DVS stream stopped on {args.durin}")
                except Exception as e:
                    print(f"Unable to stop DVS stream on {args.durin}: {e}")