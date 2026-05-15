# Student Focus Tracker

## Project Overview

**Student Focus Tracker** is an AI-powered real-time monitoring system designed to track and analyze student attention levels during online/classroom sessions. Using advanced computer vision and machine learning techniques, the system captures behavioral cues (gaze, head pose, yawning, laughing) to compute a comprehensive focus score and helps educators identify when students need intervention.

### Key Features
- 🎥 **Real-time Face Detection & Analysis** - Detects faces and extracts behavioral cues
- 👁️ **Gaze Tracking** - Monitors eye direction (forward, left, right, up, down, closed)
- 🧠 **Head Pose Estimation** - Tracks head orientation relative to the screen
- 😴 **Yawn Detection** - Identifies fatigue indicators
- 😄 **Laugh Detection** - Monitors emotional state
- 📊 **Focus Score Calculation** - Composite score (0-10) based on multiple behavioral indicators
- 🔐 **User Authentication** - Role-based access (Student, Teacher, Admin)
- 📈 **Dashboard Analytics** - Visual dashboards for tracking focus metrics
- 💾 **Data Persistence** - MongoDB backend for historical data
- ☁️ **Cloud Upload** - Optional server-based data synchronization

---

## Hardware Requirements

### Minimum Requirements
- **Processor**: Intel i5 / AMD Ryzen 5 (or equivalent)
- **RAM**: 4GB (8GB recommended for smooth performance)
- **Storage**: 2GB free space for installation and data logs
- **Webcam**: USB/Built-in camera with minimum 720p resolution (1080p recommended)
- **Internet**: Broadband connection (for server communication and uploads)
- **Display**: 1920x1080 resolution or higher

### Recommended Requirements
- **Processor**: Intel i7 / AMD Ryzen 7 or better
- **RAM**: 16GB
- **Storage**: SSD with 10GB free space
- **Webcam**: 1080p or 4K for better accuracy
- **GPU**: NVIDIA CUDA-enabled GPU (for TensorFlow/PyTorch acceleration)

---

## Software Requirements

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, Ubuntu 18.04+
- **Python**: Version 3.8 or higher
- **Node.js**: Version 16.0 or higher (for frontend)
- **MongoDB**: Version 4.4 or higher (can be cloud-hosted via MongoDB Atlas)

### Key Dependencies

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Computer Vision** | OpenCV | 4.8+ | Video capture and image processing |
| | MediaPipe | 0.8+ | Face mesh, detection, pose estimation |
| | TensorFlow | 2.10+ | Deep learning for emotion/laugh detection |
| | PyTorch | 1.10+ | ML model inference |
| **Backend** | Flask | 2.0+ | REST API server |
| | Flask-CORS | Latest | Cross-origin resource sharing |
| | PyMongo | 4.0+ | MongoDB database connection |
| **Frontend** | React | 19.2+ | UI framework |
| | Vite | 6.4+ | Build tool |
| | Axios | 1.15+ | HTTP client |
| | Chart.js | 4.5+ | Data visualization |
| **Database** | MongoDB | 4.4+ | NoSQL database |
| **ML/Analytics** | NumPy | 1.24+ | Numerical computations |
| | Scikit-learn | 1.0+ | Machine learning algorithms |
| | SciPy | 1.10+ | Scientific computing |
| **Authentication** | PyJWT | Latest | JWT token handling |
| **Environment** | python-dotenv | Latest | Environment variable management |
| **Dashboard** | Streamlit | Latest | Analytics dashboard |

---

## Technology Stack & Purpose

### 1. **Backend (Python + Flask)**
- **Main Server** ([server.py](server.py))
  - RESTful API endpoints for authentication, data management, and live tracking
  - JWT-based authentication for secure access
  - MongoDB integration for data persistence
  - Email notifications via Flask-Mail
  - CORS support for frontend communication

### 2. **Computer Vision & Detection** (utils/)

