import cv2
import os

# Try to use mediapipe, fall back to OpenCV cascade classifier
USE_MEDIAPIPE = False
mp_face_detection = None
mp_drawing = None

try:
    import mediapipe.solutions.face_detection as mp_face_detection_module
    import mediapipe.solutions.drawing_utils as mp_drawing_module
    mp_face_detection = mp_face_detection_module
    mp_drawing = mp_drawing_module
    USE_MEDIAPIPE = True
except (ImportError, AttributeError, ModuleNotFoundError):
    try:
        import mediapipe as mp
        mp_face_detection = mp.solutions.face_detection
        mp_drawing = mp.solutions.drawing_utils
        USE_MEDIAPIPE = True
    except (ImportError, AttributeError, ModuleNotFoundError):
        USE_MEDIAPIPE = False

if not USE_MEDIAPIPE:
    # Load OpenCV cascade classifier as fallback
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)


def detect_faces(frame, model_selection=0, min_detection_confidence=0.5):
    """Detect faces in a frame and return the detection list."""
    global USE_MEDIAPIPE
    
    if USE_MEDIAPIPE:
        try:
            with mp_face_detection.FaceDetection(
                model_selection=model_selection,
                min_detection_confidence=min_detection_confidence,
            ) as face_detection:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_detection.process(rgb)

            detections = []
            if results.detections:
                h, w, _ = frame.shape
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    x1 = int(bbox.xmin * w)
                    y1 = int(bbox.ymin * h)
                    x2 = int((bbox.xmin + bbox.width) * w)
                    y2 = int((bbox.ymin + bbox.height) * h)
                    confidence = detection.score[0]
                    detections.append(((x1, y1), (x2, y2), confidence))
            return detections
        except Exception:
            # Fall back to cascade if mediapipe fails
            USE_MEDIAPIPE = False
    
    # OpenCV cascade classifier fallback
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    detections = []
    for (x, y, width, height) in faces:
        x1, y1 = x, y
        x2, y2 = x + width, y + height
        confidence = 0.7  # Dummy confidence score
        detections.append(((x1, y1), (x2, y2), confidence))
    return detections


def annotate_faces(frame, detections):
    """Draw bounding boxes and confidence scores on frame."""
    for (x1, y1), (x2, y2), score in detections:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            frame,
            f"{int(score * 100)}%",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )
    return frame


if __name__ == "__main__":
    cap = cv2.VideoCapture()
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        detections = detect_faces(frame)
        annotate_faces(frame, detections)

        cv2.imshow("Face Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
