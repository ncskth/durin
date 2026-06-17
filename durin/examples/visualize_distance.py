"""Live distance and DVS visualization example with optional telemetry."""

# Run: python durin/examples/visualize_distance.py --durin durin0.local --stream-host durin0.local -p 4001 --auto-stream --use-telemetry


import argparse
import aestream
import os
import sys
import time
import threading
import socket
import cv2
import numpy as np
import subprocess
from scipy import sparse

# Allow running this file directly from source without installing the package.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from durin.durin import Durin
from durin.io.command import SetSensorPeriod, Move, StreamOn

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-d', '--durin', default='durin0.local', help='Durin IP')
arg_parser.add_argument('--stream-host', default=None, help='Host used only for ssh start@/stop@ stream control (defaults to --durin)')
arg_parser.add_argument('--control-stream-host', default=None, help='Local PC IPv4 used as UDP destination for control telemetry (overrides auto IP detection)')
arg_parser.add_argument('-p', '--port', type=int, default=4001, help='Port to fetch events')
arg_parser.add_argument('--auto-stream', action='store_true', help='Start/stop DVS stream over SSH using start@<durin> and stop@<durin>')
arg_parser.add_argument('--use-telemetry', action='store_true', help='Read obs/cmd from Durin to update ToF and IMU frequency online')
args = arg_parser.parse_args()

# Main tuning lives here so you can edit it directly without long CLI commands.
CONFIG = {
    'noise_window': 0.08,
    'neighborhood_threshold': 0.08,
    'min_neighbors': 1,
    'min_cluster_pixels': 50,
    'min_cluster_compactness': 0.08,
    'max_cluster_aspect_ratio': 7.0,
    'min_draw_cluster_area': 80,
    'max_clusters_drawn': 8,
    'draw_moving_only': False,
    'diagnostic_mode': False,
    'match_max_dist': 30.0,
    'focal_length_px': 533.33,
    'moving_speed_threshold': 0.05,
    'tof_min_mm': 30.0,
    'tof_max_mm': 4000.0,
    'tof_front_only': True,
    'tof_margin_px': 8,
    'tof_nearest_max_px': 160.0,
    'telemetry_stale_timeout': 1.0,
    'ssh_timeout': 2.0,
    'event_epsilon': 0.5,
    'max_active_ratio': 0.35,
    'min_event_epsilon': 0.5,
    'max_event_epsilon': 25.0,
    'background_alpha': 0.995,
    'use_background_subtraction': False,
    'zero_frame_warning_threshold': 120,
}

for key, value in CONFIG.items():
    setattr(args, key, value)

NEIGHBOR_KERNEL = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.uint8)

# Approximate fixed ToF projection points in DVS frame coordinates.
TOF_POINTS_NORMALIZED = [
    (0.25, 0.01),
    (0.02, 0.03),
    (0.02, 0.40),
    (0.02, 0.70),
    (0.25, 0.76),
    (0.41, 0.70),
    (0.45, 0.40),
    (0.41, 0.02),
]

# Front arc in the same order as TOF_POINTS_NORMALIZED / obs.tof.
TOF_FRONT_SENSOR_IDS = (7, 0, 1)


def compute_tof_distances_m(obs_tof, min_mm, max_mm):
    """Reduce each ToF sensor matrix to one robust distance value in meters."""
    tof = np.asarray(obs_tof)
    if tof.ndim != 3 or tof.shape[0] == 0:
        return [], None

    sensor_distances = []
    for i in range(tof.shape[0]):
        values = np.asarray(tof[i]).reshape(-1)
        valid = values[(values >= min_mm) & (values <= max_mm)]
        if valid.size == 0:
            sensor_distances.append(None)
        else:
            sensor_distances.append(float(np.median(valid) / 1000.0))

    all_values = tof.reshape(-1)
    valid_all = all_values[(all_values >= min_mm) & (all_values <= max_mm)]
    center_distance = float(np.median(valid_all) / 1000.0) if valid_all.size > 0 else None
    return sensor_distances, center_distance


def get_tof_projection_points(frame_h, frame_w):
    """Build per-sensor fixed pixel coordinates used for ToF-to-cluster association."""
    points = []
    for nx, ny in TOF_POINTS_NORMALIZED:
        px = int(round(nx * (frame_h - 1)))
        py = int(round(ny * (frame_w - 1)))
        points.append((px, py))
    return points


