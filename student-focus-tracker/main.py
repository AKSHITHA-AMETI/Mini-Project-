import cv2
import time
import os
import random
import json
import sys
import threading
from datetime import datetime, timezone
from utils.face_detection import detect_faces, annotate_faces
from utils.gaze_tracking import estimate_gaze
from utils.head_pose import estimate_head_pose
from utils.yawn_detection import estimate_yawn
from utils.laugh_detection import estimate_laugh
from utils.focus_score import compute_focus_score
# Configuration
CLASS_ID = None
DISPLAY_WINDOW = True  # Flag to control whether to show video window
SAVE_TO_FILE = True   # Save focus data to local file
UPLOAD_TO_SERVER = True  # Upload data to server when available
LOG_FILE = "focus_tracking_log.json"
UPLOAD_INTERVAL = 30  # Upload every 30 seconds when data accumulates

# API Configuration (optional for local-only mode)
API_BASE_URL = os.getenv("FOCUS_API_URL", "http://127.0.0.1:5000")
TOKEN = os.getenv("FOCUS_TOKEN")  # Optional token for server upload

def log_message(msg):
    """Print message with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}")

def upload_data_to_server(focus_data_batch, class_id, device_id, token=None):
    """Upload accumulated focus data to server"""
    if not UPLOAD_TO_SERVER or not focus_data_batch:
        return False

    try:
        import requests
        upload_url = f"{API_BASE_URL}/upload-focus-data/{class_id}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = token

        payload = {
            'device_id': device_id,
            'focus_data': focus_data_batch
        }

        response = requests.post(upload_url, json=payload, headers=headers, timeout=10)

        if response.status_code == 201:
            log_message(f"Successfully uploaded {len(focus_data_batch)} data points to server")
            return True
        else:
            log_message(f"Server upload failed: {response.status_code} - {response.text}")
            return False

    except ImportError:
        log_message("Warning: requests library not available, server upload disabled")
        return False
    except Exception as e:
        log_message(f"Server upload error: {e}")
        return False

def run_attention_tracker(token=None, headless=False):
    """Run the focus tracking locally on this device."""

    if not CLASS_ID:
        log_message("Error: CLASS_ID is required. Usage: python main.py <class_id> [--headless]")
        return

    global DISPLAY_WINDOW
    DISPLAY_WINDOW = not headless  # Disable display if running headless

    log_message(f"Starting local focus tracking for class: {CLASS_ID}")
    log_message(f"Display Mode: {'Enabled' if DISPLAY_WINDOW else 'Headless (background)'}")
    log_message(f"Data Saving: {'Enabled' if SAVE_TO_FILE else 'Disabled'}")

    # Try to access camera
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        log_message("Error: Webcam not found or unable to access it.")
        log_message("Attempting fallback: trying different camera indices...")
        for i in range(1, 5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                log_message(f"Found camera at index {i}")
                break
        if not cap.isOpened():
            log_message("Error: No camera found on this device")
            log_message("Camera is required for focus tracking. Please ensure:")
            log_message("  1. Camera device is connected")
            log_message("  2. Camera has proper permissions")
            log_message("  3. No other application is using the camera")
            return

    last_processed = 0.0
    process_interval = random.uniform(8.0, 10.0)  # Random interval to avoid predictability
    last_upload = 0.0
    upload_interval = UPLOAD_INTERVAL

    # Data accumulation for batch upload
    focus_data_batch = []
    device_id = f"device_{os.getpid()}_{os.getlogin() if hasattr(os, 'getlogin') else 'unknown'}"

    log_message("Camera initialized. Starting local focus tracking loop...")
    log_message(f"Device ID: {device_id}")
    log_message(f"Server upload: {'Enabled' if UPLOAD_TO_SERVER else 'Disabled'}")

    gaze = "Unknown"
    head_direction = "Unknown"
    yawning = False
    mouth_distance = 0.0
    laughing = False
    mouth_width = 0.0
    mouth_height = 0.0
    frame_count = 0
    processed_frames = 0

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                log_message("Error: Failed to read frame from camera")
                break

            frame_count += 1
            now = time.time()

            if now - last_processed >= process_interval:
                last_processed = now
                processed_frames += 1

                # Core computer vision detections
                try:
                    face_detections = detect_faces(frame)
                    gaze = estimate_gaze(frame)
                    head_direction = estimate_head_pose(frame)
                    yawning, mouth_distance = estimate_yawn(frame)
                    laughing, mouth_width, mouth_height = estimate_laugh(frame)
                except Exception as e:
                    log_message(f"Warning: Detection error: {e}")
                    face_detections = []
                    gaze = "Unknown"
                    head_direction = "Unknown"
                    yawning = False
                    laughing = False

                # Compute focus score using all detected features
                focus_score = compute_focus_score(
                    gaze, head_direction, yawning, laughing,
                    mouth_distance, mouth_width, mouth_height
                )

                # Prepare tracking data
                tracking_data = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "class_id": CLASS_ID,
                    "device_id": f"device_{os.getpid()}",  # Unique device identifier
                    "gaze": gaze,
                    "head_direction": head_direction,
                    "yawning": bool(yawning),
                    "mouth_distance": float(mouth_distance),
                    "laughing": bool(laughing),
                    "mouth_width": float(mouth_width),
                    "mouth_height": float(mouth_height),
                    "focus_score": float(focus_score),
                    "faces_detected": len(face_detections),
                    "frame_number": frame_count
                }

                # Save data locally and accumulate for upload
                save_focus_data(tracking_data)
                focus_data_batch.append(tracking_data)

                # Upload data periodically
                now = time.time()
                if now - last_upload >= upload_interval and focus_data_batch:
                    if upload_data_to_server(focus_data_batch, CLASS_ID, device_id, TOKEN):
                        focus_data_batch = []  # Clear batch after successful upload
                        last_upload = now
                    else:
                        # If upload fails, keep data for next attempt
                        log_message("Upload failed, will retry next interval")

                # Log summary every 10 processed frames
                if processed_frames % 10 == 0:
                    log_message(f"Frame {frame_count}: Focus={focus_score}, Gaze={gaze}, Head={head_direction}, Yawn={yawning}, Laugh={laughing}")
                    log_message(f"Data points accumulated: {len(focus_data_batch)}")

                # Mark/update face boxes
                try:
                    annotate_faces(frame, face_detections)
                except Exception as e:
                    log_message(f"Warning: Annotation error: {e}")

                # Randomize next interval to avoid fixed schedule
                process_interval = random.uniform(8.0, 10.0)

            # Display overlay only if display window is enabled
            if DISPLAY_WINDOW:
                try:
                    frame_copy = frame.copy()

                    # Display all tracking information
                    cv2.putText(frame_copy, f"Gaze: {gaze}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(frame_copy, f"Head: {head_direction}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(frame_copy, f"Yawn: {yawning} / Dist:{int(mouth_distance)}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    cv2.putText(frame_copy, f"Laugh: {laughing} / W:{int(mouth_width)} H:{int(mouth_height)}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    cv2.putText(frame_copy, f"Focus Score: {focus_score}/10", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    cv2.putText(frame_copy, f"Processed: {processed_frames} | Total: {frame_count}", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    cv2.imshow("Local Focus Tracker", frame_copy)

                    # Handle keyboard input
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        log_message("User pressed 'q'. Stopping tracker...")
                        break
                    elif key == ord("s"):
                        # Save current frame for debugging
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"debug_frame_{timestamp}.jpg"
                        cv2.imwrite(filename, frame_copy)
                        log_message(f"Saved debug frame: {filename}")

                except cv2.error as e:
                    log_message(f"Warning: OpenCV display error: {e}")
                    DISPLAY_WINDOW = False
                except Exception as e:
                    log_message(f"Warning: Display error: {e}")
                    DISPLAY_WINDOW = False

    except KeyboardInterrupt:
        log_message("Interrupted by user. Stopping tracker...")
    except Exception as e:
        log_message(f"Error in main loop: {e}")
    finally:
        cap.release()
        if DISPLAY_WINDOW:
            try:
                cv2.destroyAllWindows()
            except Exception as e:
                log_message(f"Warning: Error closing windows: {e}")

        # Final upload of any remaining data
        if focus_data_batch and UPLOAD_TO_SERVER:
            log_message(f"Performing final upload of {len(focus_data_batch)} remaining data points...")
            upload_data_to_server(focus_data_batch, CLASS_ID, device_id, TOKEN)

    log_message(f"Tracking ended. Processed {frame_count} frames, analyzed {processed_frames} for focus.")
    log_message(f"Data saved to: {LOG_FILE}")
    if UPLOAD_TO_SERVER:
        log_message("Data upload to server completed.")
    global DISPLAY_WINDOW, TOKEN
    TOKEN = token
    DISPLAY_WINDOW = not headless  # Disable display if running headless
    
    log_message(f"Starting tracking for class: {CLASS_ID}")
    log_message(f"API Base URL: {API_BASE_URL}")
    log_message(f"Display Mode: {'Enabled' if DISPLAY_WINDOW else 'Headless (background)'}")
    log_message(f"Authenticated: {bool(token)}")
    
    # Try to access camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        log_message("Error: Webcam not found or unable to access it.")
        log_message("Attempting fallback: trying different camera indices...")
        for i in range(1, 5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                log_message(f"Found camera at index {i}")
                break
        if not cap.isOpened():
            log_message("Error: No camera found on this device")
            log_message("Camera is required for focus tracking. Please ensure:")
            log_message("  1. Camera device is connected")
            log_message("  2. Camera has proper permissions")
            log_message("  3. No other application is using the camera")
            return

    last_processed = 0.0
    process_interval = random.uniform(8.0, 10.0)
    last_status_check = 0.0
    status_check_interval = 10.0  # Check status every 10 seconds

    log_message("Camera initialized. Starting focus tracking loop...")

    gaze = "Unknown"
    head_direction = "Unknown"
    yawning = False
    mouth_distance = 0.0
    laughing = False
    width = 0.0
    height = 0.0
    class_active = True
    frame_count = 0
    sent_frames = 0

    while cap.isOpened() and class_active:
        try:
            ret, frame = cap.read()
            if not ret:
                log_message("Error: Failed to read frame from camera")
                break

            frame_count += 1
            now = time.time()
            
            # Check class status every 10 seconds
            if now - last_status_check >= status_check_interval:
                last_status_check = now
                class_active = check_class_status(TOKEN)
                if not class_active:
                    log_message("Class has ended. Stopping tracker...")
                    break

            if now - last_processed >= process_interval:
                last_processed = now

                # Core detectors
                try:
                    face_detections = detect_faces(frame)
                    gaze = estimate_gaze(frame)
                    head_direction = estimate_head_pose(frame)
                    yawning, mouth_distance = estimate_yawn(frame)
                    laughing, width, height = estimate_laugh(frame)
                except Exception as e:
                    log_message(f"Warning: Detection error: {e}")
                    face_detections = []
                    gaze = "Unknown"
                    head_direction = "Unknown"

                # Focus score is computed internally for logic; not drawn on video now
                focus_score = compute_focus_score(gaze, head_direction, yawning, laughing)

                # Mark/update face boxes
                try:
                    annotate_faces(frame, face_detections)
                except Exception as e:
                    log_message(f"Warning: Annotation error: {e}")

                # Send frame event to backend
                payload = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "class_id": CLASS_ID,
                    "gaze": gaze,
                    "head_direction": head_direction,
                    "yawning": bool(yawning),
                    "mouth_distance": float(mouth_distance),
                    "laughing": bool(laughing),
                    "mouth_width": float(width),
                    "mouth_height": float(height),
                    "focus_score": float(focus_score),
                }

                headers = {}
                if TOKEN:
                    headers['Authorization'] = TOKEN

                try:
                    resp = requests.post(API_FRAME_URL, json=payload, headers=headers, timeout=2)
                    if resp.ok:
                        sent_frames += 1
                    else:
                        log_message(f"Warning: /frame API returned {resp.status_code}: {resp.text[:100]}")
                except requests.RequestException as e:
                    log_message(f"Warning: /frame API request failed: {e}")

                # Randomize next interval early to avoid fixed schedule
                process_interval = random.uniform(8.0, 10.0)

            # Display overlay only if display window is enabled and not headless
            if DISPLAY_WINDOW:
                try:
                    frame_copy = frame.copy()
                    cv2.putText(frame_copy, f"Gaze: {gaze}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(frame_copy, f"Head: {head_direction}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(frame_copy, f"Yawn: {yawning} / {int(mouth_distance)}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    cv2.putText(frame_copy, f"Laugh: {laughing} / W:{int(width)} H:{int(height)}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    cv2.putText(frame_copy, f"Sent: {sent_frames} | Status: {'ACTIVE' if class_active else 'ENDED'}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if class_active else (0, 0, 255), 2)

                    cv2.imshow("Focus Tracker", frame_copy)

                    # Handle keyboard input with timeout
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        log_message("User pressed 'q'. Stopping tracker...")
                        break
                except cv2.error as e:
                    log_message(f"Warning: OpenCV display error: {e}")
                    DISPLAY_WINDOW = False
                except Exception as e:
                    log_message(f"Warning: Display error: {e}")
                    DISPLAY_WINDOW = False
        except KeyboardInterrupt:
            log_message("Interrupted by user. Stopping tracker...")
            break
        except Exception as e:
            log_message(f"Error in main loop: {e}")
            continue

    cap.release()
    if DISPLAY_WINDOW:
        try:
            cv2.destroyAllWindows()
        except Exception as e:
            log_message(f"Warning: Error closing windows: {e}")

        # Final upload of any remaining data
        if focus_data_batch and UPLOAD_TO_SERVER:
            log_message(f"Performing final upload of {len(focus_data_batch)} remaining data points...")
            upload_data_to_server(focus_data_batch, CLASS_ID, device_id, TOKEN)

    log_message(f"Tracking ended. Processed {frame_count} frames, analyzed {processed_frames} for focus.")
    log_message(f"Data saved to: {LOG_FILE}")
    if UPLOAD_TO_SERVER:
        log_message("Data upload to server completed.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        CLASS_ID = sys.argv[1]
        token = sys.argv[2] if len(sys.argv) > 2 else None
        headless = "--headless" in sys.argv or "--background" in sys.argv
        no_upload = "--no-upload" in sys.argv or "--local-only" in sys.argv

        # Configure upload behavior
        if no_upload:
            UPLOAD_TO_SERVER = False
            log_message("Server upload disabled by command line flag")

        # Try to get token from environment if not provided
        if not token:
            token = TOKEN

        # Initialize API URLs based on CLASS_ID (for status checks if uploading)
        if UPLOAD_TO_SERVER:
            API_STATUS_URL = f"{API_BASE_URL}/classes/{CLASS_ID}/status"
            API_FRAME_URL = f"{API_BASE_URL}/frame"

        if not token and UPLOAD_TO_SERVER:
            log_message("Warning: No token provided, server upload may fail authentication")

        log_message(f"Arguments: class_id={CLASS_ID}, token={'***' if token else 'None'}, headless={headless}, upload={UPLOAD_TO_SERVER}")

        run_attention_tracker(token=token, headless=headless)
    else:
        log_message("Usage: python main.py <class_id> [token] [--headless] [--no-upload]")
        log_message("Examples:")
        log_message("  python main.py 507f1f77bcf86cd799439011 <token>                    # Full tracking with server upload")
        log_message("  python main.py 507f1f77bcf86cd799439011 <token> --headless       # Background tracking")
        log_message("  python main.py 507f1f77bcf86cd799439011 --no-upload             # Local-only tracking")
        log_message("  python main.py 507f1f77bcf86cd799439011 <token> --headless --no-upload  # Local background tracking")
