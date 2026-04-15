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
API_STATUS_URL = None
API_FRAME_URL = None
DISPLAY_WINDOW = True  # Flag to control whether to show video window

def check_class_status(token=None):
    """Check if class is active before sending tracking data."""
    if not API_STATUS_URL or not CLASS_ID:
        print("Warning: CLASS_ID not set, assuming inactive")
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
            print("Warning: Could not check class status, assuming inactive")
            return False
    except requests.RequestException as e:
        print("Warning: Class status check failed, assuming inactive:", e)
        return False

def run_attention_tracker(token=None, headless=False):
    """Run the focus tracking for a specific class."""
    if not CLASS_ID:
        print("Error: CLASS_ID is required. Usage: python main.py <class_id>")
        return
    
    global DISPLAY_WINDOW
    DISPLAY_WINDOW = not headless  # Disable display if running headless
    
    print(f"Starting Student Focus Tracker for class: {CLASS_ID}")
    print(f"Display Mode: {'Enabled' if DISPLAY_WINDOW else 'Headless (background)'}")
    
    cap = cv2.VideoCapture(0)
    last_processed = 0.0
    process_interval = random.uniform(8.0, 10.0)
    last_status_check = 0.0
    status_check_interval = 10.0  # Check status every 10 seconds

    if not cap.isOpened():
        print("Error: Webcam not found or unable to access it.")
        return

    print("Starting Student Focus Tracker. Press 'q' to stop (or CTRL+C).")

    gaze = "Unknown"
    head_direction = "Unknown"
    yawning = False
    mouth_distance = 0.0
    laughing = False
    width = 0.0
    height = 0.0
    class_active = True

    while cap.isOpened() and class_active:
        try:
            ret, frame = cap.read()
            if not ret:
                break

            now = time.time()
            
            # Check class status every 10 seconds
            if now - last_status_check >= status_check_interval:
                last_status_check = now
                class_active = check_class_status(token)
                if not class_active:
                    print("Class has ended. Stopping tracker...")
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
                    print(f"Warning: Detection error: {e}")
                    continue

                # Focus score is computed internally for logic; not drawn on video now
                focus_score = compute_focus_score(gaze, head_direction, yawning, laughing)

                # Mark/update face boxes
                try:
                    annotate_faces(frame, face_detections)
                except Exception as e:
                    print(f"Warning: Annotation error: {e}")

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
                if token:
                    headers['Authorization'] = token

                try:
                    resp = requests.post(API_FRAME_URL, json=payload, headers=headers, timeout=2)
                    if not resp.ok:
                        print(f"Warning: /frame API returned {resp.status_code}")
                except requests.RequestException as e:
                    print(f"Warning: /frame API request failed: {e}")

                # Randomize next interval early to avoid fixed schedule
                process_interval = random.uniform(8.0, 10.0)

            # Display overlay only if display window is enabled
            if DISPLAY_WINDOW:
                try:
                    frame_copy = frame.copy()
                    cv2.putText(frame_copy, f"Gaze: {gaze}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(frame_copy, f"Head: {head_direction}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(frame_copy, f"Yawn: {yawning} / {int(mouth_distance)}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    cv2.putText(frame_copy, f"Laugh: {laughing} / W:{int(width)} H:{int(height)}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    cv2.putText(frame_copy, f"Class: {CLASS_ID[:8]}... | Status: {'ACTIVE' if class_active else 'ENDED'}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if class_active else (0, 0, 255), 2)

                    cv2.imshow("Focus Tracker", frame_copy)

                    # Handle keyboard input with timeout
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        print("User pressed 'q'. Stopping tracker...")
                        break
                except cv2.error as e:
                    print(f"Warning: OpenCV display error (running in headless mode): {e}")
                    DISPLAY_WINDOW = False
                except Exception as e:
                    print(f"Warning: Display error: {e}")
                    DISPLAY_WINDOW = False
        except KeyboardInterrupt:
            print("Interrupted by user. Stopping tracker...")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            continue

    cap.release()
    if DISPLAY_WINDOW:
        try:
            cv2.destroyAllWindows()
        except Exception as e:
            print(f"Warning: Error closing windows: {e}")
    print("Tracking ended.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        CLASS_ID = sys.argv[1]
        token = sys.argv[2] if len(sys.argv) > 2 else None
        headless = "--headless" in sys.argv or "--background" in sys.argv
        
        # Initialize API URLs based on CLASS_ID
        API_STATUS_URL = f"{API_BASE_URL}/classes/{CLASS_ID}/status"
        API_FRAME_URL = f"{API_BASE_URL}/frame"
        
        run_attention_tracker(token, headless=headless)
    else:
        print("Usage: python main.py <class_id> [token] [--headless]")
        print("Example: python main.py 507f1f77bcf86cd799439011")
        print("Example (headless): python main.py 507f1f77bcf86cd799439011 <token> --headless")
