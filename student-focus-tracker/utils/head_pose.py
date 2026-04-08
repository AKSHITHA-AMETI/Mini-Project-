import cv2
import numpy as np

def estimate_head_pose(frame, min_detection_confidence=0.5, min_tracking_confidence=0.5):
    """Estimate head pose direction - stub implementation without mediapipe.
    
    This is a placeholder that returns dummy head pose.
    In production, use mediapipe.solutions.face_mesh with Python < 3.14
    """
    return "Forward"


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        direction = estimate_head_pose(frame)
        cv2.putText(frame, direction, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Head Pose", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()