def distance_from_tof_for_cluster(cluster, tof_points, tof_distances_m, tof_center_m, margin_px=0, nearest_max_px=0.0, active_sensor_ids=None):
    """Assign cluster distance from ToF using bbox-hit first, then nearest-point fallback."""
    active_ids = set(active_sensor_ids) if active_sensor_ids is not None else None
    x, y, w, h = cluster["bbox"]
    cx, cy = cluster["centroid"]
    x0 = x - margin_px
    y0 = y - margin_px
    x1 = x + w + margin_px
    y1 = y + h + margin_px

    hits = []
    for i, (px, py) in enumerate(tof_points):
        if i >= len(tof_distances_m):
            continue
        if active_ids is not None and i not in active_ids:
            continue
        d = tof_distances_m[i]
        if d is None:
            continue
        if x0 <= px <= x1 and y0 <= py <= y1:
            hits.append({"sensor": i, "distance_m": float(d), "point": (px, py), "source": "bbox"})

    # Nearest valid ToF fallback when no point intersects the bbox.
    if not hits and nearest_max_px > 0.0:
        best = None
        for i, (px, py) in enumerate(tof_points):
            if i >= len(tof_distances_m):
                continue
            if active_ids is not None and i not in active_ids:
                continue
            d = tof_distances_m[i]
            if d is None:
                continue
            dist_px = float(np.hypot(cx - px, cy - py))
            if best is None or dist_px < best[0]:
                best = (dist_px, i, px, py, float(d))
        if best is not None and best[0] <= nearest_max_px:
            hits.append({
                "sensor": best[1],
                "distance_m": best[4],
                "point": (best[2], best[3]),
                "source": "nearest",
                "dist_px": round(best[0], 1),
            })

    # Center fallback for objects crossing the image center.
    if active_ids is not None:
        selected = [tof_distances_m[i] for i in active_ids if i < len(tof_distances_m) and tof_distances_m[i] is not None]
        center_candidate_m = float(np.median(selected)) if selected else None
    else:
        center_candidate_m = tof_center_m

    if not hits and center_candidate_m is not None:
        center_x = 640 / 2.0
        center_y = 480 / 2.0
        if abs(cx - center_x) < 25 and abs(cy - center_y) < 25:
            hits.append({"sensor": "center", "distance_m": float(center_candidate_m), "point": (int(center_x), int(center_y)), "source": "center"})

    if not hits:
        return None, []
    return float(min(h["distance_m"] for h in hits)), hits


def summarize_clusters_for_log(clusters, max_items=3):
    """Build a compact human-readable summary of the most relevant clusters."""
    if not clusters:
        return "<no clusters>"

    lines = []
    for cluster in clusters[:max_items]:
        bbox = cluster["bbox"]
        centroid = cluster["centroid"]
        z_est = cluster.get("z_est")
        flow_u = cluster.get("flow_u", 0.0)
        obstacle_speed_mps = cluster.get("obstacle_speed_mps")
        moving = cluster.get("independent_motion", False)
        hits = cluster.get("tof_hits", [])
        lines.append(
            f"id={cluster['track_id']} bbox={bbox} centroid=({centroid[0]:.1f},{centroid[1]:.1f}) "
            f"tof_hits={hits} Z={('n/a' if z_est is None else f'{z_est:.2f}m')} "
            f"u={flow_u:+.1f}px/s v_obj={('n/a' if obstacle_speed_mps is None else f'{obstacle_speed_mps:.2f}m/s')} "
            f"moving={moving}"
        )
    if len(clusters) > max_items:
        lines.append(f"... +{len(clusters) - max_items} more")
    return " | ".join(lines)