#### [face_detection.py](utils/face_detection.py)
- **Purpose**: Detects faces in video frames
- **Technology**: MediaPipe Face Detection with OpenCV fallback
- **Output**: Face bounding boxes and detection confidence
- **Why**: Foundation for all behavioral analysis - must detect faces first

#### [gaze_tracking.py](utils/gaze_tracking.py)
- **Purpose**: Estimates eye gaze direction
- **Technology**: MediaPipe Face Mesh (478 facial landmarks)
- **Output**: Gaze classification ("Looking Forward", "Looking Left", "Eyes Closed", etc.)
- **Why**: Direct indicator of attention level and screen engagement

#### [head_pose.py](utils/head_pose.py)
- **Purpose**: Estimates head orientation in 3D space
- **Technology**: MediaPipe facial landmarks with angle calculations
- **Output**: Head direction ("Looking Forward", "Looking Down", "Head Tilted Left", etc.)
- **Why**: Supplementary attention indicator - head turned away = potential distraction

#### [yawn_detection.py](utils/yawn_detection.py)
- **Purpose**: Detects yawning behavior
- **Technology**: Mouth aspect ratio analysis, AI model inference
- **Output**: Binary (yawning/not yawning) + intensity metrics
- **Why**: Indicates fatigue and reduced alertness

#### [laugh_detection.py](utils/laugh_detection.py)
- **Purpose**: Detects laughing/smiling behavior
- **Technology**: Face emotion recognition models (TensorFlow/PyTorch)
- **Output**: Laugh probability + mouth width/height measurements
- **Why**: Monitors emotional state and classroom behavior

#### [focus_score.py](utils/focus_score.py)
- **Purpose**: Computes composite focus score from multiple cues
- **Technology**: State tracking with temporal stability analysis
- **Algorithm**: 
  - Combines gaze, head pose, yawn, and laugh signals
  - Applies stability weighting (prevents false positives)
  - Final score: 0-10 scale
- **Why**: Provides unified metric for focus level assessment

### 3. **Frontend (React + Vite)**
- **Framework**: React 19.2 with Vite for fast development
- **Components**:
  - [Login.jsx](frontend/src/components/Login.jsx) - User authentication
  - [Register.jsx](frontend/src/components/Register.jsx) - Account creation
  - [StudentDashboard.jsx](frontend/src/components/StudentDashboard.jsx) - Real-time tracking interface
  - [TeacherDashboard.jsx](frontend/src/components/TeacherDashboard.jsx) - Analytics and monitoring
  - [AdminDashboard.jsx](frontend/src/components/AdminDashboard.jsx) - System administration
- **State Management**: React hooks (useState, useContext)
- **HTTP Client**: Axios for API communication
- **Charting**: Chart.js with react-chartjs-2 for visualizations
- **Styling**: CSS modules for component isolation
- **Build**: Vite for optimized production builds

### 4. **Analytics Dashboard (Streamlit)**
- **File**: [dashboard/app.py](dashboard/app.py)
- **Purpose**: Real-time analytics and historical data visualization
- **Features**:
  - Focus score trends over time
  - Student statistics and comparisons
  - Real-time focus tracking interface
  - PDF report generation
  - Process management for focus trackers

### 5. **Database (MongoDB)**
- **Type**: NoSQL document database
- **Data Collections**:
  - `users` - User profiles (students, teachers, admins)
  - `classes` - Class information and enrollment
  - `focus_records` - Individual focus tracking records (timestamp, student_id, focus_score, behavioral_cues)
  - `focus_sessions` - Aggregated session data
- **Why**: Flexible schema for varied sensor data, horizontal scalability

### 6. **Core Application** ([main.py](main.py))
- **Purpose**: Main focus tracking engine
- **Features**:
  - Continuous video capture and frame processing
  - Local data logging to JSON
  - Server data upload with configurable intervals
  - Command-line configuration via argparse
  - Error handling and graceful shutdown
- **Modes**:
  - Local-only (saves to file, no server)
  - Server-sync (uploads to backend)
  - Hybrid (local + server)

---

