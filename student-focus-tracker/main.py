import cv2
import time
import os
import random
import requests
from datetime import datetime, timezone
from utils.face_detection import detect_faces, annotate_faces
from utils.gaze_tracking import estimate_gaze
from utils.head_pose import estimate_head_pose
from utils.yawn_detection import estimate_yawn
from utils.laugh_detection import estimate_laugh
from utils.focus_score import compute_focus_score

API_FRAME_URL = os.getenv("FOCUS_API_URL", "http://127.0.0.1:5000/frame")
def run_attention_tracker():
    cap = cv2.VideoCapture(0)
    last_processed = 0.0
    process_interval = random.uniform(8.0, 10.0)

    if not cap.isOpened():
        print("Error: Webcam not found.")
        return

    print("Starting Student Focus Tracker. Press 'q' to stop.")

    gaze = "Unknown"
    head_direction = "Unknown"
    yawning = False
    yawn_mar = 0.0
    laughing = False
    laugh_mar = 0.0
    laugh_width_ratio = 0.0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        now = time.time()
        if now - last_processed >= process_interval:
            last_processed = now

            # Core detectors
            face_detections = detect_faces(frame)
            gaze = estimate_gaze(frame)
            head_direction = estimate_head_pose(frame)
            yawning, yawn_mar = estimate_yawn(frame)
            laughing, laugh_mar, laugh_width_ratio = estimate_laugh(frame)

            # Focus score is computed internally for logic; not drawn on video now
            focus_score = compute_focus_score(gaze, head_direction, yawning, laughing)

            # Mark/update face boxes
            annotate_faces(frame, face_detections)

            # Send frame event to backend
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "student_id": None,
                "gaze": gaze,
                "head_direction": head_direction,
                "yawning": bool(yawning),
                "yawn_mar": float(yawn_mar),
                "laughing": bool(laughing),
                "laugh_mar": float(laugh_mar),
                "laugh_width_ratio": float(laugh_width_ratio),
                "focus_score": float(focus_score),
            }

            try:
                resp = requests.post(API_FRAME_URL, json=payload, timeout=2)
                if not resp.ok:
                    print("Warning: /frame API returned", resp.status_code, resp.text)
            except requests.RequestException as e:
                print("Warning: /frame API request failed:", e)

            # Randomize next interval early to avoid fixed schedule
            process_interval = random.uniform(8.0, 10.0)

        # Always render overlays for latest values.
        cv2.putText(frame, f"Gaze: {gaze}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Head: {head_direction}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Yawn: {yawning} / {int(mouth_distance)}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"Laugh: {laughing} / W:{int(width)} H:{int(height)}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        cv2.imshow("Focus Tracker", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_attention_tracker()
