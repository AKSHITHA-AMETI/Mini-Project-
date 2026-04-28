import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import jwt
import pytz
from flask_cors import CORS
from dotenv import load_dotenv
import subprocess
import platform
import ssl

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
            'GET /classes/<id>/status',
            'POST /start-tracking/<id>',
            'POST /frame',
            'GET /history/<class_id>',
            'GET /tracking-logs/<class_id>',
            'GET /attendance/<class_id>',
            'GET /stats/<class_id>',
            'GET /admin/summary'
        ]
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint to verify API and database connectivity"""
    try:
        client.admin.command('ismaster')
        db_status = 'connected'
    except Exception as e:
        db_status = f'disconnected: {str(e)}'
    
    return jsonify({
        'status': 'ok',
        'api': 'running',
        'database': db_status,
        'server_ip': request.remote_addr,
        'server_host': request.host
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

# If it's MongoDB Atlas, add SSL bypass to connection string
if 'mongodb+srv://' in MONGODB_URI and '&tlsInsecure=' not in MONGODB_URI:
    MONGODB_URI = MONGODB_URI + ('&' if '?' in MONGODB_URI else '?') + 'tlsInsecure=true'

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=10000)
    # Test the connection
    client.admin.command('ismaster')
    print("[SUCCESS] MongoDB connected successfully")
except ServerSelectionTimeoutError as e:
    print(f"[WARNING] MongoDB connection timeout - retrying without timeout...")
    try:
        # Try again without strict timeout for initial connection
        client = MongoClient(MONGODB_URI)
        print("[SUCCESS] MongoDB connected (with extended timeout)")
    except Exception as e2:
        print(f"[ERROR] MongoDB connection failed: {e2}")
        client = MongoClient(MONGODB_URI)
except Exception as e:
    print(f"[ERROR] MongoDB connection error: {e}")
    print("[INFO] Attempting fallback connection...")
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
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', '').strip()
        name = data.get('name', '').strip()
        class_name = data.get('class_name', '') if role == 'student' else None
        student_id = data.get('student_id', '').strip() if role == 'student' else None
        secret_code = data.get('secret_code', '').strip()

        # Validate required fields
        if not all([email, password, role, name]):
            missing = []
            if not email:
                missing.append('email')
            if not password:
                missing.append('password')
            if not role:
                missing.append('role')
            if not name:
                missing.append('name')
            return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

        # Validate email format
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Invalid email format'}), 400

        # Validate password length
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        # Validate role
        if role not in ['student', 'teacher', 'admin']:
            return jsonify({'error': 'Invalid role. Must be student, teacher, or admin'}), 400

        # Check secret code for teacher and admin
        if role in ['teacher', 'admin']:
            expected_code = app.config['TEACHER_REG_CODE'] if role == 'teacher' else app.config['ADMIN_REG_CODE']
            if not secret_code:
                return jsonify({'error': f'{role.capitalize()} registration code is required'}), 400
            if secret_code != expected_code:
                return jsonify({'error': f'Invalid {role} registration code'}), 403

        # Check if user already exists
        if db.users.find_one({'email': email}):
            return jsonify({'error': 'User with this email already exists'}), 409

        # Create user document
        user_doc = {
            'email': email,
            'password': generate_password_hash(password),
            'role': role,
            'name': name,
            'created_at': datetime.now(ist).isoformat()
        }

        if role == 'student':
            user_doc['class_name'] = class_name
            user_doc['student_id'] = student_id

        result = db.users.insert_one(user_doc)

        return jsonify({
            'message': 'Registration successful',
            'user_id': str(result.inserted_id)
        }), 201

    except Exception as e:
        print(f"Register error: {e}")
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

# ================= LOGIN =================
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        email = data.get('email', '').strip()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        user = db.users.find_one({'email': email})
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401

        if not check_password_hash(user['password'], password):
            return jsonify({'error': 'Invalid email or password'}), 401

        token = generate_token(str(user['_id']))
        return jsonify({
            'token': token,
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'name': user['name'],
                'role': user['role'],
                'student_id': user.get('student_id')
            }
        }), 200

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Login failed. Please try again.'}), 500

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

# ================= CLASS STATUS =================
@app.route('/classes/<class_id>/status', methods=['GET'])
def get_class_status(class_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    cls = db.classes.find_one({'_id': ObjectId(class_id)})
    if not cls:
        return jsonify({'error': 'Class not found'}), 404

    # Update status based on current time
    now = datetime.now(ist)
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
            db.classes.update_one({'_id': ObjectId(class_id)}, {'$set': {'status': new_status}})
            cls['status'] = new_status

    return jsonify({'status': cls['status'], '_id': str(cls['_id']), 'class_name': cls['class_name']}), 200

# ================= UPLOAD LOCAL FOCUS DATA =================
@app.route('/upload-focus-data/<class_id>', methods=['POST'])
def upload_focus_data(class_id):
    """Endpoint for devices to upload their local focus tracking data"""
    user = get_current_user()
    if not user or user['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    class_doc = db.classes.find_one({'_id': ObjectId(class_id)})
    if not class_doc:
        return jsonify({'error': 'Class not found'}), 404

    if user['email'] not in class_doc.get('student_emails', []):
        return jsonify({'error': 'You must join the class before uploading data'}), 403

    try:
        data = request.get_json()
        device_id = data.get('device_id', f"device_{os.getpid()}")

        if not data.get('focus_data') or not isinstance(data['focus_data'], list):
            return jsonify({'error': 'focus_data array is required'}), 400

        uploaded_count = 0
        for frame in data['focus_data']:
            # Add device and student identification
            frame['student_email'] = user['email']
            frame['student_id'] = user.get('student_id')
            frame['class_id'] = class_id
            frame['device_id'] = device_id
            frame['uploaded_at'] = datetime.now(ist).isoformat()

            # Insert into database
            db.frames.insert_one(frame)
            uploaded_count += 1

        # Update student status
        student_status = class_doc.get('student_status', {})
        student_record = student_status.get(user['email'], {'low_focus_count': 0, 'last_frame': None, 'devices': []})

        if device_id not in student_record.get('devices', []):
            student_record['devices'] = student_record.get('devices', []) + [device_id]

        student_record['last_upload'] = datetime.now(ist).isoformat()
        student_status[user['email']] = student_record
        db.classes.update_one({'_id': class_doc['_id']}, {'$set': {'student_status': student_status}})

        return jsonify({
            'message': f'Successfully uploaded {uploaded_count} focus data points',
            'device_id': device_id,
            'uploaded_count': uploaded_count
        }), 201

    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': 'Failed to upload focus data'}), 500

# ================= GET MULTI-DEVICE STATS =================
@app.route('/multi-device-stats/<class_id>', methods=['GET'])
def get_multi_device_stats(class_id):
    """Get aggregated stats from all devices for a class"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    class_doc = db.classes.find_one({'_id': ObjectId(class_id)})
    if not class_doc:
        return jsonify({'error': 'Class not found'}), 404

    if user['role'] == 'teacher' and class_doc.get('teacher_email') != user['email']:
        return jsonify({'error': 'Unauthorized'}), 403
    if user['role'] == 'student' and user['email'] not in class_doc.get('student_emails', []):
        return jsonify({'error': 'Unauthorized'}), 403

    # Aggregate data by student, combining all their devices
    pipeline = [
        {'$match': {'class_id': class_id}},
        {'$group': {
            '_id': '$student_email',
            'avg_focus': {'$avg': '$focus_score'},
            'total_frames': {'$sum': 1},
            'devices': {'$addToSet': '$device_id'},
            'latest_timestamp': {'$max': '$timestamp'},
            'focus_scores': {'$push': '$focus_score'},
            'gaze_directions': {'$push': '$gaze'},
            'head_directions': {'$push': '$head_direction'},
            'yawning_events': {'$sum': {'$cond': ['$yawning', 1, 0]}},
            'laughing_events': {'$sum': {'$cond': ['$laughing', 1, 0]}},
            'eyes_closed_events': {'$sum': {'$cond': [{'$eq': ['$gaze', 'Eyes Closed']}, 1, 0]}}
        }}
    ]

    results = list(db.frames.aggregate(pipeline))

    # Enrich with user details
    enriched_results = []
    for result in results:
        student_email = result['_id']
        student_user = db.users.find_one({'email': student_email})

        if student_user:
            # Calculate focus score distribution
            focus_scores = result.get('focus_scores', [])
            low_focus_count = sum(1 for score in focus_scores if score < 4)
            high_focus_count = sum(1 for score in focus_scores if score >= 7)

            enriched_results.append({
                'student_email': student_email,
                'student_name': student_user.get('name', student_email),
                'student_id': student_user.get('student_id'),
                'avg_focus_score': round(result.get('avg_focus', 0), 1),
                'total_frames': result.get('total_frames', 0),
                'device_count': len(result.get('devices', [])),
                'devices': result.get('devices', []),
                'latest_activity': result.get('latest_timestamp'),
                'focus_distribution': {
                    'low': low_focus_count,
                    'medium': len(focus_scores) - low_focus_count - high_focus_count,
                    'high': high_focus_count
                },
                'behavioral_events': {
                    'yawning': result.get('yawning_events', 0),
                    'laughing': result.get('laughing_events', 0),
                    'eyes_closed': result.get('eyes_closed_events', 0)
                },
                'gaze_summary': summarize_gaze_directions(result.get('gaze_directions', [])),
                'head_pose_summary': summarize_head_directions(result.get('head_directions', []))
            })

    return jsonify({
        'class_id': class_id,
        'class_name': class_doc.get('class_name'),
        'total_students': len(enriched_results),
        'student_stats': enriched_results
    }), 200