## Installation & Setup

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd student-focus-tracker
```

### Step 2: Create Python Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Dependencies
```bash
pip install -r req.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the root directory:

```env
# Flask Configuration
FLASK_ENV=development
FLASK_APP=server.py
FLASK_DEBUG=True
JWT_SECRET_KEY=your-secret-key-change-this

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=student_focus_tracker

# API Configuration
FOCUS_API_URL=http://127.0.0.1:5000
FOCUS_RECORDINGS_DIR=./recordings

# Email Configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Client URL
CLIENT_URL=http://localhost:5173
```

### Step 5: Initialize Database
```bash
python init_db.py
```

### Step 6: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### Step 7: Start MongoDB Service
```bash
# Windows (if installed locally)
mongod

# macOS (using Homebrew)
brew services start mongodb-community

# Linux
sudo systemctl start mongod
```

---

## Running the Application

### Option 1: Full Stack (Recommended)

**Terminal 1 - Backend API Server:**
```bash
python server.py
# Server runs at http://127.0.0.1:5000
```

**Terminal 2 - Frontend Development Server:**
```bash
cd frontend
npm run dev
# Frontend runs at http://localhost:5173
```

**Terminal 3 - Initialize Focus Tracking:**
```bash
# Local mode (saves to file)
python main.py --class-id CLASS123

# Server mode (uploads to API)
python main.py --class-id CLASS123 --upload

# Custom configuration
python main.py --class-id CLASS123 --display --upload --interval 30
```

**Terminal 4 - Analytics Dashboard (Optional):**
```bash
streamlit run dashboard/app.py
# Dashboard runs at http://localhost:8501
```

### Option 2: Production Deployment
```bash
# Build frontend
cd frontend
npm run build

# Run with production server
gunicorn -w 4 -b 0.0.0.0:5000 server:app

# Run focus tracker as daemon
python main.py --class-id PROD_CLASS --upload &
```

---

## Important Code Snippets

### 1. **Focus Score Calculation Algorithm** (focus_score.py)
```python
def compute_focus_score(gaze, head_direction, yawn, laugh, 
                       mouth_distance=0.0, mouth_width=0.0, mouth_height=0.0):
    """
    Compute comprehensive focus score based on multiple behavioral cues.
    
    Returns: float focus score (0-10 scale)
    
    Algorithm:
    - Eye contact score: Forward=1.0, Sides=0.6, Up/Down=0.3, Closed=0.0
    - Head attention: Forward=1.0, Sides/Down=0.5, Up=0.3
    - Fatigue penalty: Yawning reduces score by 2-3 points
    - Distraction penalty: Laughing/non-forward gaze reduces by 1-2 points
    - Stability factor: Applies temporal smoothing to prevent jitter
    
    Example:
    score = compute_focus_score(
        gaze="Looking Forward",
        head_direction="Looking Forward",
        yawn=False,
        laugh=False
    )
    # Returns: 9.5 (high focus)
    """
    stability = state_tracker.update(gaze, head_direction, yawn, laugh)
    
    # Base scores
    eye_contact_score = 1.0 if gaze == "Looking Forward" else lower_scores
    head_attention_score = 1.0 if head_direction == "Looking Forward" else lower_scores
    
    # Composite score
    base_score = (eye_contact_score * 0.5) + (head_attention_score * 0.3)
    
    # Apply penalties
    if yawn:
        base_score -= 2.5 * stability['yawning_stability']
    if laugh:
        base_score -= 1.5 * stability['laughing_stability']
    
    # Normalize to 0-10 scale
    focus_score = max(0, min(10, base_score * 10))
    return focus_score
```

