import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]


def estimate_gaze(frame, min_detection_confidence=0.5, min_tracking_confidence=0.5):
    with mp_face_mesh.FaceMesh(
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
        refine_landmarks=True,
    ) as face_mesh:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        return "Unknown"

    h, w, _ = frame.shape
    face_landmarks = results.multi_face_landmarks[0]

    left_eye_points = []
    right_eye_points = []

    for idx in LEFT_EYE:
        lm = face_landmarks.landmark[idx]
        left_eye_points.append((int(lm.x * w), int(lm.y * h)))

    for idx in RIGHT_EYE:
        lm = face_landmarks.landmark[idx]
        right_eye_points.append((int(lm.x * w), int(lm.y * h)))

    left_eye_center = np.mean(left_eye_points, axis=0).astype(int)
    right_eye_center = np.mean(right_eye_points, axis=0).astype(int)

    left_eye_horiz = left_eye_points[0][0], left_eye_points[3][0]
    right_eye_horiz = right_eye_points[0][0], right_eye_points[3][0]

    left_horiz_left, left_horiz_right = left_eye_horiz
    right_horiz_left, right_horiz_right = right_eye_horiz

    if left_eye_center[0] < left_horiz_left + 8 and right_eye_center[0] < right_horiz_left + 8:
        return "Looking Left"
    if left_eye_center[0] > left_horiz_right - 8 and right_eye_center[0] > right_horiz_right - 8:
        return "Looking Right"

    return "Looking Forward"


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