def summarize_gaze_directions(gaze_list):
    """Summarize gaze directions into counts"""
    summary = {}
    for gaze in gaze_list:
        if gaze:
            summary[gaze] = summary.get(gaze, 0) + 1
    return summary

def summarize_head_directions(head_list):
    """Summarize head directions into counts"""
    summary = {}
    for head in head_list:
        if head:
            summary[head] = summary.get(head, 0) + 1
    return summary

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

# ================= START TRACKING =================
@app.route('/start-tracking/<class_id>', methods=['POST'])
def start_tracking(class_id):
    print(f"[{datetime.now(ist)}] START-TRACKING called for class {class_id}")
    
    user = get_current_user()
    if not user or user['role'] != 'student':
        print(f"[{datetime.now(ist)}] Unauthorized: user={user}, role={user.get('role') if user else 'None'}")
        return jsonify({'error': 'Unauthorized'}), 403

    cls = db.classes.find_one({'_id': ObjectId(class_id)})
    if not cls:
        print(f"[{datetime.now(ist)}] Class not found: {class_id}")
        return jsonify({'error': 'Class not found'}), 404

    if user['email'] not in cls.get('student_emails', []):
        print(f"[{datetime.now(ist)}] User not in class: {user['email']} not in {cls.get('student_emails', [])}")
        return jsonify({'error': 'You must join the class before tracking'}), 403

    if cls.get('status') != 'active':
        print(f"[{datetime.now(ist)}] Class not active: status={cls.get('status')}")
        return jsonify({'error': 'Class is not active'}), 400

    try:
        # Get the token from the Authorization header
        token = request.headers.get('Authorization', '')
        print(f"[{datetime.now(ist)}] Token length: {len(token)}")
        
        # Get the directory where server.py is located
        base_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"[{datetime.now(ist)}] Base dir: {base_dir}")
        
        # Create a log file for tracking subprocess
        log_file_path = os.path.join(base_dir, f'tracking_{class_id}.log')
        print(f"[{datetime.now(ist)}] Log file: {log_file_path}")
        
        try:
            # Windows environment setup
            env = os.environ.copy()
            env['FOCUS_API_URL'] = 'http://localhost:5000'
            
            # Build command
            if platform.system() == 'Windows':
                cmd = ['python', 'main.py', class_id, token, '--headless']
            else:
                cmd = ['python3', 'main.py', class_id, token, '--headless']
            
            print(f"[{datetime.now(ist)}] Launching subprocess: {' '.join(cmd[:3])}... in {base_dir}")
            
            # Launch tracking with proper file handling
            with open(log_file_path, 'a') as log_file:
                log_file.write(f"\n{'='*60}\n")
                log_file.write(f"Started at: {datetime.now(ist)}\n")
                log_file.write(f"Student: {user['email']}\n")
                log_file.write(f"Class ID: {class_id}\n")
                log_file.write(f"Command: {' '.join(cmd)}\n")
                log_file.write(f"Working dir: {base_dir}\n")
                log_file.write(f"{'='*60}\n\n")
                log_file.flush()
                
                proc = subprocess.Popen(
                    cmd,
                    cwd=base_dir,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == 'Windows' else 0
                )
            
            print(f"[{datetime.now(ist)}] Subprocess PID: {proc.pid}")
            print(f"[{datetime.now(ist)}] Log file: {log_file_path}")
            
            return jsonify({'message': 'Tracking started successfully', 'pid': proc.pid, 'log_file': log_file_path}), 200
            
        except Exception as subprocess_error:
            error_msg = str(subprocess_error)
            print(f"[{datetime.now(ist)}] Subprocess error: {error_msg}")
            
            # Write error to log file for debugging
            with open(log_file_path, 'a') as log_file:
                log_file.write(f"ERROR: {error_msg}\n")
            
            return jsonify({'error': f'Subprocess error: {error_msg}'}), 500
            
    except Exception as e:
        print(f"[{datetime.now(ist)}] Error starting tracking: {e}")
        return jsonify({'error': f'Failed to start tracking: {str(e)}'}), 500

