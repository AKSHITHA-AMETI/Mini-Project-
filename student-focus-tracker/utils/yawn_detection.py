import cv2
import numpy as np

def estimate_yawn(frame, threshold=25, min_detection_confidence=0.5, min_tracking_confidence=0.5):
    """Detect yawning - stub implementation without mediapipe.
    
    Returns: (is_yawning: bool, mouth_distance: float)
    This is a placeholder. In production, use mediapipe.solutions.face_mesh with Python < 3.14
    """
    return (False, 0.0)


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        yawn, dist = estimate_yawn(frame)
        title = "Yawning" if yawn else "Normal"
        cv2.putText(frame, f"{title} ({int(dist)})", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("Yawn Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()
