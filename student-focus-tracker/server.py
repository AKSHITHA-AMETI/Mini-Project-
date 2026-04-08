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
    student_id = data.get('student_id') if role == 'student' else None

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
        'class_name': class_name,
        'student_id': student_id
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
        user_info = {'email': user_data['email'], 'name': user_data['name'], 'role': user_data['role']}
        if user_data.get('student_id'):
            user_info['student_id'] = user_data['student_id']
        return jsonify({'message': 'Logged in successfully', 'role': user_data['role'], 'token': token, 'user': user_info}), 200
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/admin_login', methods=['POST'])
def admin_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Fixed password for admin
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')

    user_data = db.users.find_one({'email': email, 'role': 'admin'})
    if user_data and password == admin_password:
        token = generate_token(str(user_data['_id']))
        return jsonify({'message': 'Admin logged in successfully', 'role': 'admin', 'token': token, 'user': {'email': user_data['email'], 'name': user_data['name'], 'role': 'admin'}}), 200
    return jsonify({'error': 'Invalid admin credentials'}), 401

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

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)

    # Parse times assuming they are in UTC ISO format
    start = datetime.fromisoformat(start_time).replace(tzinfo=timezone.utc).astimezone(ist)
    end = datetime.fromisoformat(end_time).replace(tzinfo=timezone.utc).astimezone(ist)

    if start <= now <= end:
        status = 'active'
    elif now < start:
        status = 'upcoming'
    else:
        status = 'completed'

    class_doc = {
        'teacher_email': current_user['email'],
        'class_name': class_name,
        'student_emails': student_emails,
        'start_time': start_time,
        'end_time': end_time,
        'meeting_url': meeting_url,
        'status': status
    }

    db.classes.insert_one(class_doc)
    return jsonify({'message': 'Class created successfully'}), 201

@app.route('/classes', methods=['GET'])
def get_classes():
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Unauthorized'}), 401

    status_filter = request.args.get('status')  # optional filter: 'active', 'upcoming', 'completed'

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)

    query = {}
    if current_user['role'] == 'teacher':
        query['teacher_email'] = current_user['email']
    elif current_user['role'] == 'student':
        query['student_emails'] = current_user['email']
    # admin gets all

    if status_filter:
        query['status'] = status_filter

    classes = list(db.classes.find(query))

    for cls in classes:
        start = datetime.fromisoformat(cls['start_time']).replace(tzinfo=timezone.utc).astimezone(ist)
        end = datetime.fromisoformat(cls['end_time']).replace(tzinfo=timezone.utc).astimezone(ist)
        if cls['status'] not in ['completed']:  # Don't change if already completed
            if now < start:
                new_status = 'upcoming'
            elif start <= now <= end:
                new_status = 'active'
            else:
                new_status = 'completed'
            if new_status != cls['status']:
                cls['status'] = new_status
                db.classes.update_one({'_id': cls['_id']}, {'$set': {'status': new_status}})
        cls['_id'] = str(cls['_id'])

    return jsonify(classes), 200

@app.route('/students', methods=['GET'])
def get_students():
    current_user = get_current_user()
    if not current_user or current_user['role'] not in ['teacher', 'admin']:
        return jsonify({'error': 'Only teachers and admins can view students'}), 403

    students = list(db.users.find({'role': 'student'}, {'_id': 1, 'email': 1, 'name': 1, 'student_id': 1, 'class_name': 1}))
    for student in students:
        student['_id'] = str(student['_id'])

    return jsonify({'students': students}), 200

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
    face_detected = data.get('face_detected', True)

    frame_doc = {
        'timestamp': timestamp,
        'student_email': current_user['email'],
        'student_id': current_user.get('student_id'),
        'class_id': class_id,
        'gaze': gaze,
        'head_direction': head_direction,
        'yawning': yawning,
        'mouth_distance': mouth_distance,
        'laughing': laughing,
        'mouth_width': mouth_width,
        'mouth_height': mouth_height,
        'focus_score': focus_score,
        'face_detected': face_detected
    }

    db.frames.insert_one(frame_doc)

    # Record participant if first frame for this class
    if not db.meeting_participants.find_one({'student_email': current_user['email'], 'class_id': class_id}):
        participant_doc = {
            'student_email': current_user['email'],
            'student_id': current_user.get('student_id'),
            'class_id': class_id,
            'joined_at': timestamp
        }
        db.meeting_participants.insert_one(participant_doc)

    # Check if focus score is low and send alert
    if focus_score < 50:  # threshold
        send_alert(current_user['email'], class_id, focus_score, 'low_focus')

    # Check if face not detected
    if not face_detected:
        send_alert(current_user['email'], class_id, 0, 'face_not_detected')

    return jsonify({'status': 'ok'}), 201

