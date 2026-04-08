# Quick Start Guide

## Setup

### 1. Ensure Dependencies are Installed
```bash
pip install -r req.txt
```

### 2. Start the Backend Server
```bash
python server.py
```
- Server will run on `http://127.0.0.1:5000`
- Database will be created at `data/attention.db`

### 3. Start the Dashboard
In a new terminal:
```bash
cd dashboard
streamlit run app.py
```
- Dashboard will open at `http://localhost:8501`

---

## Teacher Workflow

### Step 1: Register as Teacher
1. Go to dashboard login page
2. In "Register" section, enter:
   - Username: `teacher1`
   - Email: `teacher@example.com`
   - Password: `password123`
   - Role: `teacher`
3. Click "Register"

### Step 2: Login
1. Enter username and password
2. Click "Login"
3. You'll see the Teacher Dashboard

### Step 3: Create a Class
1. In the sidebar, enter:
   - Class Name: `Math 101`
   - Scheduled Time: `2024-04-01 14:00`
2. Click "Create Class"
3. Class appears in your class list

### Step 4: Add Meeting Link
1. For the class you created, click "Add Meeting Link" expander
2. Paste your meeting URL (e.g., `https://zoom.us/j/123456`)
3. Click "Save Link"

### Step 5: Enroll Students
Share the class ID with students, or use API:
```bash
curl -X POST http://127.0.0.1:5000/classes/1/enroll \
  -H "Content-Type: application/json" \
  -d '{"student_id": 2}'
```

### Step 6: Monitor Student Focus
- Dashboard automatically shows student data:
  - Average focus score
  - Number of tracked frames
- Updates in real-time as students track

---

## Student Workflow

### Step 1: Register as Student
1. Go to dashboard login page
2. In "Register" section, enter:
   - Username: `student1`
   - Email: `student@example.com`
   - Password: `password123`
   - Role: `student`
3. Click "Register"

### Step 2: Login
1. Enter username and password
2. Click "Login"
3. You'll see the Student Dashboard

### Step 3: Wait for Teacher to Enroll You
- Ask your teacher to enroll you in a class
- Once enrolled, the class will appear in your "Your Scheduled Classes"

### Step 4: Join Class Meeting (if link available)
1. When teacher adds meeting link, click "🔗 Join Class"
2. You'll be directed to the meeting URL

### Step 5: Start Focus Tracking
1. Click "▶️ Start Tracking" button
2. Note the Class ID displayed
3. Open a terminal and run:
   ```bash
   python main.py "student1" <class_id>
   ```
   Replace `<class_id>` with the actual class ID shown

### Step 6: Focus Tracking Starts
- Webcam opens with focus tracking overlay
- Your data is automatically sent to backend
- Appears in teacher's dashboard
- Press 'q' to stop tracking

---

## API Testing (Optional)

### Register User
```bash
curl -X POST http://127.0.0.1:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"student1","password":"pass123","email":"student@test.com","role":"student"}'
```

### Login
```bash
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"student1","password":"pass123"}'
```

### Create Class
```bash
curl -X POST http://127.0.0.1:5000/classes \
  -H "Content-Type: application/json" \
  -d '{"teacher_id":1,"class_name":"Physics 101","scheduled_time":"2024-04-02 10:00"}'
```

### Add Meeting Link
```bash
curl -X POST http://127.0.0.1:5000/classes/1/link \
  -H "Content-Type: application/json" \
  -d '{"link":"https://zoom.us/j/123456"}'
```

### List Classes (for teacher)
```bash
curl "http://127.0.0.1:5000/classes?user_id=1&role=teacher"
```

### Get Class Students
```bash
curl "http://127.0.0.1:5000/classes/1/students"
```

---

## Troubleshooting

### Dashboard doesn't load
- Ensure backend server is running: `python server.py`
- Check if port 5000 is available
- Try accessing `http://127.0.0.1:5000/stats` to verify backend

### Login fails
- Ensure you registered first
- Check username and password
- For testing, database file is at `data/attention.db`

### Focus tracker won't start
- Check webcam is working: `python -c "import cv2; cv2.VideoCapture(0).isOpened()"`
- Ensure main.py has correct class_id
- Try without class_id first: `python main.py`

### No student data on teacher dashboard
- Ensure student is properly enrolled in class
- Check that student starts tracking with correct class_id
- Data appears after 10+ frames (caching is 10 seconds)

---

## Database Reset
To start fresh (delete all data):
```bash
rm data/attention.db
```
Database will be recreated on next server start.

---

## Key Points to Remember
- **Links are only shown to enrolled students** ✅
- **Students must click "Start Tracking"** to activate monitoring
- **Teacher sees all student data in real-time** dashboard
- **Class ID must match** between dashboard and main.py
- **Password hashing** ensures security