# ================= TRACKING LOGS =================
@app.route('/tracking-logs/<class_id>', methods=['GET'])
def get_tracking_logs(class_id):
    """Get the tracking log file for debugging"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(base_dir, f'tracking_{class_id}.log')
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.read()
            return jsonify({'logs': logs, 'file': log_file}), 200
        else:
            return jsonify({'logs': '', 'message': 'No log file found yet', 'file': log_file}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to read logs: {str(e)}'}), 500

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

# ================= FRAME (REAL-TIME TRACKING) =================
@app.route('/frame', methods=['POST'])
def receive_frame():
    """Receive real-time tracking frame data from tracking subprocess"""
    try:
        data = request.get_json()
        
        if not data or 'class_id' not in data:
            return jsonify({'error': 'class_id is required'}), 400
        
        class_id = data.get('class_id')
        
        # Validate class exists
        cls = db.classes.find_one({'_id': ObjectId(class_id)})
        if not cls:
            return jsonify({'error': 'Class not found'}), 404
        
        # Add server-side timestamp and store
        data['timestamp'] = datetime.now(ist).isoformat()
        data['class_id'] = class_id
        
        # Insert frame data
        db.frames.insert_one(data)
        
        return jsonify({'message': 'Frame received', 'id': str(data['_id'])}), 201
    
    except Exception as e:
        print(f"[{datetime.now(ist)}] Frame receive error: {e}")
        return jsonify({'error': str(e)}), 500

# ================= STOP TRACKING =================
@app.route('/stop-tracking/<class_id>', methods=['POST'])
def stop_tracking(class_id):
    """Stop tracking for a class and clean up subprocess"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    cls = db.classes.find_one({'_id': ObjectId(class_id)})
    if not cls:
        return jsonify({'error': 'Class not found'}), 404

    # Check authorization (student in class or teacher of class)
    if user['role'] == 'student' and user['email'] not in cls.get('student_emails', []):
        return jsonify({'error': 'Unauthorized'}), 403
    if user['role'] == 'teacher' and cls.get('teacher_email') != user['email']:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        # Try to find and kill the tracking subprocess
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(base_dir, f'tracking_{class_id}.log')
        
        print(f"[{datetime.now(ist)}] Stopping tracking for class {class_id}")
        
        # Write stop signal to log for subprocess detection
        if os.path.exists(log_file):
            with open(log_file, 'a') as f:
                f.write(f"\n[{datetime.now(ist)}] STOP signal received\n")
        
        # On Windows, try to kill process using taskill
        if platform.system() == 'Windows':
            try:
                # Find and kill python processes running main.py for this class
                os.system(f'taskkill /F /IM python.exe /T 2>nul')
            except:
                pass
        else:
            # On Linux/Mac
            try:
                os.system(f'pkill -f "main.py.*{class_id}"')
            except:
                pass
        
        print(f"[{datetime.now(ist)}] Tracking stopped for class {class_id}")
        
        return jsonify({'message': 'Tracking stopped successfully'}), 200
    
    except Exception as e:
        print(f"[{datetime.now(ist)}] Stop tracking error: {e}")
        return jsonify({'error': str(e)}), 500

