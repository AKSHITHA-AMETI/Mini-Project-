# System Architecture & Data Flow

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    WEB BROWSERS                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    http://localhost:8501 (Streamlit Dashboard)      │  │
│  │                                                      │  │
│  │  ┌─────────────────┬────────────────────────────┐   │  │
│  │  │   LOGIN PAGE    │  STUDENT DASHBOARD         │   │  │
│  │  │ ┌─────────────┐ │  ┌──────────────────────┐  │   │  │
│  │  │ │ Register    │ │  │ View Enrolled Classes│  │   │  │
│  │  │ │ (S/T role)  │ │  │ Join Meeting Link    │  │   │  │
│  │  │ │             │ │  │ Start Tracking       │  │   │  │
│  │  │ │ Login       │ │  └──────────────────────┘  │   │  │
│  │  │ └─────────────┘ │                             │   │  │
│  │  │                 │  TEACHER DASHBOARD          │   │  │
│  │  │                 │  ┌──────────────────────┐   │   │  │
│  │  │                 │  │ Create New Class     │   │   │  │
│  │  │                 │  │ Add Meeting Link     │   │   │  │
│  │  │                 │  │ View Student Stats   │   │   │  │
│  │  │                 │  │ (focus score, data)  │   │   │  │
│  │  │                 │  └──────────────────────┘   │   │  │
│  │  └─────────────────┴────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬─────────────────────────────────────┘
                       │ HTTP/JSON
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              FLASK BACKEND API (server.py)                  │
│         http://127.0.0.1:5000                              │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AUTHENTICATION ENDPOINTS                            │  │
│  │  • POST /auth/register   - Create user account       │  │
│  │  • POST /auth/login      - Authenticate user         │  │
│  │  • Password hashing (PBKDF2-SHA256)                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  CLASS MANAGEMENT ENDPOINTS                          │  │
│  │  • GET  /classes          - List user's classes      │  │
│  │  • POST /classes          - Create new class         │  │
│  │  • POST /classes/<id>/link   - Add meeting link      │  │
│  │  • POST /classes/<id>/enroll - Enroll student        │  │
│  │  • GET  /classes/<id>/students - Get class analytics │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  TRACKING ENDPOINTS                                  │  │
│  │  • POST /frame      - Record focus/gaze/eye data     │  │
│  │  • GET  /history    - Retrieve historical data       │  │
│  │  • GET  /stats      - Get aggregated statistics      │  │
│  │  • GET  /meeting    - Get meeting URL                │  │
│  │  • POST /meeting    - Set meeting URL                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└──────────────────────┬─────────────────────────────────────┘
                       │ SQL
                       ↓
┌─────────────────────────────────────────────────────────────┐
│         SQLite DATABASE (data/attention.db)                 │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ TABLE: users                                         │  │
│  │ ├─ id (Primary Key)                                 │  │
│  │ ├─ username (UNIQUE)                                │  │
│  │ ├─ password_hash (hashed + salted)                  │  │
│  │ ├─ email                                            │  │
│  │ ├─ role ('student' or 'teacher')                   │  │
│  │ └─ created_at                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ TABLE: classes                                       │  │
│  │ ├─ id (Primary Key)                                 │  │
│  │ ├─ teacher_id (Foreign Key → users)                │  │
│  │ ├─ class_name                                       │  │
│  │ ├─ scheduled_time                                   │  │
│  │ └─ created_at                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ TABLE: enrollments                                   │  │
│  │ ├─ id (Primary Key)                                 │  │
│  │ ├─ class_id (Foreign Key → classes)                │  │
│  │ ├─ student_id (Foreign Key → users)                │  │
│  │ └─ enrolled_at                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ TABLE: class_links                                   │  │
│  │ ├─ id (Primary Key)                                 │  │
│  │ ├─ class_id (Foreign Key → classes)                │  │
│  │ ├─ link (Zoom/Meet URL)                            │  │
│  │ └─ created_at                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ TABLE: frames (Focus Data)                           │  │
│  │ ├─ id (Primary Key)                                 │  │
│  │ ├─ timestamp                                        │  │
│  │ ├─ student_id                                       │  │
│  │ ├─ class_id (NEW! - tracks which class)            │  │
│  │ ├─ gaze                                             │  │
│  │ ├─ head_direction                                   │  │
│  │ ├─ yawning (boolean)                                │  │
│  │ ├─ laughing (boolean)                               │  │
│  │ ├─ focus_score (computed)                           │  │
│  │ └─ [other fields...]                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagrams

### Teacher Workflow: Create Class & Monitor Students

```
1. REGISTRATION
  Browser → /auth/register (role="teacher")
    ↓
  Backend: Hash password, store in users table
    ↓
  Response: user_id, role

2. LOGIN
  Browser → /auth/login (username, password)
    ↓
  Backend: Verify password against hash
    ↓
  Response: user_id, username, role
    ↓
  Browser: Set session state → Show teacher dashboard

3. CREATE CLASS
  Browser → POST /classes (teacher_id, class_name, scheduled_time)
    ↓
  Backend: Insert into classes table
    ↓
  Response: class_id
    ↓
  Browser: Display class in list

4. ADD MEETING LINK
  Browser → POST /classes/<id>/link (link="https://zoom.us/j/...")
    ↓
  Backend: Insert/update in class_links table
    ↓
  Response: success
    ↓
  Browser: Update display

5. MONITOR STUDENTS
  Browser → GET /classes/<id>/students
    ↓
  Backend: Query enrollments + frames tables
           JOIN users on student_id
           AVG(focus_score), COUNT(frames)
    ↓
  Response: [{ username, avg_focus, frame_count }, ...]
    ↓
  Browser: Display in dashboard table
```