def send_alert(student_email, class_id, value, alert_type):
    # Get admin emails
    admins = list(db.users.find({'role': 'admin'}))
    admin_emails = [admin['email'] for admin in admins]
    
    recipients = [student_email] + admin_emails
    
    if alert_type == 'low_focus':
        subject = 'Focus Alert'
        body = f'Your focus score is low ({value}%). Please pay attention!'
    elif alert_type == 'face_not_detected':
        subject = 'Face Detection Alert'
        body = 'Face not detected. Please ensure your face is visible to the camera.'
    else:
        subject = 'Alert'
        body = f'Alert: {alert_type} - {value}'
    
    msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=recipients)
    msg.body = body
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
    student_filter = request.args.get('student_email')  # optional filter for specific student

    if current_user['role'] == 'student':
        frames = list(db.frames.find({'student_email': current_user['email'], 'class_id': class_id}).sort('_id', -1).limit(limit))
    elif current_user['role'] == 'teacher':
        # Get frames for all students in the class or specific student
        cls = db.classes.find_one({'_id': ObjectId(class_id), 'teacher_email': current_user['email']})
        if not cls:
            return jsonify({'error': 'Class not found'}), 404
        query = {'class_id': class_id}
        if student_filter:
            if student_filter not in cls['student_emails']:
                return jsonify({'error': 'Student not in class'}), 403
            query['student_email'] = student_filter
        else:
            query['student_email'] = {'$in': cls['student_emails']}
        frames = list(db.frames.find(query).sort('_id', -1).limit(limit))
    else:  # admin
        query = {'class_id': class_id}
        if student_filter:
            query['student_email'] = student_filter
        frames = list(db.frames.find(query).sort('_id', -1).limit(limit))

    for frame in frames:
        frame['_id'] = str(frame['_id'])

    return jsonify({'history': frames}), 200

@app.route('/stats/<class_id>', methods=['GET'])
def get_stats(class_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Unauthorized'}), 401

    student_filter = request.args.get('student_email')  # optional

    if current_user['role'] == 'student':
        pipeline = [
            {'$match': {'student_email': current_user['email'], 'class_id': class_id}},
            {'$group': {'_id': None, 'count': {'$sum': 1}, 'average_score': {'$avg': '$focus_score'}}}
        ]
    elif current_user['role'] == 'teacher':
        cls = db.classes.find_one({'_id': ObjectId(class_id), 'teacher_email': current_user['email']})
        if not cls:
            return jsonify({'error': 'Class not found'}), 404
        query_match = {'class_id': class_id}
        if student_filter:
            if student_filter not in cls['student_emails']:
                return jsonify({'error': 'Student not in class'}), 403
            query_match['student_email'] = student_filter
        else:
            query_match['student_email'] = {'$in': cls['student_emails']}
        pipeline = [
            {'$match': query_match},
            {'$group': {'_id': None, 'count': {'$sum': 1}, 'average_score': {'$avg': '$focus_score'}}}
        ]
    else:  # admin
        query_match = {'class_id': class_id}
        if student_filter:
            query_match['student_email'] = student_filter
        pipeline = [
            {'$match': query_match},
            {'$group': {'_id': None, 'count': {'$sum': 1}, 'average_score': {'$avg': '$focus_score'}}}
        ]

    result = list(db.frames.aggregate(pipeline))
    if result:
        stats = result[0]
        stats.pop('_id')
    else:
        stats = {'count': 0, 'average_score': 0.0}

    # Get latest frame
    query_latest = {'class_id': class_id}
    if current_user['role'] == 'student':
        query_latest['student_email'] = current_user['email']
    elif current_user['role'] == 'teacher' and student_filter:
        query_latest['student_email'] = student_filter
    latest = db.frames.find_one(query_latest, sort=[('_id', -1)])
    if latest:
        latest['_id'] = str(latest['_id'])
        stats['latest'] = latest
    else:
        stats['latest'] = None

    return jsonify(stats), 200

@app.route('/meeting_participants/<class_id>', methods=['GET'])
def get_meeting_participants(class_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Unauthorized'}), 401

    # Only teacher or admin can view
    if current_user['role'] not in ['teacher', 'admin']:
        return jsonify({'error': 'Only teachers and admins can view participants'}), 403

    if current_user['role'] == 'teacher':
        cls = db.classes.find_one({'_id': ObjectId(class_id), 'teacher_email': current_user['email']})
        if not cls:
            return jsonify({'error': 'Class not found'}), 404

    participants = list(db.meeting_participants.find({'class_id': class_id}))
    for p in participants:
        p['_id'] = str(p['_id'])

    return jsonify({'participants': participants}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
