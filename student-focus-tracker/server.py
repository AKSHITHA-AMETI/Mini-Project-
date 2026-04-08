import os
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request, session
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
from flask_mail import Mail, Message
import jwt
import pandas as pd
import pytz
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
try:
    client.admin.command('ping')
    print("MongoDB connected successfully")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    print("Please ensure MongoDB is installed and running on localhost:27017")
    exit(1)

db = client['student_focus_tracker']

# Flask-Mail setup
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
mail = Mail(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')  # 'teacher', 'student', 'admin'
    name = data.get('name')
    class_name = data.get('class_name') if role == 'student' else None

    if not all([email, password, role, name]):
        return jsonify({'error': 'Missing required fields'}), 400

    if db.users.find_one({'email': email}):
        return jsonify({'error': 'User already exists'}), 400

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    user_doc = {
        'email': email,
        'password': hashed_password,
        'role': role,
        'name': name,
        'class_name': class_name
    }

    db.users.insert_one(user_doc)
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user_data = db.users.find_one({'email': email})
    if user_data and check_password_hash(user_data['password'], password):
        token = generate_token(str(user_data['_id']))
        return jsonify({'message': 'Logged in successfully', 'role': user_data['role'], 'token': token, 'user': {'email': user_data['email'], 'name': user_data['name'], 'role': user_data['role']}}), 200
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/classes', methods=['POST'])
def create_class():
    current_user = get_current_user()
    if not current_user or current_user['role'] != 'teacher':
        return jsonify({'error': 'Only teachers can create classes'}), 403

    data = request.get_json()
    class_name = data.get('class_name')
    student_emails = data.get('student_emails', [])
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    meeting_url = data.get('meeting_url')

    if not meeting_url:
        return jsonify({'error': 'Meeting URL must be provided'}), 400

    class_doc = {
        'teacher_email': current_user['email'],
        'class_name': class_name,
        'student_emails': student_emails,
        'start_time': start_time,
        'end_time': end_time,
        'meeting_url': meeting_url,
        'status': 'inactive'
    }

    db.classes.insert_one(class_doc)
    return jsonify({'message': 'Class created successfully'}), 201

@app.route('/classes', methods=['GET'])
def get_classes():
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Unauthorized'}), 401

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)

    if current_user['role'] == 'teacher':
        classes = list(db.classes.find({'teacher_email': current_user['email']}))
    elif current_user['role'] == 'student':
        classes = list(db.classes.find({'student_emails': current_user['email']}))
    else:  # admin
        classes = list(db.classes.find({}))
    now = pd.Timestamp.now(tz='Asia/Kolkata')

    for cls in classes:
        start = pd.to_datetime(cls['start_time'], utc=True).tz_convert('Asia/Kolkata')
        end = pd.to_datetime(cls['end_time'], utc=True).tz_convert('Asia/Kolkata')
        if cls['status'] != 'completed':
            if start <= now <= end:
                cls['status'] = 'active'
                db.classes.update_one({'_id': cls['_id']}, {'$set': {'status': 'active'}})
            elif now > end:
                cls['status'] = 'inactive'
                db.classes.update_one({'_id': cls['_id']}, {'$set': {'status': 'inactive'}})
        cls['_id'] = str(cls['_id'])

    return jsonify(classes), 200

@app.route('/classes/<class_id>/status', methods=['POST'])
def set_class_status(class_id):
    current_user = get_current_user()
    if not current_user or current_user['role'] != 'teacher':
        return jsonify({'error': 'Only teachers can change class status'}), 403

    data = request.get_json()
    status = data.get('status')  # 'active', 'inactive', 'completed'

    if status not in ['active', 'inactive', 'completed']:
        return jsonify({'error': 'Invalid status'}), 400

    if status == 'active':
        # Deactivate all other active classes for this teacher
        db.classes.update_many({'teacher_email': current_user['email'], 'status': 'active'}, {'$set': {'status': 'inactive'}})

    db.classes.update_one({'_id': ObjectId(class_id), 'teacher_email': current_user['email']}, {'$set': {'status': status}})
    return jsonify({'message': 'Class status updated'}), 200

@app.route('/frame', methods=['POST'])
def add_frame():
    current_user = get_current_user()
    if not current_user or current_user['role'] != 'student':
        return jsonify({'error': 'Only students can send frame data'}), 403

    ist = pytz.timezone('Asia/Kolkata')

    data = request.get_json()
    class_id = data.get('class_id')
    timestamp = data.get('timestamp', datetime.now(ist).isoformat())
    gaze = data.get('gaze')
    head_direction = data.get('head_direction')
    yawning = data.get('yawning', False)
    mouth_distance = data.get('mouth_distance', 0.0)
    laughing = data.get('laughing', False)
    mouth_width = data.get('mouth_width', 0.0)
    mouth_height = data.get('mouth_height', 0.0)
    focus_score = data.get('focus_score', 0.0)

    frame_doc = {
        'timestamp': timestamp,
        'student_email': current_user['email'],
        'class_id': class_id,
        'gaze': gaze,
        'head_direction': head_direction,
        'yawning': yawning,
        'mouth_distance': mouth_distance,
        'laughing': laughing,
        'mouth_width': mouth_width,
        'mouth_height': mouth_height,
        'focus_score': focus_score
    }

    db.frames.insert_one(frame_doc)

    # Check if focus score is low and send alert
    if focus_score < 50:  # threshold
        send_alert(current_user['email'], class_id, focus_score)

    return jsonify({'status': 'ok'}), 201