def telemetry_loop(stop_event, shared, lock):
    """Continuously read robot telemetry (IMU frequency and ToF) and share it thread-safely."""

    print(f"[telemetry] starting on {args.durin}")
    with lock:
        shared["thread_state"] = "starting"
        shared["updated_at"] = time.time()

    try:
        stream_host = args.control_stream_host
        if stream_host:
            try:
                socket.inet_aton(stream_host)
            except OSError:
                print(
                    f"[telemetry] --control-stream-host '{stream_host}' is not a valid IPv4 address. "
                    "Ignoring override and using auto interface detection."
                )
                stream_host = None

        attempts = []
        if stream_host:
            attempts.append(("forced", StreamOn(stream_host, 1338)))
        attempts.append(("auto", None))

        durin = None
        last_construct_error = None
        for attempt_name, stream_command in attempts:
            try:
                if stream_command is not None:
                    print(f"[telemetry] forcing control stream destination to {stream_host}:1338")
                durin = Durin(args.durin, stream_command=stream_command, enable_control=True, enable_dvs=False)
                print(f"[telemetry] Durin construction OK ({attempt_name})")
                break
            except OSError as e:
                last_construct_error = e
                if getattr(e, "errno", None) == 99 and attempt_name == "forced":
                    print(
                        f"[telemetry] bind failed for forced host {stream_host}: {e}. "
                        "Retrying with auto interface detection."
                    )
                    continue
                raise

        if durin is None:
            raise RuntimeError(f"Unable to construct telemetry client: {last_construct_error}")

        print("[telemetry] Durin object constructed")

        durin.sensor.start()
        print("[telemetry] sensor started")

        durin.actuator.start()
        print("[telemetry] actuator started")

        durin(durin.stream_command_control)
        print("[telemetry] control stream command sent")

        # Request frequent IMU/ToF updates so telemetry reflects real motion.
        try:
            durin(SetSensorPeriod("Imu", 20))
            durin(SetSensorPeriod("Tof", 50))
            durin(SetSensorPeriod("SystemStatus", 500))
        except Exception as e:
            print(f"[telemetry] sensor period setup failed: {e}")

        with lock:
            shared["thread_state"] = "running"
        print("[telemetry] entering read loop")

        while not stop_event.is_set():
            try:
                obs, _, _ = durin.read()
                now = time.time()

                tof_distances_m, tof_center_m = compute_tof_distances_m(obs.tof, args.tof_min_mm, args.tof_max_mm)

                with lock:
                    shared["imu_freq_hz"] = obs.imu_frequency
                    shared["tof_distances_m"] = tof_distances_m
                    shared["tof_center_m"] = tof_center_m
                    shared["updated_at"] = now
                    shared["thread_state"] = "running"

            except Exception as e:
                with lock:
                    shared["thread_state"] = "read-error"
                    shared["last_error"] = f"{type(e).__name__}: {e}"
                print(f"[telemetry] read error: {type(e).__name__}: {e}")
                time.sleep(0.05)

        for stopper in (durin.sensor.stop, durin.actuator.stop):
            try:
                stopper()
            except Exception:
                pass

    except Exception as e:
        with lock:
            shared["thread_state"] = "fatal-error"
            shared["last_error"] = f"{type(e).__name__}: {e}"
        print(f"[telemetry] fatal error: {type(e).__name__}: {e}")
        if isinstance(e, OSError) and getattr(e, "errno", None) == 99:
            print(
                "[telemetry] Hint: --control-stream-host must be an IPv4 of THIS PC on the robot network "
                "(for example 192.168.x.y), not the robot hostname/IP."
            )
    finally:
        with lock:
            if shared.get("thread_state") != "fatal-error":
                shared["thread_state"] = "stopped"

    print("[telemetry] stopped")


def run_stream_ssh_command(command, durin_host, timeout_s):
    """Run start/stop stream over SSH and return True on success, False on failure."""
    try:
        result = subprocess.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                f"ConnectTimeout={max(1, int(round(timeout_s)))}",
                f"{command}@{durin_host}",
            ],
            check=False,
            timeout=timeout_s + 1.0,
        )
        if command == "stop" and result.returncode in (0, 1):
            return True
        return result.returncode == 0
    except Exception as e:
        print(f"[stream] {command} failed on {durin_host}: {e}")
        return False


