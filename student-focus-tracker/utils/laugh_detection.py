import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh
LEFT_MOUTH = 61
RIGHT_MOUTH = 291
UPPER_LIP = 13
LOWER_LIP = 14


def estimate_laugh(frame, width_threshold=80, height_threshold=15, min_detection_confidence=0.5, min_tracking_confidence=0.5):
    with mp_face_mesh.FaceMesh(
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
        refine_landmarks=True,
    ) as face_mesh:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        return False, 0.0, 0.0

    h, w, _ = frame.shape
    lm = results.multi_face_landmarks[0].landmark

    left = lm[LEFT_MOUTH]
    right = lm[RIGHT_MOUTH]
    upper = lm[UPPER_LIP]
    lower = lm[LOWER_LIP]

    left_point = np.array([int(left.x * w), int(left.y * h)])
    right_point = np.array([int(right.x * w), int(right.y * h)])
    upper_point = np.array([int(upper.x * w), int(upper.y * h)])
    lower_point = np.array([int(lower.x * w), int(lower.y * h)])

    mouth_width = np.linalg.norm(left_point - right_point)
    mouth_height = np.linalg.norm(upper_point - lower_point)

    is_laughing = mouth_width > width_threshold and mouth_height > height_threshold
    return is_laughing, mouth_width, mouth_height


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        laugh, w, h = estimate_laugh(frame)
        text = "Laughing" if laugh else "Normal"
        cv2.putText(frame, f"{text} W:{int(w)} H:{int(h)}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow("Laugh Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()
