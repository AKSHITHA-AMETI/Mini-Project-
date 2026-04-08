import os
import sqlite3
import hashlib
import secrets
from datetime import datetime, timezone
from flask import Flask, g, jsonify, request

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "attention.db")

app = Flask(__name__)


def get_db():
    db = getattr(g, "db", None)
    if db is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        g.db = db
    return db


def close_db(e=None):
    db = getattr(g, "db", None)
    if db is not None:
        db.close()


@app.teardown_appcontext
def teardown_db(exception):
    close_db(exception)


def hash_password(password):
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${pwd_hash.hex()}"


def verify_password(stored_hash, password):
    """Verify password against stored hash"""
    try:
        salt, pwd_hash = stored_hash.split('$')
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return new_hash.hex() == pwd_hash
    except:
        return False


def init_db():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            class_name TEXT NOT NULL,
            scheduled_time TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS class_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            link TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (class_id) REFERENCES classes(id)
        );
        
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            enrolled_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (class_id) REFERENCES classes(id),
            FOREIGN KEY (student_id) REFERENCES users(id),
            UNIQUE(class_id, student_id)
        );
        
        CREATE TABLE IF NOT EXISTS frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            student_id TEXT,
            class_id INTEGER,
            gaze TEXT,
            head_direction TEXT,
            yawning INTEGER,
            mouth_distance REAL,
            laughing INTEGER,
            mouth_width REAL,
            mouth_height REAL,
<<<<<<< Updated upstream
            focus_score REAL
        );
=======
            focus_score REAL,
            FOREIGN KEY (class_id) REFERENCES classes(id)
        );
        
>>>>>>> Stashed changes
        CREATE TABLE IF NOT EXISTS meeting (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            url TEXT
        );
        INSERT OR IGNORE INTO meeting (id, url) VALUES (1, '');
<<<<<<< Updated upstream
        CREATE TABLE IF NOT EXISTS class_status (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            status TEXT DEFAULT 'inactive'
        );
        INSERT OR IGNORE INTO class_status (id, status) VALUES (1, 'inactive');
