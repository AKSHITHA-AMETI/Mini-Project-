# Student Focus Tracker

A web-based application for tracking student attention during online meetings using computer vision and machine learning.

## Features

- **Role-based Login**: Separate interfaces for students and teachers
- **Meeting Integration**: Students can join Zoom/Meet/Google Meet meetings directly from the app
- **Real-time Focus Tracking**: Webcam-based attention monitoring
- **Teacher Dashboard**: Monitor student focus scores and trends
- **Data Persistence**: SQLite database for storing attention data

## Setup

1. Install dependencies:
```bash
pip install -r req.txt
```

2. Start the backend API server:
```bash
python server.py
```

3. Start the webcam tracker (in another terminal):
```bash
python main.py
```

4. Launch the web interface:
```bash
streamlit run dashboard/app.py
```

## Usage

### For Students:
1. Select "Student" role and login
2. Enter your meeting URL (Zoom, Google Meet, etc.)
3. Click "Join Meeting & Start Tracking"
4. The meeting will open in your browser and focus tracking will begin

### For Teachers:
1. Select "Teacher" role and login
2. View real-time student focus metrics
3. Monitor attention trends over time
4. Access historical data

## Architecture

- **Frontend**: Streamlit web interface
- **Backend**: Flask REST API
- **Database**: SQLite
- **Computer Vision**: OpenCV + MediaPipe
- **Focus Detection**: Face detection, gaze tracking, head pose estimation

## API Endpoints

- `POST /frame`: Store attention frame data
- `GET /history`: Retrieve historical data
- `GET /stats`: Get summary statistics

## Files Structure

```
student-focus-tracker/
├── main.py                 # Webcam tracking application
├── server.py              # Flask API server
├── dashboard/
│   └── app.py            # Streamlit web interface
├── utils/
│   ├── face_detection.py
│   ├── gaze_tracking.py
│   ├── head_pose.py
│   ├── yawn_detection.py
│   ├── laugh_detection.py
│   └── focus_score.py
├── data/
│   └── attention.db      # SQLite database
└── req.txt               # Python dependencies
```