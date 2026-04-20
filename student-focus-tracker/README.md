# Student Focus Tracker

A comprehensive student attention monitoring system using advanced computer vision and machine learning techniques. The system runs locally on each student's device, providing real-time focus analysis without requiring internet connectivity for tracking.

## 🚀 Key Features

### Computer Vision & AI-Powered Tracking
- **Real-time Face Detection**: Uses MediaPipe and OpenCV for robust face detection
- **Gaze Tracking**: Eye Aspect Ratio (EAR) analysis for blink/sleep detection
- **Head Pose Estimation**: 3D head orientation analysis using facial landmarks
- **Yawn Detection**: Mouth landmark analysis for fatigue detection
- **Laugh Detection**: Smile recognition using mouth shape analysis
- **Sleep Detection**: Eye closure monitoring for drowsiness alerts

### Advanced Focus Scoring Algorithm
- **Multi-factor Analysis**: Combines gaze, head pose, and behavioral cues
- **Behavioral Stability Tracking**: Accounts for prolonged vs. momentary distractions
- **Weighted Scoring**: Intelligent weighting of different attention factors
- **Real-time Updates**: Continuous focus score computation (0-10 scale)

### Local Device Processing
- **No Internet Required**: All processing happens locally on student's device
- **Privacy-Focused**: No video data sent to servers
- **Offline Capable**: Works without network connectivity
- **Cross-Platform**: Compatible with Windows, macOS, and Linux

### Multi-Device Data Aggregation
- **Centralized Dashboard**: View data from all student devices in one place
- **Device Tracking**: Monitor which devices each student is using
- **Data Synchronization**: Upload local data to server when network available
- **Aggregated Analytics**: Combined focus scores across multiple devices

### Web-Based Management Interface
- **Role-based Access**: Separate dashboards for students, teachers, and admins
- **Multi-device Support**: Students can join from different devices
- **Meeting Integration**: Direct Google Meet integration
- **Real-time Monitoring**: Live focus score visualization
- **Data Analytics**: Historical focus trend analysis

## 🛠️ Technical Implementation

### Computer Vision Pipeline
```
Camera Input → Face Detection → Landmark Extraction → Feature Analysis → Focus Scoring → Local Storage
```

### Deep Learning Models Used
- **MediaPipe Face Mesh**: 468 facial landmarks for precise feature detection
- **OpenCV Haar Cascades**: Fallback detection for compatibility
- **Custom Algorithms**: Specialized yawn, laugh, and gaze detection
- **TensorFlow Lite**: Optimized deep learning inference

### Focus Score Components (Weighted)
- **Eye Contact (35%)**: Gaze direction and eye closure detection
- **Head Attention (30%)**: Head pose and orientation analysis
- **Behavioral Analysis (35%)**: Yawn, laugh, and distraction patterns

## 📋 Prerequisites

- Python 3.8+
- Webcam/Camera device
- OpenCV-compatible camera drivers
- 4GB+ RAM recommended
- Windows/macOS/Linux

## 🔧 Installation & Setup

### 1. Install Dependencies
```bash
pip install -r req.txt
```

### 2. Environment Configuration
Create a `.env` file with:
```env
JWT_SECRET_KEY=your_jwt_secret
MAIL_USERNAME=your_gmail@gmail.com
MAIL_PASSWORD=your_gmail_app_password
ADMIN_PASSWORD=your_admin_password
```

### 3. Start the Application

**Backend Server:**
```bash
python server.py
```

