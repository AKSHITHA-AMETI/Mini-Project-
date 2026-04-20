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

def estimate_laugh(frame, width_threshold=0.8, height_threshold=0.3, min_detection_confidence=0.5, min_tracking_confidence=0.5):
    """
    Detect laughing using MediaPipe Face Mesh by analyzing mouth shape changes.

    Returns: (is_laughing: bool, mouth_width: float, mouth_height: float)
    """
    if not USE_MEDIAPIPE:
        # Fallback to basic OpenCV smile detection
        return estimate_laugh_opencv(frame, width_threshold, height_threshold)

    try:
        with mp_face_mesh.FaceMesh(
            max_num_faces=1,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        ) as face_mesh:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            if not results.multi_face_landmarks:
                return (False, 0.0, 0.0)

            face_landmarks = results.multi_face_landmarks[0]

            h, w, _ = frame.shape

            # MediaPipe face mesh landmarks for mouth corners and lips
            # Left mouth corner: 61, Right mouth corner: 291
            # Upper lip center: 13, Lower lip center: 14

            left_corner = (face_landmarks.landmark[61].x * w, face_landmarks.landmark[61].y * h)
            right_corner = (face_landmarks.landmark[291].x * w, face_landmarks.landmark[291].y * h)
            upper_lip = (face_landmarks.landmark[13].x * w, face_landmarks.landmark[13].y * h)
            lower_lip = (face_landmarks.landmark[14].x * w, face_landmarks.landmark[14].y * h)

            # Calculate mouth width (distance between corners)
            mouth_width = calculate_distance(left_corner, right_corner)

            # Calculate mouth height (distance between upper and lower lip)
            mouth_height = calculate_distance(upper_lip, lower_lip)

            # Normalize by face width for consistent threshold
            face_width = calculate_distance(
                (face_landmarks.landmark[234].x * w, face_landmarks.landmark[234].y * h),  # Left face
                (face_landmarks.landmark[454].x * w, face_landmarks.landmark[454].y * h)   # Right face
            )

            if face_width > 0:
                normalized_width = mouth_width / face_width
                normalized_height = mouth_height / face_width

                # Laughing detection: wide mouth with moderate height increase
                # Width > 80% of face width AND height > 30% of face width
                is_laughing = normalized_width > width_threshold and normalized_height > height_threshold
            else:
                is_laughing = False

            return (is_laughing, mouth_width, mouth_height)

    except Exception as e:
        print(f"Laugh detection error: {e}")
        return (False, 0.0, 0.0)

def estimate_laugh_opencv(frame, width_threshold=80, height_threshold=15):
    """
    Fallback laugh detection using OpenCV Haar cascades for smile detection.
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Load smile cascade
        smile_cascade_path = cv2.data.haarcascades + 'haarcascade_smile.xml'
        smile_cascade = cv2.CascadeClassifier(smile_cascade_path)

        if smile_cascade.empty():
            return (False, 0.0, 0.0)

        # Detect smiles
        smiles = smile_cascade.detectMultiScale(gray, 1.8, 20)

        if len(smiles) > 0:
            # Get the largest smile detection
            smile = max(smiles, key=lambda x: x[2] * x[3])
            x, y, w, h = smile

            # Check if smile meets size thresholds
            is_laughing = w > width_threshold and h > height_threshold

            return (is_laughing, float(w), float(h))
        else:
            return (False, 0.0, 0.0)

    except Exception as e:
        print(f"OpenCV laugh detection error: {e}")
        return (False, 0.0, 0.0)


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
