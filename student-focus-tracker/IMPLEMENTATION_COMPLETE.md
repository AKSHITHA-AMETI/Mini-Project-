# Complete Focus Tracking System Implementation

## ✅ What Has Been Implemented

### 1. **Backend API Endpoints** (`server.py`)

#### Focus Tracking
- **`POST /frame`** - Receive real-time tracking frame data from the tracking subprocess
- **`POST /start-tracking/<class_id>`** - Start camera tracking for a class
- **`POST /stop-tracking/<class_id>`** - Stop tracking and clean up subprocess
- **`POST /classes/<class_id>/complete`** - Manually mark a class as completed

#### Teacher Dashboard
- **`GET /teacher/classes`** - Get all teacher's classes with detailed student statistics
- **`GET /teacher/classes/<class_id>`** - Get detailed analytics for a specific class
  - Student focus scores (min, max, average)
  - Behavioral events (yawning, laughing, eyes closed)
  - Focus distribution (low/medium/high)

#### Admin Dashboard
- **`GET /admin/dashboard`** - Comprehensive system statistics
  - System users (total, students, teachers, admins)
  - Class overview (total, active, upcoming, completed)
  - Tracking statistics (total frames, average focus)
  - Behavioral events summary
  - Top teachers by class count

### 2. **Focus Calculation System**

Focus scores are calculated based on:
- **Gaze Direction** (35% weight):
  - Looking Forward = 1.0 (full attention)
  - Looking Left/Right = 0.6 (partial attention)
  - Looking Up/Down = 0.3 (minimal attention)
  - Eyes Closed = 0.0 (sleeping/not paying attention)

- **Head Direction** (30% weight):
  - Looking Forward = 1.0
  - Looking Left/Right = 0.7
  - Looking Up/Down = 0.4
  - Head Tilted = 0.2

- **Behavioral Expression** (35% weight):
  - Based on yawning, laughing, and eyes closed detection
  - Penalties applied for each behavior
  - Sleep penalty is most severe (0.8-1.0)

**Focus Score Range: 0-10 scale**
- 0-3: Low focus (requires attention)
- 4-6: Medium focus (acceptable)
- 7-10: High focus (excellent)

### 3. **Real-Time Tracking** (`main.py`)

The tracking subprocess now:
- ✅ Sends frames in real-time to `/frame` endpoint (instead of batch uploads)
- ✅ Calculates focus based on yawn, laugh, and eyes_closed detection
- ✅ Saves data locally as JSON
- ✅ Supports headless mode (background tracking without display)
- ✅ Handles camera fallback (tries indices 0-4)
- ✅ Accepts command-line arguments: `python main.py <class_id> <token> [--headless] [--no-upload]`

**Detection Metrics Tracked:**
- Gaze direction (9 possible values)
- Head pose (forward, left, right, up, down, tilted)
- Yawning (boolean + mouth_distance)
- Laughing (boolean + mouth_width, mouth_height)
- Face count per frame
- Focus score

### 4. **Student Dashboard**

**Features:**
- ✅ Join available classes via URL
- ✅ View all classes (my classes, available, upcoming, completed)
- ✅ Start tracking for active classes with **one-click**
- ✅ **NEW: Stop tracking button** that appears when tracking is active
- ✅ Real-time meeting URL redirect
- ✅ Focus history chart visualization
- ✅ Status messages showing tracking status

**Tracking Flow:**
1. Click "Start Tracking" for an active class
2. Backend launches Python subprocess with camera access
3. Subprocess sends frames in real-time to `/frame` endpoint
4. Meeting URL opens in new tab
5. Student can stop tracking anytime with "Stop Tracking" button
6. Focus data automatically saved and reflected on dashboards

### 5. **Teacher Dashboard**

**Class Overview:**
- Create new classes with meeting URLs
- View all classes with student count and average focus
- Copy student join links for sharing

**Detailed Analytics (per class):**
- ✅ Student attendance status
- ✅ Average focus score per student
- ✅ Low focus frame count per student
- ✅ Behavioral events (yawning, laughing, eyes closed)
- ✅ Focus distribution (pie chart showing low/medium/high)
- ✅ Multi-device tracking support (shows devices per student)
- ✅ Last activity timestamp
- ✅ Total frames received per student

### 6. **Admin Dashboard**

**System Metrics:**
- ✅ Total users breakdown (students, teachers, admins)
- ✅ Total classes by status (active, upcoming, completed)
- ✅ Focus tracking statistics (total frames, average focus)
- ✅ Behavioral events summary (total yawning, laughing, eyes closed)
- ✅ Top teachers ranking (by class count and students taught)