def apply_spatial_coherence_filter(frame, last_event_timestamp, current_time, neighborhood_threshold, min_neighbors, event_epsilon):
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

    # Vectorized hot-neighbor counting with convolution (much faster than nested Python loops).
    hot_mask = ((current_time - last_event_timestamp) <= neighborhood_threshold).astype(np.uint8)
    hot_neighbors = cv2.filter2D(hot_mask, ddepth=cv2.CV_16U, kernel=NEIGHBOR_KERNEL, borderType=cv2.BORDER_CONSTANT)

    keep_mask = (np.abs(frame) > event_epsilon) & (hot_neighbors >= min_neighbors)
    return np.where(keep_mask, frame, 0)


def extract_clusters(filtered_frame, min_cluster_pixels, event_epsilon, min_compactness, max_aspect_ratio):
    """Group active event pixels into connected components and keep only plausible object-like blobs."""
    binary = (np.abs(filtered_frame) > event_epsilon).astype(np.uint8)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

    clusters = []
    for label in range(1, num_labels):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < min_cluster_pixels:
            continue

        x = int(stats[label, cv2.CC_STAT_LEFT])
        y = int(stats[label, cv2.CC_STAT_TOP])
        w = int(stats[label, cv2.CC_STAT_WIDTH])
        h = int(stats[label, cv2.CC_STAT_HEIGHT])
        cx = float(centroids[label][0])
        cy = float(centroids[label][1])

        bbox_area = max(1, int(w * h))
        compactness = float(area) / float(bbox_area)
        aspect_ratio = float(max(w, h)) / float(max(1, min(w, h)))

        if compactness < min_compactness:
            continue
        if aspect_ratio > max_aspect_ratio:
            continue

        clusters.append(
            {
                "bbox": (x, y, w, h),
                "centroid": (cx, cy),
                "area": area,
                "compactness": compactness,
                "aspect_ratio": aspect_ratio,
            }
        )
    return clusters