# ================= COMPLETE CLASS =================
@app.route('/classes/<class_id>/complete', methods=['POST'])
def complete_class(class_id):
    """Manually mark a class as completed"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    cls = db.classes.find_one({'_id': ObjectId(class_id)})
    if not cls:
        return jsonify({'error': 'Class not found'}), 404

    # Only teacher can complete their class
    if user['role'] != 'teacher' or cls.get('teacher_email') != user['email']:
        return jsonify({'error': 'Only class teacher can complete a class'}), 403

    try:
        # Update class status
        db.classes.update_one(
            {'_id': ObjectId(class_id)},
            {
                '$set': {
                    'status': 'completed',
                    'completed_at': datetime.now(ist).isoformat(),
                    'completed_by': user['email']
                }
            }
        )
        
        return jsonify({'message': 'Class marked as completed', 'status': 'completed'}), 200
    
    except Exception as e:
        print(f"[{datetime.now(ist)}] Complete class error: {e}")
        return jsonify({'error': str(e)}), 500

# ================= TEACHER DASHBOARD =================
@app.route('/teacher/classes', methods=['GET'])
def get_teacher_classes():
    """Get all classes for a teacher with detailed stats"""
    user = get_current_user()
    if not user or user['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        now = datetime.now(ist)
        classes = list(db.classes.find({'teacher_email': user['email']}))
        
        class_stats = []
        for cls in classes:
            # Update status based on current time
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
            
            # Get student focus statistics
            student_stats = []
            for student_email in cls.get('student_emails', []):
                student_user = db.users.find_one({'email': student_email})
                frames = list(db.frames.find({'class_id': str(cls['_id']), 'student_email': student_email}))
                
                if frames:
                    focus_scores = [f.get('focus_score', 0) for f in frames]
                    avg_focus = sum(focus_scores) / len(focus_scores)
                    low_focus = sum(1 for s in focus_scores if s < 4)
                    
                    # Count behavioral events
                    yawns = sum(1 for f in frames if f.get('yawning'))
                    laughs = sum(1 for f in frames if f.get('laughing'))
                    eyes_closed = sum(1 for f in frames if f.get('gaze') == 'Eyes Closed')
                    
                    student_stats.append({
                        'student_name': student_user['name'] if student_user else student_email,
                        'student_email': student_email,
                        'student_id': student_user.get('student_id') if student_user else None,
                        'avg_focus_score': round(avg_focus, 1),
                        'total_frames': len(frames),
                        'low_focus_frames': low_focus,
                        'yawning_events': yawns,
                        'laughing_events': laughs,
                        'eyes_closed_events': eyes_closed,
                        'attendance': 'Present' if frames else 'Absent'
                    })
            
            class_stats.append({
                'class_id': str(cls['_id']),
                'class_name': cls['class_name'],
                'status': cls['status'],
                'start_time': cls['start_time'],
                'end_time': cls['end_time'],
                'meeting_url': cls['meeting_url'],
                'student_count': len(cls.get('student_emails', [])),
                'students_present': sum(1 for s in student_stats if s['attendance'] == 'Present'),
                'avg_class_focus': round(sum(s['avg_focus_score'] for s in student_stats) / len(student_stats), 1) if student_stats else 0,
                'student_stats': student_stats
            })
        
        return jsonify(class_stats), 200
    
    except Exception as e:
        print(f"[{datetime.now(ist)}] Teacher classes error: {e}")
        return jsonify({'error': str(e)}), 500

# ================= TEACHER CLASS DETAIL =================
@app.route('/teacher/classes/<class_id>', methods=['GET'])
def get_teacher_class_detail(class_id):
    """Get detailed analytics for a specific class"""
    user = get_current_user()
    if not user or user['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    cls = db.classes.find_one({'_id': ObjectId(class_id)})
    if not cls or cls.get('teacher_email') != user['email']:
        return jsonify({'error': 'Class not found'}), 404

    try:
        # Get all frame data for the class
        frames = list(db.frames.find({'class_id': class_id}))
        
        if not frames:
            return jsonify({
                'class_id': class_id,
                'class_name': cls['class_name'],
                'status': cls['status'],
                'student_stats': [],
                'class_insights': {'avg_focus': 0, 'total_frames': 0}
            }), 200
        
        # Aggregate by student
        student_data = {}
        for frame in frames:
            email = frame.get('student_email', 'Unknown')
            if email not in student_data:
                student_data[email] = {
                    'frames': [],
                    'focus_scores': [],
                    'yawns': 0,
                    'laughs': 0,
                    'eyes_closed': 0
                }
            
            student_data[email]['frames'].append(frame)
            student_data[email]['focus_scores'].append(frame.get('focus_score', 0))
            
            if frame.get('yawning'):
                student_data[email]['yawns'] += 1
            if frame.get('laughing'):
                student_data[email]['laughs'] += 1
            if frame.get('gaze') == 'Eyes Closed':
                student_data[email]['eyes_closed'] += 1
        
        # Build student stats
        student_stats = []
        for email, data in student_data.items():
            student_user = db.users.find_one({'email': email})
            scores = data['focus_scores']
            
            student_stats.append({
                'student_name': student_user['name'] if student_user else email,
                'student_email': email,
                'student_id': student_user.get('student_id') if student_user else None,
                'avg_focus': round(sum(scores) / len(scores), 1),
                'min_focus': min(scores),
                'max_focus': max(scores),
                'total_frames': len(scores),
                'behavioral_events': {
                    'yawning': data['yawns'],
                    'laughing': data['laughs'],
                    'eyes_closed': data['eyes_closed']
                }
            })
        
        # Class insights
        all_scores = [f.get('focus_score', 0) for f in frames]
        class_insights = {
            'avg_focus': round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
            'total_frames': len(frames),
            'total_students_participated': len(student_data),
            'total_yawning_events': sum(1 for f in frames if f.get('yawning')),
            'total_laughing_events': sum(1 for f in frames if f.get('laughing')),
            'total_eyes_closed_events': sum(1 for f in frames if f.get('gaze') == 'Eyes Closed'),
            'focus_distribution': {
                'low': sum(1 for s in all_scores if s < 4),
                'medium': sum(1 for s in all_scores if 4 <= s < 7),
                'high': sum(1 for s in all_scores if s >= 7)
            }
        }
        
        return jsonify({
            'class_id': class_id,
            'class_name': cls['class_name'],
            'status': cls['status'],
            'start_time': cls['start_time'],
            'end_time': cls['end_time'],
            'student_stats': student_stats,
            'class_insights': class_insights
        }), 200
    
    except Exception as e:
        print(f"[{datetime.now(ist)}] Teacher class detail error: {e}")
        return jsonify({'error': str(e)}), 500

# ================= ADMIN DASHBOARD =================
@app.route('/admin/dashboard', methods=['GET'])
def get_admin_dashboard():
    """Get comprehensive admin dashboard with all system statistics"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        now = datetime.now(ist)
        
        # System statistics
        total_users = db.users.count_documents({})
        students = db.users.count_documents({'role': 'student'})
        teachers = db.users.count_documents({'role': 'teacher'})
        admins = db.users.count_documents({'role': 'admin'})
        
        # Class statistics
        total_classes = db.classes.count_documents({})
        upcoming_classes = db.classes.count_documents({'status': 'upcoming'})
        active_classes = db.classes.count_documents({'status': 'active'})
        completed_classes = db.classes.count_documents({'status': 'completed'})
        
        # Frame/tracking statistics
        total_frames = db.frames.count_documents({})
        avg_focus = 0
        if total_frames > 0:
            result = list(db.frames.aggregate([
                {'$group': {'_id': None, 'avg': {'$avg': '$focus_score'}}}
            ]))
            avg_focus = round(result[0]['avg'], 1) if result else 0
        
        # Behavioral events statistics
        yawning_events = db.frames.count_documents({'yawning': True})
        laughing_events = db.frames.count_documents({'laughing': True})
        eyes_closed_events = db.frames.count_documents({'gaze': 'Eyes Closed'})
        
        # Get top teachers by class count
        teacher_stats = list(db.classes.aggregate([
            {'$group': {
                '_id': '$teacher_email',
                'class_count': {'$sum': 1},
                'total_students': {'$sum': {'$size': '$student_emails'}}
            }},
            {'$sort': {'class_count': -1}},
            {'$limit': 5}
        ]))
        
        # Enrich teacher stats with names
        enriched_teachers = []
        for ts in teacher_stats:
            teacher_user = db.users.find_one({'email': ts['_id']})
            enriched_teachers.append({
                'teacher_email': ts['_id'],
                'teacher_name': teacher_user['name'] if teacher_user else ts['_id'],
                'total_classes': ts['class_count'],
                'total_students_taught': ts['total_students']
            })
        
        return jsonify({
            'system_stats': {
                'total_users': total_users,
                'students': students,
                'teachers': teachers,
                'admins': admins
            },
            'class_stats': {
                'total_classes': total_classes,
                'upcoming': upcoming_classes,
                'active': active_classes,
                'completed': completed_classes
            },
            'tracking_stats': {
                'total_frames_received': total_frames,
                'avg_focus_score': avg_focus,
                'behavioral_events': {
                    'yawning': yawning_events,
                    'laughing': laughing_events,
                    'eyes_closed': eyes_closed_events
                }
            },
            'top_teachers': enriched_teachers
        }), 200
    
    except Exception as e:
        print(f"[{datetime.now(ist)}] Admin dashboard error: {e}")
        return jsonify({'error': str(e)}), 500

# ================= RUN =================
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)