import cv2
import time
import os
import random
import requests
import sys
import subprocess
from datetime import datetime, timezone
from utils.face_detection import detect_faces, annotate_faces
from utils.gaze_tracking import estimate_gaze
from utils.head_pose import estimate_head_pose
from utils.yawn_detection import estimate_yawn
from utils.laugh_detection import estimate_laugh
from utils.focus_score import compute_focus_score

API_BASE_URL = os.getenv("FOCUS_API_URL", "http://127.0.0.1:5000")
CLASS_ID = None
TOKEN = None
API_STATUS_URL = None
API_FRAME_URL = None
DISPLAY_WINDOW = True  # Flag to control whether to show video window

def log_message(msg):
    """Print message with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}")

def check_class_status(token=None):
    """Check if class is active before sending tracking data."""
    if not API_STATUS_URL or not CLASS_ID:
        log_message("Warning: CLASS_ID not set, assuming inactive")
        return False
    try:
        headers = {}
        if token:
            headers['Authorization'] = token
        resp = requests.get(API_STATUS_URL, headers=headers, timeout=2)
        if resp.ok:
            data = resp.json()
            # Check if class is still active
            cls = data if isinstance(data, dict) else {}
            status = cls.get("status", "inactive") if isinstance(data, dict) else None
            return status == "active"
        else:
            log_message(f"Warning: Could not check class status, returned {resp.status_code}")
            return True  # Continue tracking even if status check fails
    except requests.RequestException as e:
        log_message(f"Warning: Class status check failed: {e}")
        return True  # Continue tracking if connection fails

def run_attention_tracker(token=None, headless=False):
    """Run the focus tracking for a specific class."""
    if not CLASS_ID:
        log_message("Error: CLASS_ID is required. Usage: python main.py <class_id> <token> [--headless]")
        return
    
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
    
    log_message(f"Tracking ended. Processed {frame_count} frames, sent {sent_frames} to server.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        CLASS_ID = sys.argv[1]
        token = sys.argv[2] if len(sys.argv) > 2 else None
        headless = "--headless" in sys.argv or "--background" in sys.argv
        
        # Initialize API URLs based on CLASS_ID
        API_STATUS_URL = f"{API_BASE_URL}/classes/{CLASS_ID}/status"
        API_FRAME_URL = f"{API_BASE_URL}/frame"
        
        if not token:
            log_message("Warning: No token provided, requests may fail authentication")
        
        log_message(f"Arguments: class_id={CLASS_ID}, token={'***' if token else 'None'}, headless={headless}")
        
        run_attention_tracker(token=token, headless=headless)
    else:
        log_message("Usage: python main.py <class_id> [token] [--headless]")
        log_message("Example: python main.py 507f1f77bcf86cd799439011 <token>")
        log_message("Example (headless): python main.py 507f1f77bcf86cd799439011 <token> --headless")