def associate_clusters(curr_clusters, prev_tracks, max_dist):
    """Assign a persistent track ID to each current cluster using nearest-centroid matching."""
    next_track_id = max(prev_tracks.keys(), default=0) + 1
    if not curr_clusters:
        return curr_clusters
    if not prev_tracks:
        for cluster in curr_clusters:
            cluster["track_id"] = next_track_id
            next_track_id += 1
        return curr_clusters

    curr_centroids = np.array([c["centroid"] for c in curr_clusters], dtype=np.float32)  # [N,2]
    prev_ids = list(prev_tracks.keys())
    prev_centroids = np.array([prev_tracks[tid]["centroid"] for tid in prev_ids], dtype=np.float32)  # [M,2]

    # Compute all pairwise distances in one vectorized step.
    diff = curr_centroids[:, None, :] - prev_centroids[None, :, :]
    dists = np.linalg.norm(diff, axis=2)

    assigned_curr = set()
    assigned_prev = set()

    # Greedy one-to-one assignment from the globally smallest valid distances.
    flat_idx = np.argsort(dists, axis=None)
    n_prev = dists.shape[1]
    for flat in flat_idx:
        i = int(flat // n_prev)
        j = int(flat % n_prev)
        if dists[i, j] > max_dist:
            break
        if i in assigned_curr or j in assigned_prev:
            continue
        curr_clusters[i]["track_id"] = prev_ids[j]
        assigned_curr.add(i)
        assigned_prev.add(j)

    for i, cluster in enumerate(curr_clusters):
        if i in assigned_curr:
            continue
        cluster["track_id"] = next_track_id
        next_track_id += 1

    return curr_clusters


def draw_cluster_overlay(display_image, cluster, flow_u, z_est, independent_motion, obstacle_speed_mps=None):
    """Draw object annotations (bbox, centroid, flow and distance text) on the displayed frame."""
    x, y, w, h = cluster["bbox"]
    cx, cy = cluster["centroid"]
    track_id = cluster["track_id"]

    # The frame is displayed transposed (x/y swapped), so convert coordinates for drawing.
    dx, dy, dw, dh = y, x, h, w
    dcx, dcy = int(round(cy)), int(round(cx))

    color = (0, 255, 255) if independent_motion else (0, 200, 0)
    cv2.rectangle(display_image, (dx, dy), (dx + dw, dy + dh), color, 2)
    cv2.circle(display_image, (dcx, dcy), 3, (255, 255, 255), -1)

    line1 = f"ID:{track_id} A:{cluster['area']}"
    line2 = f"u:{flow_u:+.1f}px/s"
    if z_est is not None:
        line3 = f"Z:{z_est:.2f}m"
    else:
        line3 = "Z:n/a"
    if obstacle_speed_mps is not None:
        line4 = f"v_obj:{obstacle_speed_mps:.2f}m/s"
    else:
        line4 = "v_obj:n/a"
    if independent_motion:
        line3 += " MOVING"

    ty = max(15, dy - 20)
    cv2.putText(display_image, line1, (dx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
    cv2.putText(display_image, line2, (dx, ty + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
    cv2.putText(display_image, line3, (dx, ty + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
    cv2.putText(display_image, line4, (dx, ty + 42), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)


def select_clusters_for_visualization(clusters, min_area, max_items, draw_moving_only=False):
    """Select a readable subset of clusters for drawing without altering tracking logic."""
    if max_items <= 0:
        return []

    eligible = [c for c in clusters if int(c.get("area", 0)) >= int(min_area)]
    if draw_moving_only:
        eligible = [c for c in eligible if c.get("independent_motion", False)]

    eligible.sort(
        key=lambda c: (
            1 if c.get("independent_motion", False) else 0,
            int(c.get("area", 0)),
        ),
        reverse=True,
    )
    return eligible[:max_items]



if __name__ == "__main__":

    win_name = "Durin DVS"
    acc = 0
    start_time = time.time()
    
    prev_tracks = {}
    prev_time = None
    runtime_event_epsilon = float(args.event_epsilon)
    background_frame = None
    zero_frame_streak = 0
    stream_host = args.stream_host if args.stream_host else args.durin

    telemetry_state = {
        "imu_freq_hz": 0.0,
        "tof_distances_m": [],
        "tof_center_m": None,
        "thread_state": "not-started",
        "last_error": "",
        "updated_at": None,
    }
    telemetry_lock = threading.Lock()
    telemetry_stop_event = threading.Event()
    telemetry_thread = None

    if args.use_telemetry:
        print("[main] telemetry enabled: IMU frequency and ToF distances will be updated from obs/imu when available")
        telemetry_thread = threading.Thread(target=telemetry_loop, args=(telemetry_stop_event, telemetry_state, telemetry_lock), daemon=True)
        telemetry_thread.start()
    else:
        print("[main] telemetry disabled: using ToF-based obstacle speeds only")

    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)

    stream_started_by_script = False
    if args.auto_stream:
        print(f"[stream] requesting start on host={stream_host}, udp port={args.port}")
        stream_started_by_script = run_stream_ssh_command("start", stream_host, args.ssh_timeout)
        if stream_started_by_script:
            print(f"DVS stream started on {stream_host}")
        else:
            print("[stream] Auto-start failed. If streamer is not running, screen will remain black.")
            telemetry_stop_event.set()
            if telemetry_thread is not None:
                telemetry_thread.join(timeout=1.0)
            sys.exit(1)


    frame_viz = np.zeros((640,480, 3))
    last_event_timestamp = np.full((640, 480), -np.inf, dtype=np.float32)
    frame_h = 640
    frame_w = 480
    tof_projection_points = get_tof_projection_points(frame_h, frame_w)
    cx_img = frame_w / 2.0
    with aestream.UDPInput((640, 480), device='cpu', port=args.port) as stream:
        try:
            while True:
                loop_start = time.time()
                active_tof_sensor_ids = TOF_FRONT_SENSOR_IDS if args.tof_front_only else None

                if args.use_telemetry:
                    with telemetry_lock:
                        imu_freq_hz = telemetry_state["imu_freq_hz"]
                        tof_distances_m = list(telemetry_state.get("tof_distances_m", []))
                        tof_center_m = telemetry_state.get("tof_center_m", None)
                        telemetry_updated_at = telemetry_state["updated_at"]
                        telemetry_thread_state = telemetry_state["thread_state"]
                        telemetry_last_error = telemetry_state["last_error"]

                    if telemetry_updated_at is None:
                        telemetry_age_s = 1e9
                    else:
                        telemetry_age_s = time.time() - float(telemetry_updated_at)
                    telemetry_stale = telemetry_age_s > args.telemetry_stale_timeout
                else:
                    imu_freq_hz = 0.0
                    tof_distances_m = []
                    tof_center_m = None
                    telemetry_updated_at = None
                    telemetry_age_s = 0.0
                    telemetry_stale = False
                    telemetry_thread_state = "disabled"
                    telemetry_last_error = ""

                frame = stream.read()
                frame_f32 = frame.astype(np.float32)
                
                if args.diagnostic_mode:
                    # Raw mode: show all events unfiltered
                    motion_frame = frame_f32
                    filtered_frame = frame_f32
                elif args.use_background_subtraction:
                    if background_frame is None:
                        background_frame = frame_f32.copy()
                    # Remove quasi-static background to avoid full-frame saturation.
                    motion_frame = frame_f32 - background_frame
                    background_frame = args.background_alpha * background_frame + (1.0 - args.background_alpha) * frame_f32
                else:
                    motion_frame = frame_f32

                acc = 0.95 * acc + 0.05 * float(np.abs(motion_frame).sum())

                if not args.diagnostic_mode:
                    # Keep only pixels that changed recently; this suppresses stale isolated noise.
                    current_time = time.time() - start_time
                    event_mask = (np.abs(motion_frame) > runtime_event_epsilon)
                    last_event_timestamp[event_mask] = current_time
                    recent_mask = (current_time - last_event_timestamp) <= args.noise_window
                    filtered_frame = np.where(recent_mask, motion_frame, 0)

                    # Apply spatial coherence filter: remove isolated noise pixels.
                    filtered_frame = apply_spatial_coherence_filter(
                        filtered_frame,
                        last_event_timestamp,
                        current_time,
                        args.neighborhood_threshold,
                        args.min_neighbors,
                        runtime_event_epsilon,
                    )
                else:
                    current_time = time.time() - start_time

                filtered_for_visual = filtered_frame

                active_ratio = float(np.count_nonzero(np.abs(filtered_frame) > runtime_event_epsilon)) / float(filtered_frame.size)

                if np.count_nonzero(np.abs(motion_frame) > runtime_event_epsilon) == 0:
                    zero_frame_streak += 1
                else:
                    zero_frame_streak = 0

                if zero_frame_streak == args.zero_frame_warning_threshold:
                    print(
                        "\n[input-warning] Received many consecutive empty frames. "
                        "Check that AEstream is sending to this PC and that --stream-host points to the correct robot."
                    )
                saturated = active_ratio > args.max_active_ratio

                if saturated:
                    # Skip expensive object extraction when the whole frame is active/noisy.
                    clusters = []
                else:
                    min_px = args.min_cluster_pixels if not args.diagnostic_mode else max(1, args.min_cluster_pixels // 4)
                    clusters = extract_clusters(
                        filtered_frame,
                        min_px,
                        runtime_event_epsilon,
                        args.min_cluster_compactness if not args.diagnostic_mode else 0.02,
                        args.max_cluster_aspect_ratio if not args.diagnostic_mode else 15.0,
                    )
                    clusters = associate_clusters(clusters, prev_tracks, args.match_max_dist)

                dt = None if prev_time is None else max(1e-6, current_time - prev_time)

                # Robust bipolar visualization: positive events in green, negative in red.
                pos = np.clip(filtered_for_visual, 0, None)
                neg = np.clip(-filtered_for_visual, 0, None)
                if pos.max() > 0:
                    pos = (pos / pos.max()) * 255.0
                if neg.max() > 0:
                    neg = (neg / neg.max()) * 255.0
                frame_viz = np.zeros((frame.shape[0], frame.shape[1], 3), dtype=np.uint8)
                frame_viz[:, :, 1] = pos.astype(np.uint8)
                frame_viz[:, :, 2] = neg.astype(np.uint8)

                image = frame_viz.transpose(1, 0, 2).copy()

                new_tracks = {}
                distances = []
                obstacle_speeds = []
                moving_ids = []
                tof_hit_count = 0

                for cluster in clusters:
                    track_id = cluster["track_id"]
                    curr_cx, curr_cy = cluster["centroid"]
                    flow_u = 0.0
                    z_est = None
                    obstacle_speed_mps = None
                    independent_motion = False

                    z_est, tof_hits = distance_from_tof_for_cluster(
                        cluster,
                        tof_projection_points,
                        tof_distances_m,
                        tof_center_m,
                        margin_px=args.tof_margin_px,
                        nearest_max_px=args.tof_nearest_max_px,
                        active_sensor_ids=active_tof_sensor_ids,
                    )
                    if z_est is not None:
                        distances.append(z_est)
                        tof_hit_count += 1

                    if dt is not None and track_id in prev_tracks:
                        prev_cx, prev_cy = prev_tracks[track_id]["centroid"]
                        flow_u = (curr_cx - prev_cx) / dt

                        if z_est is not None and np.isfinite(z_est):
                            obstacle_speed_mps = abs(flow_u) * z_est / max(args.focal_length_px, 1e-6)
                            if np.isfinite(obstacle_speed_mps):
                                obstacle_speeds.append(obstacle_speed_mps)
                                if obstacle_speed_mps >= args.moving_speed_threshold:
                                    independent_motion = True
                                    moving_ids.append(track_id)

                    cluster["flow_u"] = flow_u
                    cluster["z_est"] = z_est
                    cluster["obstacle_speed_mps"] = obstacle_speed_mps
                    cluster["independent_motion"] = independent_motion
                    cluster["tof_hits"] = tof_hits
                    new_tracks[track_id] = {"centroid": (curr_cx, curr_cy), "time": current_time}

                clusters_for_draw = select_clusters_for_visualization(
                    clusters,
                    min_area=args.min_draw_cluster_area,
                    max_items=args.max_clusters_drawn,
                    draw_moving_only=args.draw_moving_only,
                )
                for cluster in clusters_for_draw:
                    draw_cluster_overlay(
                        image,
                        cluster,
                        cluster.get("flow_u", 0.0),
                        cluster.get("z_est"),
                        cluster.get("independent_motion", False),
                        cluster.get("obstacle_speed_mps"),
                    )

                prev_tracks = new_tracks
                prev_time = current_time

                if saturated:
                    mode_txt = "SATURATED_FRAME"
                else:
                    mode_txt = "TRACKING"
                cv2.putText(image, f"Mode: {mode_txt}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(
                    image,
                    f"imuHz={imu_freq_hz} clusters={len(clusters)} draw={len(clusters_for_draw)} eps={runtime_event_epsilon:.2f}",
                    (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                )
                if args.use_telemetry:
                    state_txt = (
                        f"telemetry_age={telemetry_age_s:.2f}s {'STALE' if telemetry_stale else 'OK'} "
                        f"state={telemetry_thread_state}"
                    )
                    cv2.putText(image, state_txt, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 1, cv2.LINE_AA)
                    tof_valid = sum(1 for d in tof_distances_m if d is not None)
                    tof_txt = f"tof_valid={tof_valid} center={('n/a' if tof_center_m is None else f'{tof_center_m:.2f}m')}"
                    cv2.putText(image, tof_txt, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 255), 1, cv2.LINE_AA)

                if distances:
                    cv2.putText(
                        image,
                        f"Nearest Z={min(distances):.2f}m",
                        (10, 100 if args.use_telemetry else 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 255, 255),
                        1,
                        cv2.LINE_AA,
                    )

                cv2.imshow(win_name, image)
                if cv2.waitKey(1) & 0xFF == 27:
                    break

                # Print status with velocity info.
                status_str = (
                    f'Accumulated events: {acc:5f}, Loop time (ms): {1000*(time.time()-loop_start):5f}, '
                    f'raw_nonzero: {int(np.count_nonzero(np.abs(motion_frame) > runtime_event_epsilon))}, filtered_nonzero: {int(np.count_nonzero(filtered_frame))}, '
                    f'clusters: {len(clusters)}, moving: {len(set(moving_ids))}, '
                    f'active_ratio={active_ratio:.3f}'
                )
                print(status_str, end='\r')

        except KeyboardInterrupt:
            pass
        finally:
            telemetry_stop_event.set()
            if telemetry_thread is not None:
                telemetry_thread.join(timeout=1.0)
            cv2.destroyAllWindows()
            if args.auto_stream and stream_started_by_script:
                if run_stream_ssh_command("stop", stream_host, args.ssh_timeout):
                    print(f"DVS stream stopped on {stream_host}")
                else:
                    print(f"Unable to stop DVS stream on {stream_host}")