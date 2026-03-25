import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh
UPPER_LIP = 13
LOWER_LIP = 14


def estimate_yawn(frame, threshold=25, min_detection_confidence=0.5, min_tracking_confidence=0.5):
    with mp_face_mesh.FaceMesh(
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
        refine_landmarks=True,
    ) as face_mesh:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        return False, 0.0

    h, w, _ = frame.shape
    lm = results.multi_face_landmarks[0].landmark

    upper = lm[UPPER_LIP]
    lower = lm[LOWER_LIP]
    upper_point = np.array([int(upper.x * w), int(upper.y * h)])
    lower_point = np.array([int(lower.x * w), int(lower.y * h)])

    mouth_distance = np.linalg.norm(upper_point - lower_point)
    yawn = mouth_distance > threshold
    return yawn, mouth_distance


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