@app.route('/frame', methods=['POST'])
def add_frame():
    current_user = get_current_user()
    if not current_user or current_user['role'] != 'student':
        return jsonify({'error': 'Only students can send frame data'}), 403

    data = request.get_json()
    class_id = data.get('class_id')
    timestamp = data.get('timestamp', datetime.now(timezone.utc).isoformat())
    gaze = data.get('gaze')
    head_direction = data.get('head_direction')
    yawning = data.get('yawning', False)
    mouth_distance = data.get('mouth_distance', 0.0)
    laughing = data.get('laughing', False)
    mouth_width = data.get('mouth_width', 0.0)
    mouth_height = data.get('mouth_height', 0.0)
    focus_score = data.get('focus_score', 0.0)

    frame_doc = {
        'timestamp': timestamp,
        'student_email': current_user['email'],
        'class_id': class_id,
        'gaze': gaze,
        'head_direction': head_direction,
        'yawning': yawning,
        'mouth_distance': mouth_distance,
        'laughing': laughing,
        'mouth_width': mouth_width,
        'mouth_height': mouth_height,
        'focus_score': focus_score
    }

    db.frames.insert_one(frame_doc)

    # Check if focus score is low and send alert
    if focus_score < 50:  # threshold
        send_alert(current_user['email'], class_id, focus_score)

    return jsonify({'status': 'ok'}), 201

def send_alert(student_email, class_id, focus_score):
    msg = Message('Focus Alert', sender=app.config['MAIL_USERNAME'], recipients=[student_email])
    msg.body = f'Your focus score is low ({focus_score}%). Please pay attention!'
    mail.send(msg)

def get_current_user():
    token = request.headers.get('Authorization')
    if token:
        user_id = verify_token(token)
        if user_id:
            user_data = db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return user_data  # return dict
    return None

@app.route('/history/<class_id>', methods=['GET'])
def get_history(class_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Unauthorized'}), 401

    limit = int(request.args.get('limit', 240))

    if current_user['role'] == 'student':
        frames = list(db.frames.find({'student_email': current_user['email'], 'class_id': class_id}).sort('_id', -1).limit(limit))
    elif current_user['role'] == 'teacher':
        # Get frames for all students in the class
        cls = db.classes.find_one({'_id': ObjectId(class_id), 'teacher_email': current_user['email']})
        if not cls:
            return jsonify({'error': 'Class not found'}), 404
        student_emails = cls['student_emails']
        frames = list(db.frames.find({'student_email': {'$in': student_emails}, 'class_id': class_id}).sort('_id', -1).limit(limit))
    else:  # admin
        frames = list(db.frames.find({'class_id': class_id}).sort('_id', -1).limit(limit))

    for frame in frames:
        frame['_id'] = str(frame['_id'])

    return jsonify({'history': frames}), 200

@app.route('/stats/<class_id>', methods=['GET'])
def get_stats(class_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Unauthorized'}), 401

    if current_user['role'] == 'student':
        pipeline = [
            {'$match': {'student_email': current_user['email'], 'class_id': class_id}},
            {'$group': {'_id': None, 'count': {'$sum': 1}, 'average_score': {'$avg': '$focus_score'}}}
        ]
    elif current_user['role'] == 'teacher':
        cls = db.classes.find_one({'_id': ObjectId(class_id), 'teacher_email': current_user['email']})
        if not cls:
            return jsonify({'error': 'Class not found'}), 404
        student_emails = cls['student_emails']
        pipeline = [
            {'$match': {'student_email': {'$in': student_emails}, 'class_id': class_id}},
            {'$group': {'_id': None, 'count': {'$sum': 1}, 'average_score': {'$avg': '$focus_score'}}}
        ]
    else:  # admin
        pipeline = [
            {'$match': {'class_id': class_id}},
            {'$group': {'_id': None, 'count': {'$sum': 1}, 'average_score': {'$avg': '$focus_score'}}}
        ]

    result = list(db.frames.aggregate(pipeline))
    if result:
        stats = result[0]
        stats.pop('_id')
    else:
        stats = {'count': 0, 'average_score': 0.0}

    # Get latest frame
    latest = db.frames.find_one({'class_id': class_id}, sort=[('_id', -1)])
    if latest:
        latest['_id'] = str(latest['_id'])
        stats['latest'] = latest
    else:
        stats['latest'] = None

    return jsonify(stats), 200

@app.route('/active_students/<class_id>', methods=['GET'])
def get_active_students(class_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Unauthorized'}), 401

    # Get students who have sent frames recently (e.g., last 5 minutes)
    recent_time = datetime.now(timezone.utc).timestamp() - 300  # 5 minutes ago
    recent_frames = db.frames.find({'class_id': class_id, 'timestamp': {'$gte': datetime.fromtimestamp(recent_time, tz=timezone.utc).isoformat()}})
    active_emails = set(frame['student_email'] for frame in recent_frames)
    active_count = len(active_emails)
    return jsonify({'active_students': active_count, 'emails': list(active_emails)}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
