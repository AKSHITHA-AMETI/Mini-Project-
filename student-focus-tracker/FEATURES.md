# Student Focus Tracker - New Features

## Overview
The updated Student Focus Tracker now includes authentication, class management, and role-based dashboards for both students and teachers.

## Features

### 1. User Authentication
- **Register**: Users can create new accounts as either Student or Teacher
- **Login**: Secure login with username and password
- **Role-based Access**: Different interfaces for students and teachers

#### How to Register
1. Open the dashboard
2. Go to the "Register" section
3. Enter username, email, and password
4. Select role: "student" or "teacher"
5. Click Register

#### How to Login
1. Enter your username and password
2. Click Login
3. You'll be directed to your role-specific dashboard

---

## Student Features

### View Scheduled Classes
- After logging in, students see a list of all classes they're enrolled in
- Classes display:
  - Class name
  - Scheduled time
  - Meeting link (when available)
  - Action buttons

### Start Focus Tracking
- Click "Start Tracking" button to activate the focus tracker for the class
- The tracker will record:
  - Gaze direction
  - Head position
  - Yawning detection
  - Laughter detection
  - Focus score
- Data is automatically sent to the backend and associated with the class

### Join Meeting Link
- If the teacher has added a meeting link, click "Join Class" button
- You'll be directed to the meeting URL (Zoom, Google Meet, etc.)
- **Important**: Links are only shown to enrolled students, not at registration

---

## Teacher Features

### Create New Classes
1. In the sidebar, enter:
   - Class name
   - Scheduled time (e.g., "2024-04-01 10:00")
2. Click "Create Class"
3. The class appears in your class list

### Add Meeting Links
1. For each class, click "Add Meeting Link" expander
2. Paste your meeting URL (Zoom, Google Meet, etc.)
3. Click "Save Link"
4. Link becomes available to enrolled students

### Enroll Students
- Students must register and ask the teacher for enrollment
- Teacher can enroll students via direct API call or future UI update

### View Student Dashboard
- For each class, see real-time student data:
  - Student username
  - Average focus score
  - Number of frames/data points recorded
- Monitor focus trends for all students in the class

---

## API Endpoints

### Authentication
```
POST /auth/register
- username (string, required)
- password (string, required)
- email (string, optional)
- role (string, required): "student" or "teacher"

POST /auth/login
- username (string, required)
- password (string, required)
```

### Classes
```
GET /classes?user_id=<id>&role=<role>
- List classes for a user (role: "student" or "teacher")

POST /classes
- teacher_id (integer, required)
- class_name (string, required)
- scheduled_time (string, optional)

POST /classes/<class_id>/link
- link (string, required): Meeting URL

GET /classes/<class_id>/students
- Get all students in a class with focus stats
```

### Frame Data
```
POST /frame
- timestamp (string, ISO format)
- student_id (string, optional)
- class_id (integer, optional)
- gaze (string)
- head_direction (string)
- yawning (boolean)
- mouth_distance (float)
- laughing (boolean)
- mouth_width (float)
- mouth_height (float)
- focus_score (float)
```

---

## Running the Application

### Start Backend Server
```bash
python server.py
```
- Server runs on `http://127.0.0.1:5000`
- SQLite database is created at `data/attention.db`

### Start Dashboard
```bash
streamlit run dashboard/app.py
```
- Dashboard runs on `http://localhost:8501`

### Start Focus Tracker (from command line)
```bash
# Without class association
python main.py

# With student ID and class ID
python main.py "student_123" 1
```

---

## Database Schema

### Users Table
- `id`: User ID
- `username`: Unique username
- `password_hash`: Hashed password (PBKDF2-SHA256)
- `email`: Email address
- `role`: "student" or "teacher"
- `created_at`: Timestamp

### Classes Table
- `id`: Class ID
- `teacher_id`: Teacher's user ID
- `class_name`: Name of the class
- `scheduled_time`: When the class is scheduled
- `created_at`: Timestamp

### Enrollments Table
- `id`: Enrollment ID
- `class_id`: Class ID
- `student_id`: Student's user ID
- `enrolled_at`: Timestamp

### Class Links Table
- `id`: Link ID
- `class_id`: Class ID
- `link`: Meeting URL
- `created_at`: Timestamp

### Frames Table
- `id`: Frame ID
- `timestamp`: Data timestamp
- `student_id`: Student identifier
- `class_id`: Associated class ID
- `gaze`: Gaze direction
- `head_direction`: Head position
- `yawning`: Yawn detection (0/1)
- `laughing`: Laugh detection (0/1)
- `focus_score`: Computed focus score
- Plus mouth measurements

---

## Workflow Example

### Teacher Workflow
1. Register as "teacher"
2. Create new class "Math 101" scheduled for "2024-04-01 14:00"
3. Add Zoom link "https://zoom.us/j/123456"
4. Share class ID with students
5. In dashboard, view:
   - Students enrolled in the class
   - Each student's average focus score
   - Number of tracked frames per student

### Student Workflow
1. Register as "student"
2. Ask teacher to enroll you in a class
3. Log in and see "Math 101" in your class list
4. Click "Join Class" to access Zoom link (if available)
5. Click "Start Tracking" to activate focus monitoring
6. Run `python main.py "your_username" <class_id>` to track focus
7. Your focus data appears in teacher's dashboard

---

## Security Features
- Passwords are hashed using PBKDF2-SHA256 with random salt
- Links are only shown to enrolled students
- Role-based access control (students/teachers see different interfaces)
- Authentication required for all sensitive operations

---

## Future Enhancements
- Batch enrollment of students
- Performance reports for teachers
- Real-time notifications
- Class schedule updates
- Student profile management
- Focus trend analysis
