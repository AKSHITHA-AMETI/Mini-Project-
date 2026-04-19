import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import jwt
import pytz
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "supports_credentials": True
    }
})
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': 'Student Focus Tracker API is running',
        'server_ip': request.remote_addr,
        'server_host': request.host,
        'endpoints': [
            'POST /register',
            'POST /login',
            'GET /classes',
            'POST /classes',
            'POST /classes/<id>/join',
            'POST /frame',
            'GET /history/<class_id>',
            'GET /attendance/<class_id>',
            'GET /stats/<class_id>',
            'GET /admin/summary'
        ]
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found', 'message': 'Use /register, /login, /classes, etc.'}), 404

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
# Use MongoDB Atlas (cloud) or local MongoDB
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGODB_URI)
db = client['student_focus_tracker']

# ================= Mail =================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['TEACHER_REG_CODE'] = os.getenv('TEACHER_REG_CODE', 'teach1234')
app.config['ADMIN_REG_CODE'] = os.getenv('ADMIN_REG_CODE', 'admin1234')
mail = Mail(app)

# ================= AUTH =================
def get_current_user():
    token = request.headers.get('Authorization')
    if token:
        user_id = verify_token(token)
        if user_id:
            return db.users.find_one({'_id': ObjectId(user_id)})
    return None

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
    secret_code = data.get('secret_code')

    if not all([email, password, role, name]):
        return jsonify({'error': 'Missing fields'}), 400

    if role in ['teacher', 'admin']:
        expected_code = app.config['TEACHER_REG_CODE'] if role == 'teacher' else app.config['ADMIN_REG_CODE']
        if secret_code != expected_code:
            return jsonify({'error': 'Invalid registration secret for role'}), 403

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

    start = datetime.fromisoformat(data['start_time'])
    end = datetime.fromisoformat(data['end_time'])

    if start.tzinfo is None:
        start = ist.localize(start)
    if end.tzinfo is None:
        end = ist.localize(end)

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
        'student_alerts': {},
        'student_status': {},
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
        start = datetime.fromisoformat(cls['start_time'])
        end = datetime.fromisoformat(cls['end_time'])

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

