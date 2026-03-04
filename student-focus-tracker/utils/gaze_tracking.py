import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

cap = cv2.VideoCapture(0)

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:

            left_eye_points = []
            right_eye_points = []

            for idx in LEFT_EYE:
                x = int(face_landmarks.landmark[idx].x * w)
                y = int(face_landmarks.landmark[idx].y * h)
                left_eye_points.append((x, y))
                cv2.circle(frame, (x, y), 2, (0,255,0), -1)

            for idx in RIGHT_EYE:
                x = int(face_landmarks.landmark[idx].x * w)
                y = int(face_landmarks.landmark[idx].y * h)
                right_eye_points.append((x, y))
                cv2.circle(frame, (x, y), 2, (0,255,0), -1)

            # Get center of left eye
            left_eye_center = np.mean(left_eye_points, axis=0).astype(int)

            # Simple horizontal gaze check
            eye_left = left_eye_points[0][0]
            eye_right = left_eye_points[3][0]

            if left_eye_center[0] < eye_left + 5:
                text = "Looking Left"
            elif left_eye_center[0] > eye_right - 5:
                text = "Looking Right"
            else:
                text = "Looking Forward"

            cv2.putText(frame, text, (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 255, 0), 2)

    cv2.imshow("Gaze Tracking", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()