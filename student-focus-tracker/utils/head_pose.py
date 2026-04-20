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

def estimate_head_pose(frame, min_detection_confidence=0.5, min_tracking_confidence=0.5):
    """
    Estimate head pose direction using MediaPipe Face Mesh.

    Returns: head_direction string (e.g., "Looking Forward", "Looking Left", "Looking Down")
    """
    if not USE_MEDIAPIPE:
        # Fallback to basic head pose estimation
        return estimate_head_pose_opencv(frame)

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

            # Key facial landmarks for head pose estimation
            # Nose tip: 1
            # Chin: 152
            # Left eye outer corner: 33
            # Right eye outer corner: 263
            # Left ear: 234
            # Right ear: 454

            nose_tip = np.array([face_landmarks.landmark[1].x * w, face_landmarks.landmark[1].y * h])
            chin = np.array([face_landmarks.landmark[152].x * w, face_landmarks.landmark[152].y * h])
            left_eye = np.array([face_landmarks.landmark[33].x * w, face_landmarks.landmark[33].y * h])
            right_eye = np.array([face_landmarks.landmark[263].x * w, face_landmarks.landmark[263].y * h])
            left_ear = np.array([face_landmarks.landmark[234].x * w, face_landmarks.landmark[234].y * h])
            right_ear = np.array([face_landmarks.landmark[454].x * w, face_landmarks.landmark[454].y * h])

            # Calculate face orientation using key points
            face_center_x = (left_eye[0] + right_eye[0]) / 2
            face_center_y = (left_eye[1] + right_eye[1]) / 2

            # Calculate roll (rotation around Z-axis) using eye line
            eye_line_angle = math.atan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]) * 180 / math.pi

            # Calculate yaw (left-right rotation) using ear positions
            ear_center_x = (left_ear[0] + right_ear[0]) / 2
            ear_center_y = (left_ear[1] + right_ear[1]) / 2

            # Yaw based on nose position relative to face center
            yaw_offset = nose_tip[0] - face_center_x
            yaw_threshold = w * 0.05  # 5% of frame width

            # Pitch based on nose position relative to eye level
            pitch_offset = nose_tip[1] - face_center_y
            pitch_threshold = h * 0.03  # 3% of frame height

            # Determine head direction
            if abs(eye_line_angle) > 15:  # Significant roll
                if eye_line_angle > 15:
                    return "Head Tilted Right"
                else:
                    return "Head Tilted Left"
            elif abs(yaw_offset) > yaw_threshold:
                if yaw_offset > yaw_threshold:
                    return "Looking Right"
                else:
                    return "Looking Left"
            elif abs(pitch_offset) > pitch_threshold:
                if pitch_offset > pitch_threshold:
                    return "Looking Down"
                else:
                    return "Looking Up"
            else:
                return "Looking Forward"

    except Exception as e:
        print(f"Head pose estimation error: {e}")
        return "Unknown"

def estimate_head_pose_opencv(frame):
    """
    Fallback head pose estimation using OpenCV Haar cascades.
    Basic implementation using face detection.
    """
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Load face cascade
        face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(face_cascade_path)

        if face_cascade.empty():
            return "Unknown"

        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) == 0:
            return "No Face Detected"

        # Get the largest face
        face = max(faces, key=lambda x: x[2] * x[3])
        x, y, w, h = face

        # Simple heuristic based on face position in frame
        frame_center_x = frame.shape[1] / 2
        frame_center_y = frame.shape[0] / 2

        face_center_x = x + w/2
        face_center_y = y + h/2

        x_offset = face_center_x - frame_center_x
        y_offset = face_center_y - frame_center_y

        threshold_x = frame.shape[1] * 0.2
        threshold_y = frame.shape[0] * 0.15

        if abs(x_offset) > threshold_x:
            return "Looking Right" if x_offset > 0 else "Looking Left"
        elif abs(y_offset) > threshold_y:
            return "Looking Down" if y_offset > 0 else "Looking Up"
        else:
            return "Looking Forward"

    except Exception as e:
        print(f"OpenCV head pose estimation error: {e}")
        return "Unknown"


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
