import cv2
import numpy as np

def estimate_gaze(frame, min_detection_confidence=0.5, min_tracking_confidence=0.5):
    """Estimate gaze direction - stub implementation without mediapipe.
    
    This is a placeholder that returns dummy gaze direction.
    In production, use mediapipe.solutions.face_mesh with Python < 3.14
    """
    return "Forward"


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        gaze = estimate_gaze(frame)
        cv2.putText(frame, gaze, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Gaze Tracking", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()