### 2. **Face Detection with MediaPipe** (face_detection.py)
```python
def detect_faces(frame, model_selection=0, min_detection_confidence=0.5):
    """
    Detect faces using MediaPipe or OpenCV fallback.
    
    Args:
        frame: Input video frame (numpy array)
        model_selection: 0=short-range (2m), 1=full-range (5m)
        min_detection_confidence: Threshold for face detection
    
    Returns:
        List of detected faces with bounding boxes
    
    Example:
    detections = detect_faces(frame, min_detection_confidence=0.7)
    for face in detections:
        x, y, w, h = face['bbox']
        confidence = face['confidence']
    """
    with mp_face_detection.FaceDetection(
        model_selection=model_selection,
        min_detection_confidence=min_detection_confidence
    ) as face_detection:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb)
        
        detections = []
        if results.detections:
            for detection in results.detections:
                # Extract bounding box
                bbox = detection.location_data.relative_bounding_box
                h, w, _ = frame.shape
                x, y = int(bbox.xmin * w), int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                detections.append({
                    'bbox': (x, y, width, height),
                    'confidence': detection.score[0]
                })
        return detections
```

### 3. **Gaze Tracking with Eye Aspect Ratio** (gaze_tracking.py)
```python
def eye_aspect_ratio(eye_landmarks):
    """
    Calculate Eye Aspect Ratio (EAR) for blink/sleep detection.
    
    Formula: EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    
    Where p1-p6 are the eye landmark points:
    - EAR > 0.2: Eyes open
    - EAR < 0.15: Eyes closed (blinking/sleeping)
    
    Example:
    ear = eye_aspect_ratio([p1, p2, p3, p4, p5, p6])
    if ear < 0.15:
        print("Eyes closed - student may be sleeping")
    """
    v1 = calculate_distance(eye_landmarks[1], eye_landmarks[5])
    v2 = calculate_distance(eye_landmarks[2], eye_landmarks[4])
    h = calculate_distance(eye_landmarks[0], eye_landmarks[3])
    
    ear = (v1 + v2) / (2.0 * h) if h > 0 else 0
    return ear

def estimate_gaze(frame):
    """
    Estimate gaze direction using iris and pupil tracking.
    
    Returns: 
    - "Looking Forward" (centered iris)
    - "Looking Left" / "Looking Right" (iris off-center)
    - "Looking Up" / "Looking Down" (iris top/bottom)
    - "Eyes Closed" (low eye aspect ratio)
    """
    # Implementation uses iris center relative to eye region
    iris_center = calculate_iris_center(frame)
    eye_region = calculate_eye_region(frame)
    
    # Determine gaze direction based on iris position
    if iris_center in eye_region:
        return "Looking Forward"
    # ... other cases
```

### 4. **Flask API Server - Authentication** (server.py)
```python
@app.route('/register', methods=['POST'])
def register():
    """
    User registration endpoint.
    
    Request body:
    {
        "username": "student1",
        "email": "student1@example.com",
        "password": "secure_password",
        "role": "student" (or "teacher", "admin")
    }
    
    Response:
    {
        "success": true,
        "user_id": "507f1f77bcf86cd799439011",
        "message": "User registered successfully"
    }
    """
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'student')
    
    # Hash password
    hashed_password = generate_password_hash(password)
    
    # Create user document
    user_doc = {
        'username': username,
        'email': email,
        'password': hashed_password,
        'role': role,
        'created_at': datetime.now(timezone.utc)
    }
    
    result = db.users.insert_one(user_doc)
    return jsonify({
        'success': True,
        'user_id': str(result.inserted_id)
    }), 201

@app.route('/login', methods=['POST'])
def login():
    """
    User login endpoint.
    
    Returns JWT token for subsequent API calls.
    
    Request:
    {
        "username": "student1",
        "password": "secure_password"
    }
    
    Response:
    {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "user_id": "507f1f77bcf86cd799439011",
        "role": "student"
    }
    """
    data = request.get_json()
    user = db.users.find_one({'username': data.get('username')})
    
    if user and check_password_hash(user['password'], data.get('password')):
        token = jwt.encode({
            'user_id': str(user['_id']),
            'username': user['username'],
            'exp': datetime.utcnow() + timedelta(days=7)
        }, app.config['JWT_SECRET_KEY'])
        
        return jsonify({
            'token': token,
            'user_id': str(user['_id']),
            'role': user['role']
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401
```