**Local Focus Tracking (on each student's device):**
```bash
python main.py <class_id> [--headless]
```

**Frontend Development:**
```bash
cd frontend
npm install
npm run dev
```

## 📤 Data Synchronization

### Uploading Local Data to Server
After running focus tracking locally, you can upload the collected data to the server for dashboard viewing:

```bash
python main.py <class_id> --upload
```

Or run the tracking with automatic upload:
```bash
python main.py <class_id> --upload --auto-upload-interval 300
```

### Manual Data Upload
If you have existing local data files, you can upload them manually:

```bash
python upload_data.py
```

This interactive script will guide you through uploading your `focus_tracking_log.json` file to the server.

### Multi-Device Dashboard Access
Once data is uploaded from multiple devices:
1. Open the teacher dashboard
2. Select your class
3. View aggregated data from all student devices
4. Monitor focus scores across different devices per student

### Data Privacy & Security
- **Local Processing**: All video analysis happens on-device
- **Optional Upload**: Data upload is completely optional
- **JWT Authentication**: Secure API endpoints with token-based auth
- **Device Tracking**: Each device upload is tracked separately

### 4. Docker Deployment
```bash
docker-compose up --build
```

## 🎯 Usage

### For Students
1. Register/Login through the web interface
2. Join a class using the teacher-provided URL
3. Click "Start Tracking" - the system automatically:
   - Accesses your camera
   - Runs computer vision analysis locally
   - Saves focus data to local JSON file
   - Opens the meeting URL

### For Teachers
1. Create classes through the teacher dashboard
2. Share class URLs with students
3. Monitor real-time focus scores
4. View historical analytics

### Local Tracking Features
- **Visual Feedback**: Real-time overlay showing detection results
- **Debug Mode**: Press 's' to save debug frames
- **Headless Mode**: Background tracking without display window
- **Data Export**: All focus data saved locally as JSON

## 🔍 Computer Vision Features Details

### Gaze Tracking
- **Eye Aspect Ratio (EAR)**: Detects eye blinks and closure
- **Pupil Position Analysis**: Determines gaze direction
- **Sleep Detection**: Prolonged eye closure triggers alerts

### Yawn Detection
- **Mouth Landmark Analysis**: Measures vertical mouth opening
- **Face-normalized Metrics**: Consistent detection across face sizes
- **Intensity Classification**: Distinguishes between mild and intense yawns

### Behavioral Analysis
- **State Persistence**: Tracks consecutive frames of behavior
- **Distraction Patterns**: Identifies prolonged vs. momentary attention loss
- **Multi-modal Scoring**: Combines visual cues for accurate assessment

## 📊 Data Storage

### Local JSON Storage
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "class_id": "507f1f77bcf86cd799439011",
  "device_id": "device_12345",
  "gaze": "Looking Forward",
  "head_direction": "Looking Forward",
  "yawning": false,
  "mouth_distance": 15.2,
  "laughing": false,
  "mouth_width": 45.8,
  "mouth_height": 12.3,
  "focus_score": 8.5,
  "faces_detected": 1
}
```

### Database Integration
- **MongoDB**: Stores user accounts, classes, and aggregated analytics
- **Real-time Sync**: Optional data upload when network available
- **Privacy Compliant**: No raw video data stored

## 🧪 Testing

### Run Feature Tests
```bash
python -c "
# Test script to verify all CV features
import cv2
from utils.face_detection import detect_faces
from utils.gaze_tracking import estimate_gaze
# ... (runs comprehensive tests)
"
```

### Demo Mode
```bash
python main.py demo_class_123 --demo
```

## 🔒 Privacy & Security

- **Local Processing**: All computer vision runs on-device
- **No Video Upload**: Raw camera feed never leaves the device
- **Data Ownership**: Students control their focus data
- **Opt-in Tracking**: Explicit user consent required
- **Secure Storage**: Local JSON files with optional encryption

## 🚀 Performance

- **Real-time Processing**: 30+ FPS on modern hardware
- **Low Resource Usage**: Optimized for laptops and desktops
- **Battery Efficient**: Minimal CPU/GPU usage
- **Multi-camera Support**: Automatic fallback camera detection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement computer vision improvements
4. Add comprehensive tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **MediaPipe**: For advanced facial landmark detection
- **OpenCV**: For computer vision foundation
- **TensorFlow**: For deep learning capabilities
- **Flask**: For robust web API development
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