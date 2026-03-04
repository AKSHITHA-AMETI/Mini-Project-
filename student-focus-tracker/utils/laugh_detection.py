import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

cap = cv2.VideoCapture(0)

LEFT_MOUTH = 61
RIGHT_MOUTH = 291
UPPER_LIP = 13
LOWER_LIP = 14

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:

            left = face_landmarks.landmark[LEFT_MOUTH]
            right = face_landmarks.landmark[RIGHT_MOUTH]
            upper = face_landmarks.landmark[UPPER_LIP]
            lower = face_landmarks.landmark[LOWER_LIP]

            left_point = np.array([int(left.x * w), int(left.y * h)])
            right_point = np.array([int(right.x * w), int(right.y * h)])
            upper_point = np.array([int(upper.x * w), int(upper.y * h)])
            lower_point = np.array([int(lower.x * w), int(lower.y * h)])

            cv2.circle(frame, tuple(left_point), 3, (0,255,0), -1)
            cv2.circle(frame, tuple(right_point), 3, (0,255,0), -1)

            mouth_width = np.linalg.norm(left_point - right_point)
            mouth_height = np.linalg.norm(upper_point - lower_point)

            text = "Normal"

            # Laugh condition
            if mouth_width > 80 and mouth_height > 15:
                text = "Laughing"

            cv2.putText(frame, text, (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0,0,255), 2)

            cv2.putText(frame, f"W:{int(mouth_width)} H:{int(mouth_height)}",
                        (30, 90),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (255,0,0), 2)

    cv2.imshow("Laugh Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()