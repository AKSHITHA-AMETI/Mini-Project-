import cv2
from utils.face_detection import detect_faces, annotate_faces
from utils.gaze_tracking import estimate_gaze
from utils.head_pose import estimate_head_pose
from utils.yawn_detection import estimate_yawn
from utils.laugh_detection import estimate_laugh
from utils.focus_score import compute_focus_score


def run_attention_tracker():
    cap = cv2.VideoCapture(0)
    frame_count = 0

    if not cap.isOpened():
        print("Error: Webcam not found.")
        return

    print("Starting Student Focus Tracker. Press 'q' to stop.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % 2 != 0:
            # reduce processing load by half, keep a fast preview
            cv2.imshow("Focus Tracker", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue

        # Core detectors
        face_detections = detect_faces(frame)
        gaze = estimate_gaze(frame)
        head_direction = estimate_head_pose(frame)
        yawning, mouth_distance = estimate_yawn(frame)
        laughing, width, height = estimate_laugh(frame)

        focus_score = compute_focus_score(gaze, head_direction, yawning, laughing)

        # Visual overlays
        annotate_faces(frame, face_detections)
        cv2.putText(frame, f"Gaze: {gaze}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Head: {head_direction}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Yawn: {yawning} / {int(mouth_distance)}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"Laugh: {laughing} / W:{int(width)} H:{int(height)}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"Focus Score: {focus_score}%", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow("Focus Tracker", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_attention_tracker()