### Student Workflow: Join Class & Track Focus

```
1. REGISTRATION
  Browser → /auth/register (role="student")
    ↓
  Backend: Hash password, store in users table
    ↓
  Response: user_id, role

2. LOGIN
  Browser → /auth/login (username, password)
    ↓
  Backend: Verify password
    ↓
  Response: user_id, username, role
    ↓
  Browser: Set session state → Show student dashboard

3. VIEW CLASSES (only enrolled)
  Browser → GET /classes (user_id, role="student")
    ↓
  Backend: SELECT from classes
           JOIN enrollments WHERE student_id = ?
           LEFT JOIN class_links
    ↓
  Response: [{ class_name, scheduled_time, link }, ...]
    ↓
  Browser: Display active classes only
  NOTE: Links ONLY shown for enrolled students!

4. JOIN MEETING (if link exists)
  Browser → Click "🔗 Join Class"
    ↓
  Client-side: Open link in new window

5. START TRACKING
  Browser → Click "▶️ Start Tracking"
    ↓
  Browser: Display "Class ID: 1" message
    ↓
  User: Copy class ID

6. RUN FOCUS TRACKER
  Terminal → python main.py "student1" 1
    ↓
  Opening webcam...
    ↓
  Every 8-10 seconds:
    ├─ Detect face, gaze, head pose
    ├─ Detect yawning, laughing
    ├─ Compute focus score
    └─ POST /frame (timestamp, student_id, class_id, ...)
         ↓
      Backend: Insert into frames table
         ↓
      Response: {status: "ok"}

7. TEACHER SEES DATA
  Teacher's browser auto-refreshes every 10 seconds
    ↓
  GET /classes/<id>/students
    ↓
  Shows student1's avg_focus increasing
```

---

## 🔒 Security Flow

### Password Security
```
Registration:
  User enters password → Generate random salt
    ↓
  PBKDF2-SHA256(password, salt, 100000 iterations)
    ↓
  Store: salt$hashed_password in database

Login:
  User enters password → Extract salt from stored hash
    ↓
  PBKDF2-SHA256(password, salt, 100000 iterations)
    ↓
  Compare with stored hash
    ↓
  If match → Create session, return user_id
```

### Link Privacy
```
Before Enrollment:
  Student at registration page
    ↓
  They DON'T see any meeting links
    ↓
  Can't access links in database

After Enrollment:
  Student logs in
    ↓
  GET /classes queries with role="student"
    ↓
  Backend filters: only classes where student is enrolled
    ↓
  LEFT JOIN class_links → links now included
    ↓
  Student's dashboard shows meeting link
```

---

## 🎯 Key Data Associations

```
User
  ├─ role: "teacher" → can create multiple classes
  │   └─ Class 1
  │   └─ Class 2
  │   └─ Class 3
  │
  └─ role: "student" → can enroll in multiple classes
      └─ Enrollment 1 → Class 1 ← (also enrolled: student2, student3)
      └─ Enrollment 2 → Class 2 ← (also enrolled: student2)

Class 1 (created by teacher_id=1)
  ├─ teacher_id: 1
  ├─ scheduled_time: 2024-04-01 10:00
  ├─ class_links: https://zoom.us/j/123456
  │
  └─ Enrollments:
      ├─ student_id: 2 (student1)
      ├─ student_id: 3 (student2)
      └─ student_id: 4 (student3)
         ↓
         Frames:
         ├─ student_id: 2, class_id: 1, focus_score: 85
         ├─ student_id: 2, class_id: 1, focus_score: 87
         ├─ student_id: 3, class_id: 1, focus_score: 92
         ├─ student_id: 3, class_id: 1, focus_score: 90
         └─ student_id: 4, class_id: 1, focus_score: 78
```

---

## 📊 Analytics Query Example

```sql
-- Show average focus per student in Class 1
SELECT 
  u.id,
  u.username,
  AVG(f.focus_score) as avg_focus,
  COUNT(f.id) as frame_count
FROM enrollments e
JOIN users u ON e.student_id = u.id
LEFT JOIN frames f ON f.student_id = CAST(u.id AS TEXT) 
                      AND f.class_id = 1
WHERE e.class_id = 1
GROUP BY u.id, u.username;

-- Result:
-- id | username | avg_focus | frame_count
-- 2  | student1 | 86.0      | 2
-- 3  | student2 | 91.0      | 2
-- 4  | student3 | 78.0      | 1
```

---

## 🚀 Deployment Flow

```
Development:
  ├─ Python 3.10
  ├─ Local Flask (http://127.0.0.1:5000)
  ├─ Local Streamlit (http://localhost:8501)
  └─ SQLite database (data/attention.db)

Production Ready:
  ├─ Python 3.10+ compatible
  ├─ Flask can run with Gunicorn/uWSGI
  ├─ Streamlit can serve multiple users
  └─ SQLite can be migrated to PostgreSQL
```

---

## 🔄 Real-Time Update Cycle

```
Every 10 seconds (caching period):

Teacher's Dashboard:
  1. Browser calls GET /classes/<id>/students
  2. Backend executes analytics query
  3. Returns fresh student stats
  4. Streamlit updates table display
  5. Teacher sees latest focus scores

While Student is Tracking:
  1. Webcam processes frame every 8-10 seconds
  2. Sends POST /frame with data
  3. Backend inserts row in frames table
  4. Data immediately available for queries
  5. Next dashboard refresh shows updated stats
```

---

**This architecture ensures:**
- ✅ Real-time data collection
- ✅ Privacy (links hidden until enrollment)
- ✅ Security (password hashing, role-based access)
- ✅ Scalability (database-backed)
- ✅ Separation of concerns (frontend/backend)
