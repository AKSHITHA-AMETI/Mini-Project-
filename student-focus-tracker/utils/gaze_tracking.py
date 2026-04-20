import cv2
import numpy as np
import math

# Try to use mediapipe for face mesh
USE_MEDIAPIPE = False
mp_face_mesh = None
mp_drawing = None

try:
    import mediapipe as mp
    mp_face_mesh = mp.solutions.face_mesh
    mp_drawing = mp.solutions.drawing_utils
    USE_MEDIAPIPE = True
except ImportError:
    USE_MEDIAPIPE = False

def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two points."""
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def eye_aspect_ratio(eye_landmarks):
    """Calculate Eye Aspect Ratio (EAR) for blink/sleep detection."""
    # Vertical eye landmarks
    v1 = calculate_distance(eye_landmarks[1], eye_landmarks[5])
    v2 = calculate_distance(eye_landmarks[2], eye_landmarks[4])

    # Horizontal eye landmark
    h = calculate_distance(eye_landmarks[0], eye_landmarks[3])

    # EAR = (v1 + v2) / (2 * h)
    ear = (v1 + v2) / (2.0 * h) if h > 0 else 0
    return ear

def estimate_gaze(frame, min_detection_confidence=0.5, min_tracking_confidence=0.5):
    """
    Estimate gaze direction and detect sleeping using MediaPipe Face Mesh.

    Returns: gaze_direction string (e.g., "Looking Forward", "Looking Left", "Eyes Closed")
    """
    if not USE_MEDIAPIPE:
        # Fallback to basic gaze estimation
        return estimate_gaze_opencv(frame)

    try:
        with mp_face_mesh.FaceMesh(
            max_num_faces=1,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        ) as face_mesh:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            if not results.multi_face_landmarks:
                return "No Face Detected"

            face_landmarks = results.multi_face_landmarks[0]

            h, w, _ = frame.shape

            # Left eye landmarks (MediaPipe indices)
            left_eye_indices = [33, 160, 158, 133, 153, 144]  # [corner1, top1, top2, corner2, bottom1, bottom2]
            left_eye = [(face_landmarks.landmark[i].x * w, face_landmarks.landmark[i].y * h) for i in left_eye_indices]

            # Right eye landmarks
            right_eye_indices = [362, 385, 387, 263, 373, 380]
            right_eye = [(face_landmarks.landmark[i].x * w, face_landmarks.landmark[i].y * h) for i in right_eye_indices]

            # Calculate EAR for both eyes
            left_ear = eye_aspect_ratio(left_eye)
            right_ear = eye_aspect_ratio(right_eye)
            avg_ear = (left_ear + right_ear) / 2.0

            # Eye blink/sleep detection threshold
            EAR_THRESHOLD = 0.25  # Typical threshold for closed eyes
            if avg_ear < EAR_THRESHOLD:
                return "Eyes Closed"

            # Pupil center estimation for gaze direction
            # Left eye pupil center (approximated)
            left_pupil_x = (left_eye[0][0] + left_eye[3][0]) / 2
            left_pupil_y = (left_eye[1][1] + left_eye[4][1]) / 2

            # Right eye pupil center
            right_pupil_x = (right_eye[0][0] + right_eye[3][0]) / 2
            right_pupil_y = (right_eye[1][1] + right_eye[4][1]) / 2

            # Average pupil position
            avg_pupil_x = (left_pupil_x + right_pupil_x) / 2
            avg_pupil_y = (left_pupil_y + right_pupil_y) / 2

            # Face center
            face_center_x = w / 2
            face_center_y = h / 2

            # Determine gaze direction based on pupil position relative to face center
            x_offset = avg_pupil_x - face_center_x
            y_offset = avg_pupil_y - face_center_y

            # Thresholds for direction detection
            x_threshold = w * 0.1  # 10% of face width
            y_threshold = h * 0.05  # 5% of face height

            if abs(x_offset) < x_threshold and abs(y_offset) < y_threshold:
                return "Looking Forward"
            elif x_offset > x_threshold:
                return "Looking Right"
            elif x_offset < -x_threshold:
                return "Looking Left"
            elif y_offset > y_threshold:
                return "Looking Down"
            elif y_offset < -y_threshold:
                return "Looking Up"
            else:
                return "Looking Forward"

    except Exception as e:
        print(f"Gaze estimation error: {e}")
        return "Unknown"

def estimate_gaze_opencv(frame):
    """
    Fallback gaze estimation using OpenCV Haar cascades.
    Basic implementation for eye detection.
    """
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Load eye cascade
        eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
        eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

        if eye_cascade.empty():
            return "Unknown"

        eyes = eye_cascade.detectMultiScale(gray, 1.1, 3)

        if len(eyes) == 0:
            return "Eyes Closed"
        elif len(eyes) >= 2:
            return "Looking Forward"
        else:
            return "Looking Away"

    except Exception as e:
        print(f"OpenCV gaze estimation error: {e}")
        return "Unknown"


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