### 5. **Real-time Focus Tracking - Main Loop** (main.py)
```python
def main():
    """
    Main focus tracking loop.
    
    Workflow:
    1. Capture frame from webcam
    2. Detect faces
    3. Extract behavioral cues (gaze, head, yawn, laugh)
    4. Compute focus score
    5. Save/upload data
    6. Repeat at ~30 FPS
    """
    import cv2
    from utils.face_detection import detect_faces
    from utils.gaze_tracking import estimate_gaze
    from utils.focus_score import compute_focus_score
    
    cap = cv2.VideoCapture(0)  # Webcam
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect faces
        detections = detect_faces(frame)
        
        for face in detections:
            # Extract behavioral cues
            gaze = estimate_gaze(frame[face_roi])
            head_pose = estimate_head_pose(frame[face_roi])
            yawn = detect_yawn(frame[face_roi])
            laugh = detect_laugh(frame[face_roi])
            
            # Compute focus score
            focus_score = compute_focus_score(gaze, head_pose, yawn, laugh)
            
            # Create tracking record
            tracking_data = {
                'class_id': CLASS_ID,
                'student_id': STUDENT_ID,
                'timestamp': datetime.utcnow(),
                'focus_score': focus_score,
                'gaze': gaze,
                'head_pose': head_pose,
                'yawning': yawn,
                'laughing': laugh
            }
            
            # Save locally
            save_focus_data(tracking_data)
            
            # Upload to server
            if UPLOAD_TO_SERVER:
                upload_focus_data(tracking_data)
        
        # Display results
        cv2.imshow('Focus Tracking', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
```

### 6. **React Frontend - Student Dashboard** (StudentDashboard.jsx)
```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Line } from 'react-chartjs-2';

export function StudentDashboard() {
    const [focusScore, setFocusScore] = useState(0);
    const [history, setHistory] = useState([]);
    const [stats, setStats] = useState({});
    
    useEffect(() => {
        // Fetch real-time focus score every 2 seconds
        const interval = setInterval(() => {
            axios.get('/api/current-focus', {
                headers: { 'Authorization': localStorage.getItem('token') }
            })
            .then(res => setFocusScore(res.data.focus_score))
            .catch(err => console.error(err));
        }, 2000);
        
        // Fetch historical data
        axios.get('/api/focus-history?limit=60', {
            headers: { 'Authorization': localStorage.getItem('token') }
        })
        .then(res => setHistory(res.data))
        .catch(err => console.error(err));
        
        return () => clearInterval(interval);
    }, []);
    
    const chartData = {
        labels: history.map(h => new Date(h.timestamp).toLocaleTimeString()),
        datasets: [{
            label: 'Focus Score',
            data: history.map(h => h.focus_score),
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
        }]
    };
    
    return (
        <div className="dashboard">
            <h2>Your Focus Score: {focusScore.toFixed(1)}/10</h2>
            <Line data={chartData} />
            <div className="stats">
                <p>Average: {stats.average?.toFixed(1)}</p>
                <p>Peak: {stats.peak?.toFixed(1)}</p>
                <p>Session Duration: {stats.duration} min</p>
            </div>
        </div>
    );
}
```

### 7. **MongoDB Data Schema** (Collections)
```javascript
// users collection
{
    _id: ObjectId,
    username: "student1",
    email: "student@example.com",
    password: "hashed_password",
    role: "student",  // or "teacher", "admin"
    created_at: ISODate,
    updated_at: ISODate
}

// focus_records collection
{
    _id: ObjectId,
    class_id: "CLASS123",
    student_id: ObjectId,
    timestamp: ISODate,
    focus_score: 8.5,
    gaze: "Looking Forward",
    head_pose: "Looking Forward",
    yawning: false,
    laughing: false,
    mouth_distance: 0.0,
    mouth_width: 0.0,
    mouth_height: 0.0,
    confidence: 0.95
}

// classes collection
{
    _id: ObjectId,
    name: "Computer Science 101",
    teacher_id: ObjectId,
    students: [ObjectId, ObjectId, ...],
    created_at: ISODate,
    schedule: [{ day: "Monday", time: "10:00-11:00" }]
}
```