=======
>>>>>>> Stashed changes
        """
    )
    db.commit()


@app.route("/auth/register", methods=["POST"])
def register():
    """Register a new user (student or teacher)"""
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "JSON payload required"}), 400
    
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    email = data.get("email", "").strip()
    role = data.get("role", "student").lower()  # 'student' or 'teacher'
    
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    
    if role not in ["student", "teacher"]:
        return jsonify({"error": "role must be 'student' or 'teacher'"}), 400
    
    db = get_db()
    try:
        password_hash = hash_password(password)
        cursor = db.execute(
            "INSERT INTO users (username, password_hash, email, role) VALUES (?, ?, ?, ?)",
            (username, password_hash, email, role)
        )
        user_id = cursor.lastrowid
        db.commit()
        return jsonify({"status": "ok", "user_id": user_id, "role": role}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "username already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/auth/login", methods=["POST"])
def login():
    """Login user"""
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "JSON payload required"}), 400
    
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    
    db = get_db()
    user = db.execute(
        "SELECT id, username, role, password_hash FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    
    if not user or not verify_password(user["password_hash"], password):
        return jsonify({"error": "invalid username or password"}), 401
    
    return jsonify({
        "status": "ok",
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"]
    }), 200


@app.route("/classes", methods=["GET"])
def list_classes():
    """List classes for student (enrolled) or teacher (created)"""
    user_id = request.args.get("user_id")
    role = request.args.get("role")
    
    if not user_id or not role:
        return jsonify({"error": "user_id and role required"}), 400
    
    db = get_db()
    if role == "teacher":
        cursor = db.execute(
            """SELECT c.id, c.class_name, c.teacher_id, c.scheduled_time, 
                      cl.link, c.created_at
               FROM classes c
               LEFT JOIN class_links cl ON c.id = cl.class_id
               WHERE c.teacher_id = ? ORDER BY c.scheduled_time DESC""",
            (user_id,)
        )
    else:  # student
        cursor = db.execute(
            """SELECT c.id, c.class_name, c.teacher_id, c.scheduled_time,
                      cl.link, c.created_at
               FROM classes c
               LEFT JOIN class_links cl ON c.id = cl.class_id
               JOIN enrollments e ON c.id = e.class_id
               WHERE e.student_id = ? ORDER BY c.scheduled_time DESC""",
            (user_id,)
        )
    
    rows = cursor.fetchall()
    classes = [dict(row) for row in rows]
    return jsonify({"classes": classes}), 200


@app.route("/classes", methods=["POST"])
def create_class():
    """Create a new class (teacher only)"""
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "JSON payload required"}), 400
    
    teacher_id = data.get("teacher_id")
    class_name = data.get("class_name", "").strip()
    scheduled_time = data.get("scheduled_time")
    
    if not teacher_id or not class_name:
        return jsonify({"error": "teacher_id and class_name required"}), 400
    
    db = get_db()
    cursor = db.execute(
        "INSERT INTO classes (teacher_id, class_name, scheduled_time) VALUES (?, ?, ?)",
        (teacher_id, class_name, scheduled_time)
    )
    class_id = cursor.lastrowid
    db.commit()
    
    return jsonify({"status": "ok", "class_id": class_id}), 201


@app.route("/classes/<int:class_id>/link", methods=["POST"])
def add_class_link(class_id):
    """Add or update meeting link for a class (teacher only)"""
    data = request.get_json(force=True, silent=True)
    if not data or "link" not in data:
        return jsonify({"error": "link required"}), 400
    
    link = data.get("link", "").strip()
    
    db = get_db()
    existing = db.execute(
        "SELECT id FROM class_links WHERE class_id = ?",
        (class_id,)
    ).fetchone()
    
    if existing:
        db.execute(
            "UPDATE class_links SET link = ? WHERE class_id = ?",
            (link, class_id)
        )
    else:
        db.execute(
            "INSERT INTO class_links (class_id, link) VALUES (?, ?)",
            (class_id, link)
        )
    db.commit()
    
    return jsonify({"status": "ok"}), 200


@app.route("/users/search", methods=["GET"])
def search_users():
    """Search for users by email or username"""
    query = request.args.get("q", "").strip()
    
    if not query or len(query) < 2:
        return jsonify({"error": "query must be at least 2 characters"}), 400
    
    db = get_db()
    cursor = db.execute(
        """SELECT id, username, email, role 
           FROM users 
           WHERE (email LIKE ? OR username LIKE ?) AND role = 'student'
           LIMIT 10""",
        (f"%{query}%", f"%{query}%")
    )
    
    users = [dict(row) for row in cursor.fetchall()]
    return jsonify({"users": users}), 200


@app.route("/classes/<int:class_id>/enroll", methods=["POST"])
def enroll_student(class_id):
    """Enroll a student in a class"""
    data = request.get_json(force=True, silent=True)
    if not data or "student_id" not in data:
        return jsonify({"error": "student_id required"}), 400
    
    student_id = data.get("student_id")
    
    db = get_db()
    try:
        db.execute(
            "INSERT INTO enrollments (class_id, student_id) VALUES (?, ?)",
            (class_id, student_id)
        )
        db.commit()
        return jsonify({"status": "ok"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "student already enrolled"}), 409


@app.route("/classes/<int:class_id>/students", methods=["GET"])
def get_class_students(class_id):
    """Get all students in a class with their focus stats"""
    db = get_db()
    
    cursor = db.execute(
        """SELECT u.id, u.username, 
                  AVG(f.focus_score) as avg_focus,
                  COUNT(f.id) as frame_count
           FROM enrollments e
           JOIN users u ON e.student_id = u.id
           LEFT JOIN frames f ON f.student_id = CAST(u.id AS TEXT) AND f.class_id = ?
           WHERE e.class_id = ?
           GROUP BY u.id, u.username""",
        (class_id, class_id)
    )
    
    students = [dict(row) for row in cursor.fetchall()]
    return jsonify({"students": students}), 200


@app.route("/frame", methods=["POST"])
def add_frame():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "JSON payload required"}), 400

    timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat())
    student_id = data.get("student_id")
    class_id = data.get("class_id")
    gaze = data.get("gaze")
    head_direction = data.get("head_direction")
    yawning = 1 if data.get("yawning") else 0
    mouth_distance = float(data.get("mouth_distance", 0.0))
    laughing = 1 if data.get("laughing") else 0
    mouth_width = float(data.get("mouth_width", 0.0))
    mouth_height = float(data.get("mouth_height", 0.0))
    focus_score = float(data.get("focus_score", 0.0))

    db = get_db()
    db.execute(
        "INSERT INTO frames (timestamp, student_id, class_id, gaze, head_direction, yawning, mouth_distance, laughing, mouth_width, mouth_height, focus_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (timestamp, student_id, class_id, gaze, head_direction, yawning, mouth_distance, laughing, mouth_width, mouth_height, focus_score),
    )
    db.commit()

    return jsonify({"status": "ok"}), 201


@app.route("/history", methods=["GET"])
def get_history():
    limit = int(request.args.get("limit", 240))
    db = get_db()
    cursor = db.execute(
        "SELECT * FROM frames ORDER BY id DESC LIMIT ?", (limit,)
    )
    rows = cursor.fetchall()
    history = [dict(row) for row in rows]
    return jsonify({"history": history})


@app.route("/meeting", methods=["GET"])
def get_meeting():
    db = get_db()
    row = db.execute("SELECT url FROM meeting WHERE id = 1").fetchone()
    return jsonify({"url": row["url"] if row else ""})


@app.route("/meeting", methods=["POST"])
def set_meeting():
    data = request.get_json(force=True, silent=True)
    if not data or "url" not in data:
        return jsonify({"error": "url required"}), 400
    url = data["url"]
    db = get_db()
    db.execute("UPDATE meeting SET url = ? WHERE id = 1", (url,))
    db.commit()
    return jsonify({"status": "ok"}), 200


@app.route("/class_status", methods=["GET"])
def get_class_status():
    db = get_db()
    row = db.execute("SELECT status FROM class_status WHERE id = 1").fetchone()
    return jsonify({"status": row["status"] if row else "inactive"})


@app.route("/class_status", methods=["POST"])
def set_class_status():
    data = request.get_json(force=True, silent=True)
    if not data or "status" not in data:
        return jsonify({"error": "status required"}), 400
    status = data["status"]
    if status not in ["active", "inactive"]:
        return jsonify({"error": "status must be 'active' or 'inactive'"}), 400
    db = get_db()
    db.execute("UPDATE class_status SET status = ? WHERE id = 1", (status,))
    db.commit()
    return jsonify({"status": "ok"}), 200


@app.route("/stats", methods=["GET"])
def get_stats():
    db = get_db()
    cursor = db.execute("SELECT COUNT(*) as count, AVG(focus_score) as average_score FROM frames")
    row = cursor.fetchone()
    count = row["count"] if row else 0
    average_score = row["average_score"] if row and row["average_score"] else 0.0

    cursor = db.execute("SELECT * FROM frames ORDER BY id DESC LIMIT 1")
    latest = cursor.fetchone()
    latest_data = dict(latest) if latest else None

    return jsonify({"count": count, "average_score": average_score, "latest": latest_data})


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
