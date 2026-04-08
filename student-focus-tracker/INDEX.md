# Student Focus Tracker - Project Index

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **IMPLEMENTATION.md** | ✅ Complete feature summary & architecture |
| **QUICK_START.md** | 🚀 Step-by-step setup and usage guide |
| **FEATURES.md** | 📖 Detailed feature documentation |
| **README.md** | 📝 Original project overview |
| **INDEX.md** | 📋 This file - project roadmap |

---

## 📂 Project Structure

```
student-focus-tracker/
├── server.py              ← Backend API (Flask)
├── main.py                ← Focus tracker (webcam)
├── dashboard/
│   └── app.py            ← Frontend (Streamlit)
├── utils/
│   ├── face_detection.py
│   ├── gaze_tracking.py
│   ├── head_pose.py
│   ├── yawn_detection.py
│   ├── laugh_detection.py
│   └── focus_score.py
├── data/
│   └── logs.csv
│   └── attention.db      ← SQLite database
├── req.txt               ← Python dependencies
├── init_db.py            ← Database initialization
├── IMPLEMENTATION.md     ← Feature summary
├── QUICK_START.md        ← Setup guide
├── FEATURES.md           ← Detailed docs
└── README.md             ← Project overview
```

---

## 🎯 Core Features Implemented

### ✅ Role-Based System
- **Students**: View classes, join links, start tracking
- **Teachers**: Create classes, add links, monitor students

### ✅ Authentication
- Secure registration and login
- Password hashing (PBKDF2-SHA256)
- Session management

### ✅ Class Management
- Teachers create and schedule classes
- Add meeting links (Zoom, Google Meet)
- Students enroll in classes
- Real-time student analytics

### ✅ Focus Tracking
- Associates data with specific classes
- Tracks per student per class
- Shows focus metrics in teacher dashboard

### ✅ Security
- Links hidden from unregistered users
- Enrollment required for link visibility
- Role-based access control

---

## 🚀 Quick Start Commands

### Setup
```bash
pip install -r req.txt
python init_db.py
```

### Run System
```bash
# Terminal 1
python server.py

# Terminal 2
streamlit run dashboard/app.py

# Terminal 3 (after starting tracking from dashboard)
python main.py "student_username" <class_id>
```

### Access
- Dashboard: http://localhost:8501
- Backend: http://127.0.0.1:5000

---

## 👥 User Workflows

### Teacher: Setup Class
1. Register as teacher
2. Create class "Math 101"
3. Add Zoom link
4. Receive class ID
5. Share with students
6. View student focus data in real-time

### Student: Attend Class
1. Register as student
2. Request enrollment from teacher
3. Log in, see class in list
4. Click "Join Class" for Zoom link
5. Click "Start Tracking"
6. Run focus tracker with class ID
7. Data appears in teacher dashboard

---

## 📊 Data Models

### User
```
id, username, password_hash, email, role, created_at
```

### Class
```
id, teacher_id, class_name, scheduled_time, created_at
```

### Enrollment
```
id, class_id, student_id, enrolled_at
```

### Class Link
```
id, class_id, link, created_at
```

### Frame (Focus Data)
```
id, timestamp, student_id, class_id, gaze, head_direction,
yawning, mouth_distance, laughing, mouth_width, mouth_height, focus_score
```

---

## 🔌 API Endpoints

### Authentication
```
POST /auth/register     - Create new user
POST /auth/login        - Log in user
```

### Classes
```
GET  /classes           - List user's classes
POST /classes           - Create new class
POST /classes/<id>/link - Add meeting link
GET  /classes/<id>/students - Get class analytics
```

### Tracking
```
POST /frame            - Record focus data
GET  /history          - Get historical data
GET  /stats            - Get overall statistics
```

---

## 🔐 Security Features

✅ **Password Hashing**: PBKDF2-SHA256 with unique salt  
✅ **Link Privacy**: Hidden until enrollment  
✅ **Role-Verified**: Separate UIs and endpoints  
✅ **Session Management**: Streamlit session state  
✅ **Data Association**: Class-based tracking  

---

## 📁 Key Files & Changes

### ✨ New Files
- `init_db.py` - Database initialization helper
- `IMPLEMENTATION.md` - Architecture & features
- `QUICK_START.md` - Setup guide
- `FEATURES.md` - Detailed documentation
- `INDEX.md` - This file

### 🔄 Modified Files
- **server.py** - Added auth, classes, enrollments
- **dashboard/app.py** - Complete redesign (role-based)
- **main.py** - Added class tracking support
- **req.txt** - Updated dependencies

---

## 🧪 Testing Checklist

- ✅ Database initialization
- ✅ User registration (student/teacher)
- ✅ User login
- ✅ Class creation
- ✅ Meeting link addition
- ✅ Student enrollment
- ✅ Student dashboard display
- ✅ Teacher class management
- ✅ Focus tracking
- ✅ Analytics display

---

## ⚙️ Dependencies

Key packages:
- **Flask**: Backend API
- **Streamlit**: Frontend UI
- **MediaPipe**: AI detections
- **OpenCV**: Webcam & video
- **Pandas**: Data handling
- **SQLite**: Database (built-in)
- **NumPy**: Data processing

---

## 🎓 Usage Scenarios

### Scenario 1: Monitor Class Concentration
1. Teacher creates "History 101"
2. Adds Zoom meeting
3. 30 students enroll
4. All students start tracking in class
5. Teacher sees real-time focus metrics
6. Identifies struggling students
7. Provides targeted help

### Scenario 2: Track Personal Focus
1. Single student in class
2. Starts daily tracking
3. Monitor self-improvement over time
4. Teacher sees progress
5. Uses data for assessment

### Scenario 3: Multi-Class Administration
1. Teacher creates multiple classes
2. Different schedules and links
3. Manages all in single dashboard
4. Compares focus across classes
5. Analyzes trends

---

## 📞 Getting Help

**See documentation:**
1. **QUICK_START.md** - Getting started
2. **FEATURES.md** - Detailed features
3. **IMPLEMENTATION.md** - Architecture details
4. **Code comments** - Implementation details

**Common Issues:**
- Database won't initialize → Run `python init_db.py`
- Links not showing → Ensure student is enrolled
- No webcam → Check camera permissions
- Slow response → Restart backend server

---

## ✨ Status: COMPLETE ✅

All requested features have been successfully implemented:
- ✅ Student authentication and dashboard
- ✅ Teacher class creation and management
- ✅ Meeting links (hidden from non-enrolled users)
- ✅ Focus tracking with class association
- ✅ Real-time student analytics for teachers
- ✅ Secure authentication system
- ✅ Complete documentation

**Ready for production use!**

---

## 📅 Last Updated
April 1, 2026

## 🔄 Version
1.0 - Initial implementation with auth, classes, and analytics