---

## API Endpoints Reference

### Authentication
- **POST** `/register` - Register new user
- **POST** `/login` - User login, returns JWT token
- **POST** `/logout` - User logout

### Focus Tracking
- **GET** `/current-focus` - Get real-time focus score
- **GET** `/focus-history/{class_id}` - Get historical focus data
- **POST** `/focus-record` - Submit focus tracking record
- **GET** `/student-stats/{student_id}` - Get student statistics

### Classes
- **GET** `/classes` - List all classes
- **POST** `/classes` - Create new class
- **GET** `/classes/{class_id}` - Get class details
- **PUT** `/classes/{class_id}` - Update class
- **DELETE** `/classes/{class_id}` - Delete class

### Teacher/Admin
- **GET** `/class-statistics/{class_id}` - Get class-wide statistics
- **GET** `/reports/{class_id}` - Generate class report
- **POST** `/tracker/start/{class_id}` - Start focus tracking
- **POST** `/tracker/stop/{class_id}` - Stop focus tracking

---

## Usage Examples

### Example 1: Starting a Focus Tracking Session
```bash
python main.py --class-id CLASS001 --student-id STUDENT_123 --upload --interval 30
```

### Example 2: Accessing Dashboard
1. Open `http://localhost:5173` in browser
2. Login with credentials
3. If teacher/admin: View real-time class statistics
4. If student: View your focus score and history

### Example 3: Retrieving Focus Statistics
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/student-stats/STUDENT_123
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| No face detected | Ensure good lighting, camera at eye level, face clearly visible |
| Focus score erratic | Increase frame processing rate, check lighting conditions |
| MongoDB connection error | Verify MongoDB is running, check `MONGODB_URI` in `.env` |
| CORS errors | Ensure `FLASK_CORS` is configured with correct origins |
| Webcam not found | Check camera is connected, test with `cv2.VideoCapture(0)` |
| High CPU usage | Reduce frame resolution, decrease detection frequency |
| JWT token expired | Login again, tokens expire after 7 days by default |

---

## Project Structure Summary

```
student-focus-tracker/
├── main.py                 # Main focus tracking engine
├── server.py              # Flask API backend
├── init_db.py             # Database initialization
├── req.txt                # Python dependencies
├── .env                   # Environment variables (create this)
│
├── utils/                 # Core ML/Vision utilities
│   ├── face_detection.py  # Face detection module
│   ├── gaze_tracking.py   # Eye gaze estimation
│   ├── head_pose.py       # Head pose estimation
│   ├── yawn_detection.py  # Yawn detection
│   ├── laugh_detection.py # Laugh/emotion detection
│   └── focus_score.py     # Composite focus score
│
├── frontend/              # React web application
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── StudentDashboard.jsx
│   │   │   ├── TeacherDashboard.jsx
│   │   │   └── AdminDashboard.jsx
│   │   ├── api.js        # API service layer
│   │   └── App.jsx       # Main app component
│   ├── package.json
│   └── vite.config.js
│
└── dashboard/            # Streamlit analytics dashboard
    └── app.py

```

---

## Future Enhancements

- [ ] Multi-face tracking in group classes
- [ ] Mobile app support (React Native)
- [ ] Advanced emotion recognition (micro-expressions)
- [ ] Attention intervention system (alerts, recommendations)
- [ ] Integration with learning management systems (LMS)
- [ ] Predictive analytics for at-risk students
- [ ] Privacy mode / blur detection
- [ ] Multi-camera setup support
- [ ] Real-time intervention alerts
- [ ] Detailed GDPR compliance features

---

## License

MIT License - See LICENSE file for details

---

## Support & Contact

For issues, questions, or feature requests, please open an issue on the GitHub repository or contact the development team.

---

**Last Updated**: May 2026
**Version**: 1.0.0
