import cv2
import mediapipe as mp

mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils


def detect_faces(frame, model_selection=0, min_detection_confidence=0.5):
    """Detect faces in a frame and return the detection list."""
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
            bboxC = detection.location_data.relative_bounding_box
            x1 = int(bboxC.xmin * w)
            y1 = int(bboxC.ymin * h)
            x2 = int((bboxC.xmin + bboxC.width) * w)
            y2 = int((bboxC.ymin + bboxC.height) * h)
            detections.append(((x1, y1), (x2, y2), detection.score[0]))
    return detections


def annotate_faces(frame, detections):
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