### 7. **Class Management**

**Status Transitions:**
- Upcoming → Active (when current time reaches start time)
- Active → Completed (when current time exceeds end time OR teacher marks complete)
- Teachers can manually complete a class anytime

**Tracking Lifecycle:**
- Class must be "active" to start tracking
- Tracking creates subprocess that runs until:
  - Student clicks "Stop Tracking"
  - Teacher stops the class
  - Class time expires
  - Student closes the app

---

## 🚀 How to Use

### Starting the System

1. **Backend Server** (already running on http://10.176.131.7:5000):
   ```bash
   python server.py
   ```

2. **Frontend** (already built and served):
   Access at: http://10.176.131.7:3005 (or your machine's IP)

### Student Workflow

1. **Register/Login** as a student
2. **Join a class** - Either:
   - Find it in "Available Classes" tab
   - Use teacher-provided join link: `http://ip:3005/student?join=<class_id>`
3. **When class is active**, click **"🎥 Start Tracking"**
4. **Meeting URL opens** and camera tracking starts in background
5. **View your focus history** in the class details
6. Click **"⏹ Stop Tracking"** when done

### Teacher Workflow

1. **Register/Login** as a teacher
2. **Create a class** with:
   - Class name
   - Start/end times
   - Meeting URL (e.g., Google Meet, Zoom link)
3. **Copy student join link** and share with students
4. **During class**, view real-time focus analytics:
   - Student attendance
   - Average focus scores
   - Behavioral events
   - Focus distribution
5. **Mark class as complete** when finished

### Admin Workflow

1. **View system dashboard** with:
   - Total users and class statistics
   - Focus tracking metrics
   - Behavioral events summary
   - Top performing teachers

---

## 📊 Data Flow

```
Student Device
    ↓ (Camera)
    ↓ (main.py subprocess)
    ↓ (Real-time frames via /frame)
    ↓
Backend API (server.py)
    ↓ (Store in MongoDB)
    ↓
Dashboards
    ↓ (Teachers/Admins view analytics)
    ↓
Insights (Focus improvement recommendations)
```

---

## 🎯 Key Features Summary

| Feature | Status | Details |
|---------|--------|---------|
| Real-time camera tracking | ✅ | Via subprocess sending frames to /frame endpoint |
| Focus calculation | ✅ | Based on gaze, head direction, behavioral cues |
| Yawn detection | ✅ | Included in focus penalties |
| Sleep/eyes-closed detection | ✅ | Most severe focus penalty (0.8-1.0) |
| Laugh detection | ✅ | Included in behavioral penalties |
| Stop tracking | ✅ | Student can stop anytime with button |
| Class completion | ✅ | Automatic (time-based) or manual (teacher) |
| Multi-device support | ✅ | Tracks multiple devices per student |
| Teacher analytics | ✅ | Detailed per-student and class-wide stats |
| Admin dashboard | ✅ | System-wide metrics and top teachers |
| Network detection | ✅ | Auto-detects server IP for multi-device access |

---

## 🔧 Technical Stack

- **Backend**: Flask + MongoDB Atlas
- **Frontend**: React + Vite + Axios
- **Tracking**: Python + OpenCV + MediaPipe
- **Real-time**: HTTP POST requests to /frame endpoint
- **Authentication**: JWT tokens
- **Timezone**: IST (Asia/Kolkata)

---

## 📝 Notes

- Focus scores are calculated every 8-10 seconds (randomized to prevent prediction)
- Frames are sent to server in real-time (3-second timeout)
- Local JSON file maintained for backup
- Camera fallback: tries indices 0-4 to find available camera
- Headless mode: tracking runs without display window (for server deployments)

---

## 🐛 Troubleshooting

**Issue:** Camera not accessing
- Solution: Check permissions, try different camera index (--headless might help on some systems)

**Issue:** Frames not uploading to server
- Solution: Check network connectivity, verify token is valid

**Issue:** Focus scores not appearing
- Solution: Ensure /frame endpoint is receiving data, check browser console for errors

**Issue:** Tracking subprocess not starting
- Solution: Check backend logs at `tracking_<class_id>.log`, verify class is active

---

## 📌 What's Next (Optional Enhancements)

1. Real-time alerts when focus drops below threshold
2. Daily/weekly focus reports via email
3. Comparison charts between students
4. Predictive alerts (before focus drops)
5. Mobile app for student check-ins
6. Integration with calendar systems
7. Advanced ML models for focus prediction

---

Created: April 21, 2026
Version: 1.0 - Complete Focus Tracking System
