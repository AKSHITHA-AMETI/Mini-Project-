import cv2
import mediapipe as mp
import numpy as np
import time

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

cap = cv2.VideoCapture(0)

# Mouth landmark points
UPPER_LIP = 13
LOWER_LIP = 14

yawn_start_time = 0
yawn_detected = False

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:

            # Get lip coordinates
            upper = face_landmarks.landmark[UPPER_LIP]
            lower = face_landmarks.landmark[LOWER_LIP]

            upper_point = np.array([int(upper.x * w), int(upper.y * h)])
            lower_point = np.array([int(lower.x * w), int(lower.y * h)])

            # Draw points
            cv2.circle(frame, tuple(upper_point), 3, (0,255,0), -1)
            cv2.circle(frame, tuple(lower_point), 3, (0,255,0), -1)

            # Calculate distance
            mouth_distance = np.linalg.norm(upper_point - lower_point)

            # Threshold (adjust if needed)
            if mouth_distance > 25:
                if not yawn_detected:
                    yawn_start_time = time.time()
                    yawn_detected = True
                cv2.putText(frame, "Yawning...",
                            (30, 50), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0,0,255), 2)
            else:
                yawn_detected = False

            # Show distance (for debugging)
            cv2.putText(frame, f"Distance: {int(mouth_distance)}",
                        (30, 90), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (255,0,0), 2)

    cv2.imshow("Yawn Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()