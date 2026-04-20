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

def estimate_yawn(frame, threshold=0.5, min_detection_confidence=0.5, min_tracking_confidence=0.5):
    """
    Detect yawning using MediaPipe Face Mesh.

    Returns: (is_yawning: bool, mouth_distance: float)
    """
    if not USE_MEDIAPIPE:
        # Fallback to basic OpenCV mouth detection
        return estimate_yawn_opencv(frame, threshold)

    try:
        with mp_face_mesh.FaceMesh(
            max_num_faces=1,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        ) as face_mesh:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            if not results.multi_face_landmarks:
                return (False, 0.0)

            face_landmarks = results.multi_face_landmarks[0]

            # MediaPipe face mesh landmarks for mouth
            # Upper lip: 13, Lower lip: 14
            # Left mouth corner: 61, Right mouth corner: 291
            # Upper inner lip: 12, Lower inner lip: 15

            h, w, _ = frame.shape

            # Get mouth landmarks
            upper_lip = (int(face_landmarks.landmark[13].x * w), int(face_landmarks.landmark[13].y * h))
            lower_lip = (int(face_landmarks.landmark[14].x * w), int(face_landmarks.landmark[14].y * h))

            # Calculate vertical mouth opening distance
            mouth_distance = calculate_distance(upper_lip, lower_lip)

            # Normalize by face width for consistent threshold
            face_width = calculate_distance(
                (face_landmarks.landmark[234].x * w, face_landmarks.landmark[234].y * h),  # Left face
                (face_landmarks.landmark[454].x * w, face_landmarks.landmark[454].y * h)   # Right face
            )

            normalized_distance = mouth_distance / face_width if face_width > 0 else 0

            # Yawning threshold (mouth open more than 50% of face width)
            is_yawning = normalized_distance > threshold

            return (is_yawning, mouth_distance)

    except Exception as e:
        print(f"Yawn detection error: {e}")
        return (False, 0.0)

def estimate_yawn_opencv(frame, threshold=25):
    """
    Fallback yawn detection using OpenCV Haar cascades.
    Less accurate but works without MediaPipe.
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Load mouth cascade (you might need to download this)
        mouth_cascade_path = cv2.data.haarcascades + 'haarcascade_smile.xml'
        mouth_cascade = cv2.CascadeClassifier(mouth_cascade_path)

        if mouth_cascade.empty():
            return (False, 0.0)

        # Detect mouths
        mouths = mouth_cascade.detectMultiScale(gray, 1.7, 11)

        if len(mouths) > 0:
            # Get the largest mouth detection
            mouth = max(mouths, key=lambda x: x[2] * x[3])
            x, y, w, h = mouth

            # Simple heuristic: if mouth is wide enough, consider it yawning
            mouth_ratio = w / h if h > 0 else 0
            is_yawning = mouth_ratio > 2.0  # Wide mouth ratio indicates yawning

            return (is_yawning, float(w))
        else:
            return (False, 0.0)

    except Exception as e:
        print(f"OpenCV yawn detection error: {e}")
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