# ================= AVAILABLE CLASSES =================
@app.route('/classes/available', methods=['GET'])
def get_available_classes():
    user = get_current_user()
    if not user or user['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 401

    now = datetime.now(ist)
    classes = list(db.classes.find({
        'student_emails': {'$ne': user['email']},
        'status': {'$ne': 'completed'}
    }))

    for cls in classes:
        start = datetime.fromisoformat(cls['start_time'])
        end = datetime.fromisoformat(cls['end_time'])

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

# ================= JOIN CLASS =================
@app.route('/classes/<class_id>/join', methods=['POST'])
def join_class(class_id):
    user = get_current_user()
    if not user or user['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    cls = db.classes.find_one({'_id': ObjectId(class_id)})
    if not cls:
        return jsonify({'error': 'Class not found'}), 404

    if user['email'] not in cls.get('student_emails', []):
        db.classes.update_one(
            {'_id': ObjectId(class_id)},
            {
                '$addToSet': {'student_emails': user['email']},
                '$set': {f'student_status.{user["email"]}': {'low_focus_count': 0, 'last_frame': None}}
            }
        )

    return jsonify({'message': 'Joined class successfully'}), 200

# ================= FRAME =================
@app.route('/frame', methods=['POST'])
def add_frame():
    user = get_current_user()
    if not user or user['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    class_id = data.get('class_id')
    if not class_id:
        return jsonify({'error': 'Class ID is required'}), 400

    class_doc = db.classes.find_one({'_id': ObjectId(class_id)})
    if not class_doc:
        return jsonify({'error': 'Class not found'}), 404

    if user['email'] not in class_doc.get('student_emails', []):
        return jsonify({'error': 'You must join the class before sending frames'}), 403

    now = datetime.now(ist)
    frame = {
        'timestamp': now.isoformat(),
        'student_email': user['email'],
        'student_id': user.get('student_id'),
        'class_id': class_id,
        'focus_score': data.get('focus_score', 0),
        'face_detected': data.get('face_detected', True)
    }

    db.frames.insert_one(frame)

    student_status = class_doc.get('student_status', {})
    student_record = student_status.get(user['email'], {'low_focus_count': 0, 'last_frame': None})

    if student_record.get('last_frame'):
        last_time = datetime.fromisoformat(student_record['last_frame'])
        gap = now - last_time
    else:
        gap = None

    # Inactivity alert for teacher when a student returns after a long pause
    inactivity_threshold = timedelta(minutes=10)
    teacher_email = class_doc.get('teacher_email')
    if gap and gap > inactivity_threshold and class_doc.get('status') == 'active' and teacher_email:
        send_alert(teacher_email, f"Student {user.get('student_id') or user['email']} was inactive for {int(gap.total_seconds() / 60)} minutes in {class_doc['class_name']}.")

    if frame['focus_score'] < 4:
        student_record['low_focus_count'] = student_record.get('low_focus_count', 0) + 1
        if student_record['low_focus_count'] == 2:
            send_alert(user['email'], f"Low focus alert: your focus score is low in class {class_doc['class_name']}. Please pay attention.")
        elif student_record['low_focus_count'] >= 3 and teacher_email:
            send_alert(teacher_email, f"Student {user.get('student_id') or user['email']} has been low focus repeatedly in {class_doc['class_name']}.")
    else:
        student_record['low_focus_count'] = 0

    student_record['last_frame'] = now.isoformat()
    student_status[user['email']] = student_record
    db.classes.update_one({'_id': class_doc['_id']}, {'$set': {'student_status': student_status}})

    if not frame['face_detected']:
        send_alert(user['email'], 'Face not detected. Please adjust your camera.')

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
@app.route('/attendance/<class_id>', methods=['GET'])
def get_attendance(class_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    cls = db.classes.find_one({'_id': ObjectId(class_id)})
    if not cls:
        return jsonify({'error': 'Class not found'}), 404

    if user['role'] == 'teacher' and cls.get('teacher_email') != user['email']:
        return jsonify({'error': 'Unauthorized'}), 403
    if user['role'] == 'student' and user['email'] not in cls.get('student_emails', []):
        return jsonify({'error': 'Unauthorized'}), 403

    attendance = []
    for student_email in cls.get('student_emails', []):
        student_user = db.users.find_one({'email': student_email})
        student_name = student_user['name'] if student_user else student_email
        student_id = student_user.get('student_id') if student_user else None
        frames = list(db.frames.find({'class_id': class_id, 'student_email': student_email}))
        avg_focus = round(sum(f.get('focus_score', 0) for f in frames) / len(frames), 1) if frames else 0
        attended = len(frames) > 0
        last_seen = frames[-1]['timestamp'] if frames else None
        inactive = False
        if last_seen:
            last_time = datetime.fromisoformat(last_seen)
            inactive = (datetime.now(ist) - last_time) > timedelta(minutes=10)
        attendance.append({
            'student_name': student_name,
            'student_email': student_email,
            'student_id': student_id,
            'attended': attended,
            'avg_attention': avg_focus,
            'frames_sent': len(frames),
            'last_seen': last_seen,
            'inactive': inactive
        })

    return jsonify(attendance), 200

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

# ================= ADMIN =================
@app.route('/admin/summary', methods=['GET'])
def get_admin_summary():
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    summary = {
        'total_users': db.users.count_documents({}),
        'students': db.users.count_documents({'role': 'student'}),
        'teachers': db.users.count_documents({'role': 'teacher'}),
        'classes': db.classes.count_documents({}),
        'active_classes': db.classes.count_documents({'status': 'active'}),
        'upcoming_classes': db.classes.count_documents({'status': 'upcoming'}),
        'completed_classes': db.classes.count_documents({'status': 'completed'})
    }

    return jsonify(summary), 200

# ================= RUN =================
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)