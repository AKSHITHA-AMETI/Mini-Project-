import os
import sqlite3
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


def init_db():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            student_id TEXT,
            gaze TEXT,
            head_direction TEXT,
            yawning INTEGER,
            mouth_distance REAL,
            laughing INTEGER,
            mouth_width REAL,
            mouth_height REAL,
            focus_score REAL
        );
        CREATE TABLE IF NOT EXISTS meeting (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            url TEXT
        );
        INSERT OR IGNORE INTO meeting (id, url) VALUES (1, '');
        CREATE TABLE IF NOT EXISTS class_status (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            status TEXT DEFAULT 'inactive'
        );
        INSERT OR IGNORE INTO class_status (id, status) VALUES (1, 'inactive');
        """
    )
    db.commit()


@app.route("/frame", methods=["POST"])
def add_frame():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "JSON payload required"}), 400

    timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat())
    student_id = data.get("student_id")
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
        "INSERT INTO frames (timestamp, student_id, gaze, head_direction, yawning, mouth_distance, laughing, mouth_width, mouth_height, focus_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (timestamp, student_id, gaze, head_direction, yawning, mouth_distance, laughing, mouth_width, mouth_height, focus_score),
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
