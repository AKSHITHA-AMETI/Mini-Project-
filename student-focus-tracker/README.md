# Student Focus Tracker

A web-based application for tracking student attention during online meetings using computer vision and machine learning.

## Features

- **Role-based Login**: Separate interfaces for students, teachers, and admins
- **Student ID Tracking**: Each student tracked by unique ID
- **Meeting Integration**: Students can join Google Meet meetings, participants tracked
- **Real-time Focus Tracking**: Webcam-based attention monitoring (students only)
- **Face Detection Alerts**: Alerts sent to student and admin if face not detected
- **Teacher Dashboard**: Monitor student focus scores and trends
- **Admin Access**: View all classes and participants
- **Multi-device Support**: Students can join from different devices
- **Data Persistence**: MongoDB database for storing attention data
- **Deployment Ready**: Docker support for easy deployment

## Setup

1. Install MongoDB locally or use Docker.

2. Install dependencies:
```bash
pip install -r req.txt
```

3. Set environment variables:
   - JWT_SECRET_KEY
   - MAIL_USERNAME (Gmail)
   - MAIL_PASSWORD (Gmail app password)
   - ADMIN_PASSWORD (for admin login)

4. Start the backend API server:
```bash
python server.py
```

5. For deployment with Docker:
```bash
docker-compose up --build
```

## API Endpoints

- POST /register: Register user
- POST /login: Student/Teacher login
- POST /admin_login: Admin login
- POST /classes: Create class
- GET /classes: Get classes (optional ?status=active/upcoming/completed)
- POST /classes/<class_id>/status: Set class status
- POST /frame: Send frame data (students)
- GET /history/<class_id>: Get frame history (optional ?student_email=...&limit=...)
- GET /stats/<class_id>: Get stats (optional ?student_email=...)
- GET /meeting_participants/<class_id>: Get all joined students
- GET /students: Get all students (for teacher selection)

### For Teachers:
1. Register/Login with email/password
2. Create classes with meeting URLs
3. View student focus data

### For Admins:
1. Login with admin email and fixed password
2. Access all data

## API Endpoints

- POST /register: Register user
- POST /login: Student/Teacher login
- POST /admin_login: Admin login
- POST /classes: Create class
- GET /classes: Get classes
- POST /frame: Send frame data (students)
- GET /meeting_participants/<class_id>: Get all joined students
- And more...

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