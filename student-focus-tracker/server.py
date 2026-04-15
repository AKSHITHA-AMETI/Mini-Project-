import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import jwt
import pytz

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')

# IST timezone
ist = pytz.timezone('Asia/Kolkata')

# ================= JWT =================
def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.now(ist) + timedelta(hours=24)
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except:
        return None

# ================= DB =================
client = MongoClient('mongodb://localhost:27017/')
db = client['student_focus_tracker']

# ================= Mail =================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
mail = Mail(app)

# ================= AUTH =================
def get_current_user():
    token = request.headers.get('Authorization')
    if token:
        user_id = verify_token(token)
        if user_id:
            return db.users.find_one({'_id': ObjectId(user_id)})
    return None

def parse_ist_datetime(dt_str):
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        return ist.localize(dt)
    return dt.astimezone(ist)

# ================= REGISTER =================
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    name = data.get('name')
    class_name = data.get('class_name') if role == 'student' else None
    student_id = data.get('student_id') if role == 'student' else None

    if not all([email, password, role, name]):
        return jsonify({'error': 'Missing fields'}), 400

    if db.users.find_one({'email': email}):
        return jsonify({'error': 'User exists'}), 400

    db.users.insert_one({
        'email': email,
        'password': generate_password_hash(password),
        'role': role,
        'name': name,
        'class_name': class_name,
        'student_id': student_id
    })

    return jsonify({'message': 'Registered'}), 201

# ================= LOGIN =================
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    user = db.users.find_one({'email': data.get('email')})
    if user and check_password_hash(user['password'], data.get('password')):
        token = generate_token(str(user['_id']))
        return jsonify({
            'token': token,
            'user': {
                'email': user['email'],
                'name': user['name'],
                'role': user['role'],
                'student_id': user.get('student_id')
            }
        }), 200

    return jsonify({'error': 'Invalid credentials'}), 401

# ================= CREATE CLASS =================
@app.route('/classes', methods=['POST'])
def create_class():
    user = get_current_user()
    if not user or user['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()

    start = parse_ist_datetime(data['start_time'])
    end = parse_ist_datetime(data['end_time'])

    now = datetime.now(ist)

    if now < start:
        status = 'upcoming'
    elif start <= now <= end:
        status = 'active'
    else:
        status = 'completed'

    db.classes.insert_one({
        'teacher_email': user['email'],
        'class_name': data['class_name'],
        'student_emails': data.get('student_emails', []),
        'start_time': start.isoformat(),
        'end_time': end.isoformat(),
        'meeting_url': data['meeting_url'],
        'status': status
    })

    return jsonify({'message': 'Class created', 'status': status}), 201

# ================= GET CLASSES =================
@app.route('/classes', methods=['GET'])
def get_classes():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    now = datetime.now(ist)

    query = {}
    if user['role'] == 'teacher':
        query['teacher_email'] = user['email']
    elif user['role'] == 'student':
        query['student_emails'] = user['email']

    classes = list(db.classes.find(query))

    for cls in classes:
        start = parse_ist_datetime(cls['start_time'])
        end = parse_ist_datetime(cls['end_time'])

        if cls['status'] != 'completed':
            if now < start:
                new_status = 'upcoming'
            elif start <= now <= end:
                new_status = 'active'
            else:
                new_status = 'completed'

            if new_status != cls['status']:
                db.classes.update_one({'_id': cls['_id']}, {'$set': {'status': new_status}})
                cls['status'] = new_status

        cls['_id'] = str(cls['_id'])

    return jsonify(classes), 200

# ================= CLASS STATUS =================
@app.route('/classes/<class_id>/status', methods=['GET'])
def get_class_status(class_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    cls = db.classes.find_one({'_id': ObjectId(class_id)})
    if not cls:
        return jsonify({'error': 'Class not found'}), 404

    now = datetime.now(ist)
    start = parse_ist_datetime(cls['start_time'])
    end = parse_ist_datetime(cls['end_time'])

    current_status = cls['status']
    if current_status != 'completed':
        if now < start:
            current_status = 'upcoming'
        elif start <= now <= end:
            current_status = 'active'
        else:
            current_status = 'completed'
        if current_status != cls['status']:
            db.classes.update_one({'_id': cls['_id']}, {'$set': {'status': current_status}})
            cls['status'] = current_status

    return jsonify({
        'status': cls['status'],
        'class_name': cls['class_name'],
        'start_time': cls['start_time'],
        'end_time': cls['end_time']
    }), 200

# ================= FRAME =================
@app.route('/frame', methods=['POST'])
def add_frame():
    user = get_current_user()
    if not user or user['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()

    frame = {
        'timestamp': datetime.now(ist).isoformat(),
        'student_email': user['email'],
        'student_id': user.get('student_id'),
        'class_id': data.get('class_id'),
        'focus_score': data.get('focus_score', 0),
        'face_detected': data.get('face_detected', True)
    }

    db.frames.insert_one(frame)

    if frame['focus_score'] < 50:
        send_alert(user['email'], 'Low focus')

    if not frame['face_detected']:
        send_alert(user['email'], 'Face not detected')

    return jsonify({'status': 'ok'}), 201

# ================= ALERT =================
def send_alert(email, message):
    try:
        msg = Message(
            'Alert',
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = message
        mail.send(msg)
    except Exception as e:
        print("Mail error:", e)

# ================= HISTORY =================
@app.route('/history/<class_id>', methods=['GET'])
def get_history(class_id):
    frames = list(db.frames.find({'class_id': class_id}).sort('_id', -1).limit(200))

    for f in frames:
        f['_id'] = str(f['_id'])

    return jsonify({'history': frames}), 200

# ================= STATS =================
@app.route('/stats/<class_id>', methods=['GET'])
def get_stats(class_id):
    result = list(db.frames.aggregate([
        {'$match': {'class_id': class_id}},
        {'$group': {'_id': None, 'avg': {'$avg': '$focus_score'}, 'count': {'$sum': 1}}}
    ]))

    if result:
        data = result[0]
        return jsonify({'average': data['avg'], 'count': data['count']}), 200

    return jsonify({'average': 0, 'count': 0}), 200

# ================= RUN =================
if __name__ == '__main__':
    app.run(debug=True)