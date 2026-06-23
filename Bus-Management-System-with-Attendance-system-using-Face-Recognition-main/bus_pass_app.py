from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import cv2
import numpy as np
import os
import sqlite3
import json
import base64
import hashlib
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
app = Flask(__name__)
app.secret_key = 'smart_campus_transit_2024'

# Configuration
UPLOAD_FOLDER = 'static/uploads'
KNOWN_FACES_FOLDER = 'static/known_faces'
PASS_PHOTOS_FOLDER = 'static/pass_photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create directories
for folder in [UPLOAD_FOLDER, KNOWN_FACES_FOLDER, PASS_PHOTOS_FOLDER, 'static/temp']:
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['KNOWN_FACES_FOLDER'] = KNOWN_FACES_FOLDER
app.config['PASS_PHOTOS_FOLDER'] = PASS_PHOTOS_FOLDER

# Initialize face cascade
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Database initialization
def init_db():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            phone_number TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            roll_number TEXT UNIQUE,
            department TEXT,
            year TEXT,
            phone_number TEXT,
            father_name TEXT,
            father_phone TEXT,
            address TEXT,
            face_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bus_passes (
            pass_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            pass_number TEXT UNIQUE NOT NULL,
            issue_date DATE,
            expiry_date DATE,
            route TEXT,
            status TEXT DEFAULT 'pending',
            photo_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (student_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            pass_id INTEGER,
            date DATE,
            boarding_time TIME,
            drop_time TIME,
            verification_type TEXT,
            status TEXT DEFAULT 'present',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (student_id),
            FOREIGN KEY (pass_id) REFERENCES bus_passes (pass_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bus_locations (
            location_id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER,
            current_location TEXT,
            destination TEXT,
            distance_left TEXT,
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS routes (
            route_id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_name TEXT UNIQUE NOT NULL,
            start_point TEXT,
            end_point TEXT,
            stops TEXT,
            driver_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (driver_id) REFERENCES users (user_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bus_stops (
            stop_id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id INTEGER,
            stop_name TEXT NOT NULL,
            stop_time TIME,
            amount INTEGER DEFAULT 0,
            stop_order INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (route_id) REFERENCES routes (route_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS driver_parent_messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER,
            student_id INTEGER,
            sender_type TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (driver_id) REFERENCES users (user_id),
            FOREIGN KEY (student_id) REFERENCES students (student_id)
        )
    ''')
    
    # Add new columns to existing tables (safe if already exist)
    for alter_sql in [
        "ALTER TABLE routes ADD COLUMN driver_id INTEGER",
        "ALTER TABLE routes ADD COLUMN vehicle_no TEXT",
        "ALTER TABLE routes ADD COLUMN driver_name TEXT",
        "ALTER TABLE routes ADD COLUMN driver_phone TEXT",
        "ALTER TABLE bus_passes ADD COLUMN boarding_stop TEXT",
        "ALTER TABLE bus_passes ADD COLUMN pass_amount INTEGER DEFAULT 0",
        "ALTER TABLE students ADD COLUMN route_id INTEGER",
        "ALTER TABLE students ADD COLUMN parent_password TEXT",
        "ALTER TABLE bus_locations ADD COLUMN latitude REAL",
        "ALTER TABLE bus_locations ADD COLUMN longitude REAL",
    ]:
        try:
            cursor.execute(alter_sql)
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
    
    # Insert default users if not exists (admin, driver, student)
    default_users = [
        ('admin', 'admin123', 'admin'),
        ('driver', 'driver123', 'driver'),
        ('student', 'student123', 'student'),
    ]
    for username, password, role in default_users:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                          (username, hashlib.sha256(password.encode()).hexdigest(), role))

    # Insert SRK INSTITUTE Route if not exists
    cursor.execute("SELECT COUNT(*) FROM routes WHERE route_name = 'SRK INSTITUTE OF TECHNOLOGY - ROUTE NO-27'")
    if cursor.fetchone()[0] == 0:
        # First, create/update the driver
        cursor.execute("SELECT user_id FROM users WHERE username = 'srk_driver'")
        driver_result = cursor.fetchone()
        if not driver_result:
            cursor.execute("INSERT INTO users (username, password, role, phone_number) VALUES (?, ?, ?, ?)",
                          ('srk_driver', hashlib.sha256('driver123'.encode()).hexdigest(), 'driver', '8099159599'))
            driver_id = cursor.lastrowid
        else:
            driver_id = driver_result['user_id']
            # Update driver's phone number
            cursor.execute("UPDATE users SET phone_number = ? WHERE user_id = ?", ('8099159599', driver_id))

        # Insert the SRK route
        cursor.execute("""
            INSERT INTO routes (route_name, start_point, end_point, stops, driver_id, vehicle_no, driver_name, driver_phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'SRK INSTITUTE OF TECHNOLOGY - ROUTE NO-27',
            'ENIKEPADU-VIJAYAWADA',
            'SRK COLLEGE',
            'HB COLONY,SIVALAYAM,CHURCH,VURMILA NAGAR,RTC WORK SHOP,SITARA CENTER,RAMU COURIER OFFICE,KABELA,MILK PROJECT,SAI RAM THEATRE,CHITTI NAGAR,YARRA KATTA,KEDHARESWARA RAO PETA,RAMAVARAPPADU RING,SRK COLLEGE,VIJAYA COLLEGE',
            driver_id,
            'AP39WB2410',
            'A. MALEESWARA RAO',
            '8099159599'
        ))
        route_id = cursor.lastrowid

        # Insert bus stops with times and amounts
        bus_stops = [
            ('HB COLONY', '07:20', 1500, 1),
            ('SIVALAYAM', '07:25', 1600, 2),
            ('CHURCH', '07:30', 1700, 3),
            ('VURMILA NAGAR', '07:40', 1800, 4),
            ('RTC WORK SHOP', '07:45', 20500, 5),
            ('SITARA CENTER', '07:50', 1900, 6),
            ('RAMU COURIER OFFICE', '07:52', 2000, 7),
            ('KABELA', '07:55', 2100, 8),
            ('MILK PROJECT', '08:00', 2200, 9),
            ('SAI RAM THEATRE', '08:05', 2300, 10),
            ('CHITTI NAGAR', '08:10', 2400, 11),
            ('YARRA KATTA', '08:10', 19500, 12),
            ('KEDHARESWARA RAO PETA', '08:10', 2500, 13),
            ('RAMAVARAPPADU RING', '08:40', 2600, 14),
            ('SRK COLLEGE', '08:45', 18500, 15),
            ('VIJAYA COLLEGE', '08:50', 2700, 16)
        ]

        for stop_name, stop_time, amount, stop_order in bus_stops:
            cursor.execute("""
                INSERT INTO bus_stops (route_id, stop_name, stop_time, amount, stop_order)
                VALUES (?, ?, ?, ?, ?)
            """, (route_id, stop_name, stop_time, amount, stop_order))

    # Insert SRK INSTITUTE OF TECHNOLOGY ENIKEPADU-VIJAYAWADA Route if not exists
    cursor.execute("SELECT COUNT(*) FROM routes WHERE route_name = 'SRK INSTITUTE OF TECHNOLOGY ENIKEPADU-VIJAYAWADA ROUTE NO-11'")
    if cursor.fetchone()[0] == 0:
        # First, create/update the driver
        cursor.execute("SELECT user_id FROM users WHERE username = 'srk_route11_driver'")
        driver_result = cursor.fetchone()
        if not driver_result:
            cursor.execute("INSERT INTO users (username, password, role, phone_number) VALUES (?, ?, ?, ?)",
                          ('srk_route11_driver', hashlib.sha256('driver123'.encode()).hexdigest(), 'driver', '9440549338'))
            driver_id = cursor.lastrowid
        else:
            driver_id = driver_result['user_id']
            # Update driver's phone number
            cursor.execute("UPDATE users SET phone_number = ? WHERE user_id = ?", ('9440549338', driver_id))

        # Insert the SRK ENIKEPADU-VIJAYAWADA route
        cursor.execute("""
            INSERT INTO routes (route_name, start_point, end_point, stops, driver_id, vehicle_no, driver_name, driver_phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'SRK INSTITUTE OF TECHNOLOGY ENIKEPADU-VIJAYAWADA ROUTE NO-11',
            'ENIKEPADU-VIJAYAWADA',
            'VITW',
            'RAYANAPADU GATE,BHAVANIPURAM DHARGA,BHAVANIPURAM SWATHI CEN,BANK CENTER,RTC WORK SHOP ROAD,SITHARA DIATER,SORANGAM/KBN COLLEGE,PANJA CENTER,RAILWAY STATION,ELURU LAKULU,CHALLAPALLI BANGALA,VIJAYA TALKIS,GUNADALA,SRK,VITW',
            driver_id,
            'AP16TB9228',
            'A ANJANEYULU',
            '9440549338'
        ))
        route_id = cursor.lastrowid

        # Insert bus stops with times and amounts
        bus_stops = [
            ('RAYANAPADU GATE', '07:20', 22500, 1),
            ('BHAVANIPURAM DHARGA', '07:45', 22000, 2),
            ('BHAVANIPURAM SWATHI CEN', '07:47', 21500, 3),
            ('BANK CENTER', '07:49', 21000, 4),
            ('RTC WORK SHOP ROAD', '07:50', 20500, 5),
            ('SITHARA DIATER', '08:00', 20000, 6),
            ('SORANGAM/KBN COLLEGE', '08:05', 19500, 7),
            ('PANJA CENTER', '08:10', 19000, 8),
            ('RAILWAY STATION', '08:20', 18500, 9),
            ('ELURU LAKULU', '08:22', 18000, 10),
            ('CHALLAPALLI BANGALA', '08:25', 17500, 11),
            ('VIJAYA TALKIS', '08:30', 18500, 12),
            ('GUNADALA', '08:35', 17000, 13),
            ('SRK', '08:40', 16500, 14),
            ('VITW', '08:45', 16000, 15)
        ]

        for stop_name, stop_time, amount, stop_order in bus_stops:
            cursor.execute("""
                INSERT INTO bus_stops (route_id, stop_name, stop_time, amount, stop_order)
                VALUES (?, ?, ?, ?, ?)
            """, (route_id, stop_name, stop_time, amount, stop_order))

    # Seed 10 sample students if none exist
    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] == 0:
        sample_students = [
            ('Navya Sri', 'CS001', 'Computer Science', '1st Year', '9988776655', 'Father of Navya', '9988776655', 'Address 1', 1, 'parent123'),
            ('Akhila Reddy', 'CS002', 'Computer Science', '2nd Year', '9988776656', 'Father of Akhila', '9988776656', 'Address 2', 1, 'parent123'),
            ('Rohit Kumar', 'ME001', 'Mechanical', '1st Year', '9988776657', 'Father of Rohit', '9988776657', 'Address 3', 2, 'parent123'),
            ('Suresh Babu', 'EC001', 'Electronics', '3rd Year', '9988776658', 'Father of Suresh', '9988776658', 'Address 4', 2, 'parent123'),
            ('Anjali Sharma', 'CS003', 'Computer Science', '2nd Year', '9988776659', 'Father of Anjali', '9988776659', 'Address 5', 3, 'parent123'),
            ('Kiran Teja', 'IT001', 'Information Technology', '1st Year', '9988776660', 'Father of Kiran', '9988776660', 'Address 6', 3, 'parent123'),
            ('Priya Verma', 'EE001', 'Electrical', '4th Year', '9988776661', 'Father of Priya', '9988776661', 'Address 7', 4, 'parent123'),
            ('Rahul Mehta', 'CV001', 'Civil', '2nd Year', '9988776662', 'Father of Rahul', '9988776662', 'Address 8', 4, 'parent123'),
            ('Sneha Patel', 'CS004', 'Computer Science', '3rd Year', '9988776663', 'Father of Sneha', '9988776663', 'Address 9', 5, 'parent123'),
            ('Arjun Rao', 'ME002', 'Mechanical', '2nd Year', '9988776664', 'Father of Arjun', '9988776664', 'Address 10', 5, 'parent123'),
        ]
        for name, roll, dept, year, phone, fname, fphone, addr, route_id, pwd in sample_students:
            uname = 's' + roll.lower().replace(' ', '_')
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (uname, hashlib.sha256('student123'.encode()).hexdigest(), 'student'))
            uid = cursor.lastrowid
            cursor.execute("""
                INSERT INTO students (user_id, name, roll_number, department, year, phone_number, father_name, father_phone, address, route_id, parent_password)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (uid, name, roll, dept, year, phone, fname, fphone, addr, route_id, pwd))
    
    conn.commit()
    conn.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

class FaceRecognitionSystem:
    def __init__(self):
        self.known_faces = {}
        self.load_known_faces()
    
    def enhance_image(self, image):
        """Enhance image brightness and contrast"""
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        enhanced = cv2.convertScaleAbs(enhanced, alpha=1.2, beta=20)
        return enhanced
    
    def capture_from_webcam(self, save_path=None):
        """Capture image from webcam without display"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            return None, "Cannot access camera. Make sure camera is connected and not in use."
        
        try:
            cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.6)
            cap.set(cv2.CAP_PROP_CONTRAST, 0.7)
            cap.set(cv2.CAP_PROP_SATURATION, 0.8)
            
            for _ in range(5):
                ret, frame = cap.read()
                if not ret:
                    continue
            
            ret, frame = cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                enhanced_frame = self.enhance_image(frame)
                
                if save_path:
                    cv2.imwrite(save_path, enhanced_frame)
                
                cap.release()
                return enhanced_frame, None
            else:
                cap.release()
                return None, "Failed to capture image from camera"
        except Exception as e:
            cap.release()
            return None, f"Camera error: {str(e)}"
    
    def detect_faces(self, image):
        """Detect faces in image"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        return faces
    
    def extract_face_encoding(self, image_path):
        """Extract face features from image using histogram comparison"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) == 0:
                return None
            
            (x, y, w, h) = faces[0]
            face_region = gray[y:y+h, x:x+w]
            face_resized = cv2.resize(face_region, (100, 100))
            
            hist = cv2.calcHist([face_resized], [0], None, [256], [0, 256])
            cv2.normalize(hist, hist)
            
            return hist.flatten()
        except Exception as e:
            print(f"Error extracting encoding: {e}")
            return None
    
    def save_known_face(self, student_id, image_path):
        """Save known face with student ID"""
        encoding = self.extract_face_encoding(image_path)
        if encoding is not None:
            self.known_faces[str(student_id)] = encoding.tolist()
            self.save_known_faces()
            return True
        return False
    
    def recognize_student(self, image_path, tolerance=0.6):
        """Recognize student from image using histogram correlation"""
        print(f"DEBUG: Starting face recognition for {image_path}")
        
        unknown_encoding = self.extract_face_encoding(image_path)
        if unknown_encoding is None:
            print("DEBUG: No face detected in image")
            return None, "No face detected"
        
        print(f"DEBUG: Face encoding extracted, shape: {unknown_encoding.shape}")
        
        if not self.known_faces:
            print("DEBUG: No known faces in database")
            return None, "No registered students in database"
        
        print(f"DEBUG: Found {len(self.known_faces)} known faces: {list(self.known_faces.keys())}")
        
        best_match = None
        best_score = -1
        
        for key, encoding in self.known_faces.items():
            encoding = np.array(encoding)
            
            try:
                unknown_encoding_reshaped = unknown_encoding.reshape(256, 1).astype(np.float32)
                encoding_reshaped = encoding.reshape(256, 1).astype(np.float32)
                
                correlation = cv2.compareHist(encoding_reshaped, unknown_encoding_reshaped, cv2.HISTCMP_CORREL)
                
                correlation_score = float(correlation)
                print(f"DEBUG: Comparing with '{key}': score = {correlation_score:.4f}")
                
                if correlation_score > best_score:
                    best_score = correlation_score
                    best_match = key
                    
            except Exception as e:
                print(f"DEBUG: Error comparing with '{key}': {e}")
                continue
        
        print(f"DEBUG: Best match: '{best_match}' with score: {best_score:.4f}")
        print(f"DEBUG: Tolerance: {tolerance}")
        
        if best_score >= tolerance:
            # Check if the match is a student ID or name
            if best_match.isdigit():
                # It's a student ID
                print(f"DEBUG: Match is student ID: {best_match}")
                return best_match, f"Student recognized (similarity: {best_score:.4f})"
            else:
                # It's a name, try to find the student by name
                print(f"DEBUG: Match is name: '{best_match}', looking up student...")
                student = self.get_student_by_name(best_match)
                if student:
                    print(f"DEBUG: Student found: ID={student['student_id']}, Name={student['name']}")
                    return str(student['student_id']), f"Student recognized (similarity: {best_score:.4f})"
                else:
                    print(f"DEBUG: Student '{best_match}' not found in database")
                    return None, f"Face recognized but student '{best_match}' not found in database"
        else:
            print(f"DEBUG: Score {best_score:.4f} below tolerance {tolerance}")
            return None, f"Unknown student (best similarity: {best_score:.4f})"
    
    def get_student_by_name(self, name):
        """Get student by name from database"""
        try:
            conn = get_db_connection()
            student = conn.execute('SELECT * FROM students WHERE name = ?', (name,)).fetchone()
            conn.close()
            return student
        except Exception as e:
            print(f"Error finding student by name: {e}")
            return None
    
    def load_known_faces(self):
        """Load known faces from file"""
        try:
            if os.path.exists('known_faces.json'):
                with open('known_faces.json', 'r') as f:
                    self.known_faces = json.load(f)
        except Exception as e:
            print(f"Error loading known faces: {e}")
            self.known_faces = {}
    
    def save_known_faces(self):
        """Save known faces to file"""
        try:
            with open('known_faces.json', 'w') as f:
                json.dump(self.known_faces, f)
        except Exception as e:
            print(f"Error saving known faces: {e}")

# Initialize face recognition system
face_system = FaceRecognitionSystem()

# Database helper functions

def get_db_connection():
    # Use path relative to this file so DB is always in the app folder
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_student_by_user_id(user_id):
    conn = get_db_connection()
    student = conn.execute('SELECT * FROM students WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    return student

def get_student_by_id(student_id):
    conn = get_db_connection()
    student = conn.execute('SELECT * FROM students WHERE student_id = ?', (student_id,)).fetchone()
    conn.close()
    return student

def get_bus_pass_by_student_id(student_id):
    conn = get_db_connection()
    pass_info = conn.execute('SELECT * FROM bus_passes WHERE student_id = ? ORDER BY created_at DESC LIMIT 1', 
                           (student_id,)).fetchone()
    conn.close()
    return pass_info

# Routes
@app.route('/')
def index():
    return render_template('transit_index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        conn = get_db_connection()
        # Debug: print database path and query info
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
        print(f"DEBUG LOGIN: DB path = {db_path}")
        print(f"DEBUG LOGIN: username = '{username}', password = '{password}'")
        
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        # Debug: check all users
        all_users = conn.execute('SELECT username, password FROM users').fetchall()
        print(f"DEBUG LOGIN: All users in DB = {[(u[0], u[1]) for u in all_users]}")
        print(f"DEBUG LOGIN: Found user = {user}")
        
        conn.close()
        
        if user:
            print(f"DEBUG LOGIN: User data structure = {user}")
            print(f"DEBUG LOGIN: User columns - user_id={user[0]}, username={user[1]}, password={user[2]}, role={user[3]}")
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            print(f"DEBUG LOGIN: Input password hashed = {hashed_password}")
            print(f"DEBUG LOGIN: Stored password = {user[2]}")
            print(f"DEBUG LOGIN: Passwords match = {hashed_password == user[2]}")
            
            if hashed_password == user[2]:
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[3]
                if user[3] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user[3] == 'student':
                    return redirect(url_for('student_dashboard'))
                else:
                    return redirect(url_for('driver_dashboard'))
        else:
            print("DEBUG LOGIN: User not found in database")
        flash('Invalid username or password')
    
    return render_template('login.html')


@app.route('/parent_login', methods=['GET', 'POST'])
def parent_login():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('password', '')
        conn = get_db_connection()
        student = conn.execute(
            'SELECT s.student_id, s.name, s.roll_number, s.route_id, s.parent_password FROM students s WHERE s.student_id = ?',
            (student_id,)
        ).fetchone()
        conn.close()
        if student and (student[4] or '').strip() == password.strip():
            session['user_id'] = None
            session['role'] = 'parent'
            session['parent_student_id'] = student['student_id']
            session['username'] = f"Parent of {student['name']}"
            return redirect(url_for('parent_dashboard'))
        flash('Invalid student selection or password.')
    conn = get_db_connection()
    students = conn.execute('SELECT student_id, name, roll_number FROM students ORDER BY name').fetchall()
    conn.close()
    return render_template('parent_login.html', students=students)


@app.route('/parent/dashboard')
@login_required
def parent_dashboard():
    if session.get('role') != 'parent':
        return redirect(url_for('index'))
    student_id = session.get('parent_student_id')
    if not student_id:
        return redirect(url_for('parent_login'))
    conn = get_db_connection()
    student = conn.execute('SELECT s.student_id, s.name, s.roll_number, s.route_id FROM students s WHERE s.student_id = ?', (student_id,)).fetchone()
    
    # Get driver contact details via student's route
    driver_info = None
    if student and student['route_id']:
        driver_info = conn.execute('''
            SELECT u.username as driver_name, u.phone_number as driver_phone, r.route_name
            FROM routes r
            JOIN users u ON r.driver_id = u.user_id
            WHERE r.route_id = ?
        ''', (student['route_id'],)).fetchone()
    
    messages = conn.execute('''
        SELECT m.*, u.username as driver_username
        FROM driver_parent_messages m
        LEFT JOIN users u ON m.driver_id = u.user_id
        WHERE m.student_id = ?
        ORDER BY m.created_at DESC
        LIMIT 50
    ''', (student_id,)).fetchall()
    conn.close()
    return render_template('parent_dashboard.html', student=student, messages=messages, driver_info=driver_info)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data with defaults to avoid KeyError
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        name = (request.form.get('name') or '').strip()
        roll_number = (request.form.get('roll_number') or '').strip()
        department = request.form.get('department') or ''
        year = request.form.get('year') or ''
        phone_number = (request.form.get('phone_number') or '').strip()
        father_name = (request.form.get('father_name') or '').strip()
        father_phone = (request.form.get('father_phone') or '').strip()
        address = (request.form.get('address') or '').strip()
        parent_password = (request.form.get('parent_password') or '').strip() or 'parent123'

        if not username or not password:
            flash('Username and password are required.')
            return render_template('student_register.html')
        if not name or not roll_number:
            flash('Full name and roll number are required.')
            return render_template('student_register.html')

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                          (username, hashed_password, 'student'))
            user_id = cursor.lastrowid

            cursor.execute('''
                INSERT INTO students (user_id, name, roll_number, department, year, phone_number,
                                    father_name, father_phone, address, parent_password)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, roll_number, department, year, phone_number,
                  father_name, father_phone, address, parent_password))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.rollback()
            flash('Username or roll number already exists. Please choose different ones.')
        except Exception as e:
            conn.rollback()
            flash(f'Registration failed: {str(e)}')
        finally:
            conn.close()

    return render_template('student_register.html')

@app.route('/driver_register', methods=['GET', 'POST'])
def driver_register():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        name = (request.form.get('name') or '').strip()
        phone_number = (request.form.get('phone_number') or '').strip()
        license_number = (request.form.get('license_number') or '').strip()
        address = (request.form.get('address') or '').strip()

        if not username or not password:
            flash('Username and password are required.')
            return render_template('driver_register.html')
        if not name or not phone_number:
            flash('Full name and phone number are required.')
            return render_template('driver_register.html')

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute('INSERT INTO users (username, password, role, phone_number) VALUES (?, ?, ?, ?)',
                          (username, hashed_password, 'driver', phone_number))
            conn.commit()
            flash('Driver registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.rollback()
            flash('Username already exists. Please choose a different one.')
        except Exception as e:
            conn.rollback()
            flash(f'Registration failed: {str(e)}')
        finally:
            conn.close()

    return render_template('driver_register.html')

@app.route('/student/attendance_history')
@login_required
def student_attendance_history():
    if session['role'] != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    student = get_student_by_user_id(session['user_id'])
    if not student:
        return jsonify({'success': False, 'error': 'Student not found'})
    
    conn = get_db_connection()
    attendance_records = conn.execute('''
        SELECT a.date, a.boarding_time, a.verification_type, a.status, b.pass_number, b.route
        FROM attendance a
        JOIN bus_passes b ON a.pass_id = b.pass_id
        WHERE a.student_id = ?
        ORDER BY a.date DESC, a.boarding_time DESC
        LIMIT 30
    ''', (student['student_id'],)).fetchall()
    conn.close()
    
    attendance_list = []
    for record in attendance_records:
        attendance_list.append({
            'date': record['date'],
            'boarding_time': record['boarding_time'],
            'verification_type': record['verification_type'],
            'status': record['status'],
            'pass_number': record['pass_number'],
            'route': record['route']
        })
    
    return jsonify({
        'success': True,
        'attendance': attendance_list
    })

@app.route('/driver/update_location', methods=['GET', 'POST'])
@login_required
def driver_update_location():
    if session['role'] != 'driver':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        current_location = request.form.get('current_location')
        destination = request.form.get('destination')
        distance_left = request.form.get('distance_left')
        message = request.form.get('message')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert new location update (text fields; lat/lng via track_location)
        cursor.execute('''
            INSERT INTO bus_locations (driver_id, current_location, destination, distance_left, message)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], current_location or '', destination or '', distance_left or '', message or ''))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Location updated successfully'})
    
    return render_template('driver_update_location.html')

@app.route('/get_latest_location')
def get_latest_location():
    """API endpoint to get latest driver location for students/parents (includes lat/lng for map)"""
    conn = get_db_connection()
    latest_location = conn.execute('''
        SELECT current_location, destination, distance_left, message, timestamp, latitude, longitude
        FROM bus_locations
        ORDER BY timestamp DESC
        LIMIT 1
    ''').fetchone()
    conn.close()
    
    if latest_location:
        return jsonify({
            'success': True,
            'current_location': latest_location['current_location'] or '',
            'destination': latest_location['destination'] or '',
            'distance_left': latest_location['distance_left'] or '',
            'message': latest_location['message'] or '',
            'timestamp': latest_location['timestamp'],
            'latitude': latest_location['latitude'] if latest_location['latitude'] is not None else None,
            'longitude': latest_location['longitude'] if latest_location['longitude'] is not None else None
        })
    else:
        return jsonify({
            'success': False,
            'message': 'No location updates available'
        })


@app.route('/driver/track_location', methods=['POST'])
@login_required
def driver_track_location():
    """Driver shares exact GPS location (for Track button); students/parents see it on map"""
    if session.get('role') != 'driver':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    data = request.get_json() or request.form
    lat = data.get('latitude')
    lng = data.get('longitude')
    if lat is None or lng is None:
        return jsonify({'success': False, 'error': 'latitude and longitude required'})
    try:
        lat, lng = float(lat), float(lng)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'Invalid coordinates'})
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bus_locations (driver_id, current_location, destination, distance_left, message, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (session['user_id'], 'Live location', '', '', 'Tracking', lat, lng))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Location shared'})


@app.route('/parent/send_message', methods=['POST'])
@login_required
def parent_send_message():
    if session.get('role') != 'parent':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    student_id = session.get('parent_student_id')
    j = request.get_json(silent=True) or {}
    msg = request.form.get('message') or j.get('message') or ''
    if not msg.strip():
        return jsonify({'success': False, 'error': 'Message required'})
    conn = get_db_connection()
    student = conn.execute('SELECT route_id FROM students WHERE student_id = ?', (student_id,)).fetchone()
    driver_id = None
    if student and student['route_id']:
        dr = conn.execute('SELECT driver_id FROM routes WHERE route_id = ?', (student['route_id'],)).fetchone()
        if dr and dr['driver_id']:
            driver_id = dr['driver_id']
    
    if driver_id is None:
        conn.close()
        return jsonify({'success': False, 'error': 'No driver assigned to your student route. Please contact the administrator.'})
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO driver_parent_messages (driver_id, student_id, sender_type, message)
        VALUES (?, ?, ?, ?)
    ''', (driver_id, student_id, 'parent', msg.strip()))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Message sent successfully'})


@app.route('/driver/send_message_to_parent', methods=['POST'])
@login_required
def driver_send_message_to_parent():
    if session.get('role') != 'driver':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    student_id = request.form.get('student_id') or (request.get_json(silent=True) or {}).get('student_id')
    msg = request.form.get('message') or (request.get_json(silent=True) or {}).get('message', '')
    if not student_id or not str(msg).strip():
        return jsonify({'success': False, 'error': 'student_id and message required'})
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO driver_parent_messages (driver_id, student_id, sender_type, message)
        VALUES (?, ?, ?, ?)
    ''', (session['user_id'], student_id, 'driver', str(msg).strip()))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Message sent'})

@app.route('/driver/send_parent_notification', methods=['GET', 'POST'])
@login_required
def driver_send_parent_notification():
    if session['role'] != 'driver':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        message = request.form.get('custom_message')
        
        if not student_id or not message.strip():
            return jsonify({'success': False, 'message': 'Student and message are required'})
        
        # Send normal message to parent
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO driver_parent_messages (driver_id, student_id, sender_type, message)
            VALUES (?, ?, ?, ?)
        ''', (session['user_id'], student_id, 'driver', message.strip()))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Message sent to parent successfully'
        })
    
    # Get students with approved passes for dropdown
    conn = get_db_connection()
    students = conn.execute('''
        SELECT s.student_id, s.name, s.father_phone, b.pass_number, b.route
        FROM students s
        JOIN bus_passes b ON s.student_id = b.student_id
        WHERE b.status = 'approved'
    ''').fetchall()
    conn.close()
    
    return render_template('driver_send_notification.html', students=students)

@app.route('/driver/messages')
@login_required
def driver_messages():
    if session['role'] != 'driver':
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    
    # Get all messages for this driver with student details
    messages = conn.execute('''
        SELECT m.*, s.name as student_name, s.roll_number, r.route_name,
               datetime(m.created_at) as formatted_time
        FROM driver_parent_messages m
        JOIN students s ON m.student_id = s.student_id
        LEFT JOIN routes r ON s.route_id = r.route_id
        WHERE m.driver_id = ?
        ORDER BY m.created_at DESC
        LIMIT 100
    ''', (session['user_id'],)).fetchall()
    
    # Get unique students for filtering
    students = conn.execute('''
        SELECT DISTINCT s.student_id, s.name, s.roll_number, r.route_name
        FROM students s
        JOIN driver_parent_messages m ON s.student_id = m.student_id
        LEFT JOIN routes r ON s.route_id = r.route_id
        WHERE m.driver_id = ?
        ORDER BY s.name
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return render_template('driver_messages.html', messages=messages, students=students)

@app.route('/test_email_config')
def test_email_config():
    """Test email configuration and show current settings"""
    config_info = {
        'smtp_server': EMAIL_CONFIG['smtp_server'],
        'smtp_port': EMAIL_CONFIG['smtp_port'],
        'sender_email': EMAIL_CONFIG['sender_email'],
        'sender_password_set': bool(EMAIL_CONFIG['sender_password'] and EMAIL_CONFIG['sender_password'] != 'APP_PASSWORD'),
        'sender_name': EMAIL_CONFIG['sender_name']
    }
    
    return jsonify({
        'success': True,
        'config': config_info,
        'message': 'Check if sender_email is your actual email and sender_password_set is True'
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if session['role'] != 'student':
        return redirect(url_for('index'))
    
    student = get_student_by_user_id(session['user_id'])
    bus_pass = get_bus_pass_by_student_id(student['student_id']) if student else None
    
    # Get driver contact details
    driver_info = None
    if student and student['route_id']:
        conn = get_db_connection()
        driver_info = conn.execute('''
            SELECT u.username as driver_name, u.phone_number as driver_phone, r.route_name
            FROM routes r
            JOIN users u ON r.driver_id = u.user_id
            WHERE r.route_id = ?
        ''', (student['route_id'],)).fetchone()
        conn.close()
    
    return render_template('student_dashboard.html', student=student, bus_pass=bus_pass, driver_info=driver_info)

@app.route('/apply_pass')
@login_required
def apply_pass():
    if session['role'] != 'student':
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    # Get routes with their assigned drivers
    routes = conn.execute('''
        SELECT r.*, u.username as driver_name, u.phone_number as driver_phone
        FROM routes r
        LEFT JOIN users u ON r.driver_id = u.user_id
        ORDER BY r.route_name
    ''').fetchall()
    conn.close()
    
    return render_template('apply_pass.html', routes=routes)

@app.route('/capture_photo', methods=['POST'])
@login_required
def capture_photo():
    """Capture photo for bus pass application"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_path = os.path.join('static/temp', f'pass_photo_{timestamp}.jpg')
        
        frame, error = face_system.capture_from_webcam(temp_path)
        if error:
            return jsonify({'success': False, 'error': error})
        
        # Detect faces
        faces = face_system.detect_faces(frame)
        
        if len(faces) == 0:
            return jsonify({'success': False, 'error': 'No face detected'})
        
        # Draw rectangles around faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Save image with face detection
        result_path = os.path.join('static/temp', f'pass_result_{timestamp}.jpg')
        cv2.imwrite(result_path, frame)
        
        # Convert to base64 for display
        with open(result_path, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode()
        
        # Clean up temp files
        if os.path.exists(result_path):
            os.remove(result_path)
        
        return jsonify({
            'success': True,
            'image': f'data:image/jpeg;base64,{img_data}',
            'temp_path': temp_path,
            'faces_detected': len(faces)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_route_stops', methods=['POST'])
def get_route_stops():
    """Get stops for a selected route"""
    route_name = request.form.get('route_name')
    if not route_name:
        return jsonify({'success': False, 'error': 'Route name required'})
    
    conn = get_db_connection()
    route = conn.execute('SELECT route_id FROM routes WHERE route_name = ?', (route_name,)).fetchone()
    
    if not route:
        conn.close()
        return jsonify({'success': False, 'error': 'Route not found'})
    
    stops = conn.execute('''
        SELECT stop_name, stop_time, amount 
        FROM bus_stops 
        WHERE route_id = ? 
        ORDER BY stop_order
    ''', (route['route_id'],)).fetchall()
    
    conn.close()
    return jsonify({'success': True, 'stops': [dict(stop) for stop in stops]})

@app.route('/get_route_drivers', methods=['POST'])
def get_route_drivers():
    """Get available drivers for a selected route"""
    route_name = request.form.get('route_name')
    if not route_name:
        return jsonify({'success': False, 'error': 'Route name required'})
    
    conn = get_db_connection()
    route = conn.execute('SELECT route_id, driver_id FROM routes WHERE route_name = ?', (route_name,)).fetchone()
    
    if not route:
        conn.close()
        return jsonify({'success': False, 'error': 'Route not found'})
    
    # Get the assigned driver for this route
    if route['driver_id']:
        driver = conn.execute('''
            SELECT user_id, username, phone_number 
            FROM users 
            WHERE user_id = ? AND role = 'driver'
        ''', (route['driver_id'],)).fetchone()
        
        if driver:
            conn.close()
            return jsonify({
                'success': True, 
                'drivers': [{
                    'user_id': driver['user_id'],
                    'username': driver['username'],
                    'phone_number': driver['phone_number']
                }]
            })
    
    # If no specific driver assigned, get all available drivers
    all_drivers = conn.execute('''
        SELECT user_id, username, phone_number 
        FROM users 
        WHERE role = 'driver'
        ORDER BY username
    ''').fetchall()
    
    conn.close()
    return jsonify({
        'success': True, 
        'drivers': [dict(driver) for driver in all_drivers]
    })

@app.route('/submit_pass_application', methods=['POST'])
@login_required
def submit_pass_application():
    """Submit bus pass application"""
    try:
        student = get_student_by_user_id(session['user_id'])
        if not student:
            return jsonify({'success': False, 'error': 'Student not found'})
        
        # Get form data
        route = request.form.get('route')
        boarding_stop = request.form.get('boarding_stop')
        pass_amount = request.form.get('pass_amount')
        duration_from = request.form.get('duration_from')
        duration_to = request.form.get('duration_to')
        temp_path = request.form.get('temp_path')
        
        if not all([route, boarding_stop, pass_amount, duration_from, duration_to, temp_path]):
            return jsonify({'success': False, 'error': 'All fields are required'})
        
        if not os.path.exists(temp_path):
            return jsonify({'success': False, 'error': 'No photo captured'})
        
        # Save photo permanently
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        photo_filename = f'student_{student["student_id"]}_{timestamp}.jpg'
        photo_path = os.path.join(app.config['PASS_PHOTOS_FOLDER'], photo_filename)
        
        import shutil
        shutil.copy2(temp_path, photo_path)
        
        # Save bus pass application with boarding stop and amount
        conn = get_db_connection()
        
        # Generate unique pass number using sequential numbering
        date_prefix = datetime.now().strftime('%Y%m%d')
        
        # Get the highest sequence number for today
        max_seq_query = '''
            SELECT MAX(CAST(SUBSTR(pass_number, 9) AS INTEGER)) 
            FROM bus_passes 
            WHERE pass_number LIKE ?
        '''
        max_seq = conn.execute(max_seq_query, (f'PASS{date_prefix}%',)).fetchone()[0]
        
        if max_seq is None:
            sequence = 1
        else:
            sequence = max_seq + 1
        
        pass_number = f"PASS{date_prefix}{sequence:04d}"
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bus_passes (student_id, pass_number, issue_date, expiry_date, route, boarding_stop, pass_amount, photo_path, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (student['student_id'], pass_number, duration_from, duration_to, route, boarding_stop, int(pass_amount), photo_path, 'pending'))
        pass_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Save face for recognition
        face_system.save_known_face(str(student['student_id']), photo_path)
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'message': 'Bus pass application submitted successfully!',
            'pass_number': pass_number
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/driver/dashboard')
@login_required
def driver_dashboard():
    if session['role'] != 'driver':
        return redirect(url_for('index'))
    conn = get_db_connection()
    my_route = conn.execute('SELECT * FROM routes WHERE driver_id = ?', (session['user_id'],)).fetchone()
    route_id = my_route['route_id'] if my_route else None
    total_students = conn.execute('SELECT COUNT(*) as count FROM students').fetchone()['count']
    if route_id:
        # Count students who have applied for bus passes on this driver's route
        route_students = conn.execute('''
            SELECT COUNT(DISTINCT s.student_id) as count 
            FROM students s
            JOIN bus_passes b ON s.student_id = b.student_id
            WHERE b.route = (SELECT route_name FROM routes WHERE route_id = ?)
        ''', (route_id,)).fetchone()['count']
        
        # Get detailed student information for this route
        route_student_details = conn.execute('''
            SELECT DISTINCT s.student_id, s.name, s.roll_number, s.department, s.year, s.phone_number,
                   b.pass_number, b.status as pass_status, b.boarding_stop
            FROM students s
            JOIN bus_passes b ON s.student_id = b.student_id
            WHERE b.route = (SELECT route_name FROM routes WHERE route_id = ?)
            ORDER BY s.name
        ''', (route_id,)).fetchall()
        
        today_attendance = conn.execute('''
            SELECT COUNT(DISTINCT a.student_id) as count FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE s.route_id = ? AND a.date = ?
        ''', (route_id, datetime.now().date())).fetchone()['count']
    else:
        route_students = 0
        route_student_details = []
        today_attendance = conn.execute('SELECT COUNT(*) as count FROM attendance WHERE date = ?', (datetime.now().date(),)).fetchone()['count']
    active_passes = conn.execute('SELECT COUNT(*) as count FROM bus_passes WHERE status = "approved"').fetchone()['count']
    
    # Get recent messages from parents
    recent_messages = conn.execute('''
        SELECT m.*, s.name as student_name, s.roll_number,
               datetime(m.created_at) as formatted_time
        FROM driver_parent_messages m
        JOIN students s ON m.student_id = s.student_id
        WHERE m.driver_id = ? AND m.sender_type = 'parent'
        ORDER BY m.created_at DESC
        LIMIT 5
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    return render_template('driver_dashboard.html',
                         total_students=total_students,
                         active_passes=active_passes,
                         today_attendance=today_attendance,
                         my_route=my_route,
                         route_students=route_students,
                         route_student_details=route_student_details,
                         recent_messages=recent_messages)

@app.route('/driver/attendance')
@login_required
def driver_attendance():
    if session['role'] != 'driver':
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    
    # Get driver's route
    my_route = conn.execute('SELECT * FROM routes WHERE driver_id = ?', (session['user_id'],)).fetchone()
    
    if my_route:
        # Get today's attendance for this driver's route
        today = datetime.now().date()
        attendance_records = conn.execute('''
            SELECT a.student_id, a.date, a.boarding_time, a.drop_time, a.verification_type, a.status,
                   s.name, s.roll_number, s.department, s.year, b.pass_number
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            LEFT JOIN bus_passes b ON a.student_id = b.student_id
            WHERE s.route_id = ? AND a.date = ?
            ORDER BY a.boarding_time DESC
        ''', (my_route['route_id'], today)).fetchall()
        
        # Get attendance summary for the last 7 days
        attendance_summary = conn.execute('''
            SELECT a.date, COUNT(DISTINCT a.student_id) as present_count,
                   (SELECT COUNT(*) FROM students s2 WHERE s2.route_id = ?) as total_students
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE s.route_id = ? AND a.date >= date('now', '-7 days')
            GROUP BY a.date
            ORDER BY a.date DESC
        ''', (my_route['route_id'], my_route['route_id'])).fetchall()
        
        # Get route students list
        route_students = conn.execute('''
            SELECT s.student_id, s.name, s.roll_number, s.phone_number,
                   b.pass_number, b.status as pass_status
            FROM students s
            LEFT JOIN bus_passes b ON s.student_id = b.student_id
            WHERE s.route_id = ?
            ORDER BY s.name
        ''', (my_route['route_id'],)).fetchall()
    else:
        attendance_records = []
        attendance_summary = []
        route_students = []
    
    conn.close()
    
    return render_template('driver_attendance.html', 
                         attendance_records=attendance_records,
                         attendance_summary=attendance_summary,
                         route_students=route_students,
                         my_route=my_route)


@app.route('/driver/attendance_records')
@login_required
def driver_attendance_records():
    if session['role'] != 'driver':
        return redirect(url_for('index'))
    conn = get_db_connection()
    my_route = conn.execute('SELECT route_id, route_name FROM routes WHERE driver_id = ?', (session['user_id'],)).fetchone()
    route_id = my_route['route_id'] if my_route else None
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    export = request.args.get('export')
    q = '''
        SELECT a.date, a.boarding_time, a.drop_time, a.verification_type, a.status,
               s.name, s.roll_number, s.department, s.year, 
               COALESCE(b.pass_number, 'No Pass') as pass_number
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        LEFT JOIN bus_passes b ON a.pass_id = b.pass_id
        WHERE 1=1
    '''
    params = []
    if route_id:
        q += ' AND s.route_id = ?'
        params.append(route_id)
    if date_from:
        q += ' AND a.date >= ?'
        params.append(date_from)
    if date_to:
        q += ' AND a.date <= ?'
        params.append(date_to)
    q += ' ORDER BY a.date DESC, a.boarding_time DESC LIMIT 200'
    records = conn.execute(q, params).fetchall()
    conn.close()
    if export == 'excel':
        try:
            from openpyxl import Workbook
            from io import BytesIO
            wb = Workbook()
            ws = wb.active
            ws.title = 'Attendance'
            ws.append(['Date', 'Boarding Time', 'Student Name', 'Roll Number', 'Department', 'Pass Number'])
            for r in records:
                ws.append([str(r['date']), str(r['boarding_time'] or ''), str(r['name']), str(r['roll_number'] or ''), str(r['department'] or ''), str(r['pass_number'] or '')])
            buf = BytesIO()
            wb.save(buf)
            buf.seek(0)
            from flask import send_file
            return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='driver_attendance.xlsx')
        except Exception:
            pass
    return render_template('driver_attendance_records.html', records=records, my_route=my_route)

def send_attendance_message_to_parent(student_id, student_name, attendance_time, route_name, message_type='boarding'):
    """Send automated attendance message to parent"""
    try:
        conn = get_db_connection()
        
        # Get student details including parent phone
        student = conn.execute('''
            SELECT father_phone, father_name, route_id 
            FROM students 
            WHERE student_id = ?
        ''', (student_id,)).fetchone()
        
        if not student or not student['father_phone']:
            print(f"No parent phone found for student {student_id}")
            conn.close()
            return False
        
        # Get driver ID for this route
        route = conn.execute('''
            SELECT driver_id FROM routes WHERE route_id = ?
        ''', (student['route_id'],)).fetchone()
        
        if not route or not route['driver_id']:
            print(f"No driver assigned to route {student['route_id']}")
            conn.close()
            return False
        
        # Create attendance message based on type
        if message_type == 'boarding':
            message = f"""🚌 Attendance Alert!
            
Student: {student_name}
Time: {attendance_time}
Route: {route_name}
Status: Boarded Successfully

Your child has boarded the bus safely. Thank you!
- SRK Transport System"""
        elif message_type == 'drop_off':
            message = f"""🏠 Drop-off Alert!
            
Student: {student_name}
Time: {attendance_time}
Route: {route_name}
Status: Dropped Safely

Your child has been dropped safely. Thank you!
- SRK Transport System"""
        else:
            message = f"""📝 Attendance Update
            
Student: {student_name}
Time: {attendance_time}
Route: {route_name}

- SRK Transport System"""
        
        # Store message in database
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO driver_parent_messages (driver_id, student_id, sender_type, message)
            VALUES (?, ?, ?, ?)
        ''', (route['driver_id'], student_id, 'system', message))
        
        conn.commit()
        conn.close()
        
        # Here you can integrate actual SMS service like Twilio, etc.
        # For now, messages are stored in database
        print(f"Attendance message ({message_type}) sent to parent of {student_name}")
        print(f"Parent phone: {student['father_phone']}")
        print(f"Message: {message[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"Error sending attendance message: {str(e)}")
        return False

def send_sms_notification(phone_number, message):
    """Send SMS notification (placeholder for actual SMS integration)"""
    # This is where you would integrate SMS service like:
    # - Twilio
    # - AWS SNS
    # - Local SMS gateway
    # - WhatsApp Business API
    
    # For demonstration, we'll just log the message
    print(f"SMS would be sent to {phone_number}: {message}")
    
    # Example Twilio integration (commented out):
    # from twilio.rest import Client
    # account_sid = 'your_account_sid'
    # auth_token = 'your_auth_token'
    # client = Client(account_sid, auth_token)
    # message = client.messages.create(
    #     body=message,
    #     from_='+1234567890',  # Your Twilio number
    #     to=phone_number
    # )
    # return message.sid
    
    return True

@app.route('/capture_attendance', methods=['POST'])
@login_required
def capture_attendance():
    """Capture face for attendance marking"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_path = os.path.join('static/temp', f'attendance_{timestamp}.jpg')
        
        frame, error = face_system.capture_from_webcam(temp_path)
        if error:
            return jsonify({'success': False, 'error': error})
        
        # Detect faces
        faces = face_system.detect_faces(frame)
        
        if len(faces) == 0:
            return jsonify({'success': False, 'error': 'No face detected'})
        
        # Draw rectangles around faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Save image with face detection
        result_path = os.path.join('static/temp', f'attendance_result_{timestamp}.jpg')
        cv2.imwrite(result_path, frame)
        
        # Try to recognize student
        recognized_student_id, message = face_system.recognize_student(temp_path)
        
        student_info = None
        attendance_marked = False
        
        if recognized_student_id:
            # Get student information
            student = get_student_by_id(recognized_student_id)
            if student:
                # Check if student has valid bus pass
                bus_pass = get_bus_pass_by_student_id(recognized_student_id)
                if bus_pass and bus_pass['status'] == 'approved':
                    # Mark attendance
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    # Check if already marked today
                    today = datetime.now().date()
                    existing = conn.execute('''
                        SELECT * FROM attendance 
                        WHERE student_id = ? AND date = ? AND boarding_time IS NOT NULL
                    ''', (recognized_student_id, today)).fetchone()
                    
                    if not existing:
                        attendance_time = datetime.now().strftime('%H:%M:%S')
                        cursor.execute('''
                            INSERT INTO attendance (student_id, pass_id, date, boarding_time, verification_type, status)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (recognized_student_id, bus_pass['pass_id'], today, 
                              attendance_time, 'face', 'present'))
                        conn.commit()
                        attendance_marked = True
                        
                        # Send attendance message to parent
                        send_attendance_message_to_parent(
                            recognized_student_id, 
                            student['name'], 
                            attendance_time, 
                            bus_pass['route']
                        )
                    
                    conn.close()
                    
                    student_info = {
                        'name': student['name'],
                        'roll_number': student['roll_number'],
                        'department': student['department'],
                        'pass_number': bus_pass['pass_number'],
                        'route': bus_pass['route']
                    }
        
        # Convert to base64 for display
        with open(result_path, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode()
        
        # Clean up temp files
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(result_path):
            os.remove(result_path)
        
        return jsonify({
            'success': True,
            'image': f'data:image/jpeg;base64,{img_data}',
            'student_info': student_info,
            'attendance_marked': attendance_marked,
            'message': message,
            'faces_detected': len(faces)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/mark_drop_off_attendance', methods=['POST'])
@login_required
def mark_drop_off_attendance():
    """Mark drop-off attendance for a student"""
    if session.get('role') != 'driver':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        student_id = request.form.get('student_id') or (request.get_json(silent=True) or {}).get('student_id')
        
        if not student_id:
            return jsonify({'success': False, 'error': 'Student ID required'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get today's attendance record
        today = datetime.now().date()
        existing = cursor.execute('''
            SELECT * FROM attendance 
            WHERE student_id = ? AND date = ?
        ''', (student_id, today)).fetchone()
        
        if existing:
            # Update drop time
            drop_time = datetime.now().strftime('%H:%M:%S')
            cursor.execute('''
                UPDATE attendance 
                SET drop_time = ?, status = 'completed'
                WHERE student_id = ? AND date = ?
            ''', (drop_time, student_id, today))
            
            # Get student and route info for message
            student_info = cursor.execute('''
                SELECT s.name, r.route_name 
                FROM students s
                JOIN routes r ON s.route_id = r.route_id
                WHERE s.student_id = ?
            ''', (student_id,)).fetchone()
            
            if student_info:
                # Send drop-off message to parent
                send_attendance_message_to_parent(
                    student_id, 
                    student_info['name'], 
                    drop_time, 
                    student_info['route_name'],
                    'drop_off'
                )
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True, 
                'message': f'Drop-off attendance marked for {student_info["name"] if student_info else "student"}'
            })
        else:
            conn.close()
            return jsonify({'success': False, 'error': 'No boarding record found for today'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/test_attendance_message', methods=['POST'])
@login_required
def test_attendance_message():
    """Test endpoint to send attendance message"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        student_id = request.form.get('student_id')
        message_type = request.form.get('message_type', 'boarding')
        
        if not student_id:
            return jsonify({'success': False, 'error': 'Student ID required'})
        
        conn = get_db_connection()
        student = conn.execute('''
            SELECT s.name, r.route_name 
            FROM students s
            JOIN routes r ON s.route_id = r.route_id
            WHERE s.student_id = ?
        ''', (student_id,)).fetchone()
        
        if student:
            current_time = datetime.now().strftime('%H:%M:%S')
            success = send_attendance_message_to_parent(
                student_id, 
                student['name'], 
                current_time, 
                student['route_name'],
                message_type
            )
            
            conn.close()
            
            if success:
                return jsonify({
                    'success': True, 
                    'message': f'Test {message_type} message sent to parent of {student["name"]}'
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to send message'})
        else:
            conn.close()
            return jsonify({'success': False, 'error': 'Student not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if session['role'] != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    
    # Get statistics
    total_students = conn.execute('SELECT COUNT(*) as count FROM students').fetchone()['count']
    pending_passes = conn.execute('SELECT COUNT(*) as count FROM bus_passes WHERE status = "pending"').fetchone()['count']
    approved_passes = conn.execute('SELECT COUNT(*) as count FROM bus_passes WHERE status = "approved"').fetchone()['count']
    today_attendance = conn.execute('SELECT COUNT(*) as count FROM attendance WHERE date = ?', 
                                  (datetime.now().date(),)).fetchone()['count']
    
    # Get recent applications
    recent_applications = conn.execute('''
        SELECT b.pass_id, s.name, s.roll_number, b.pass_number, b.status, b.created_at
        FROM bus_passes b
        JOIN students s ON b.student_id = s.student_id
        ORDER BY b.created_at DESC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         total_students=total_students,
                         pending_passes=pending_passes,
                         approved_passes=approved_passes,
                         today_attendance=today_attendance,
                         recent_applications=recent_applications)

@app.route('/admin/pass_applications')
@login_required
def admin_pass_applications():
    if session['role'] != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    applications = conn.execute('''
        SELECT b.*, s.name, s.roll_number, s.department, s.phone_number
        FROM bus_passes b
        JOIN students s ON b.student_id = s.student_id
        ORDER BY b.created_at DESC
    ''').fetchall()
    conn.close()
    
    return render_template('admin_applications.html', applications=applications)

@app.route('/admin/approve_pass/<int:pass_id>', methods=['POST'])
@login_required
def approve_pass(pass_id):
    if session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    conn = get_db_connection()
    # Approve the pass
    conn.execute('UPDATE bus_passes SET status = ? WHERE pass_id = ?', ('approved', pass_id))
    
    # Auto-assign route_id to student based on the approved bus pass route
    bus_pass = conn.execute('SELECT student_id, route FROM bus_passes WHERE pass_id = ?', (pass_id,)).fetchone()
    if bus_pass and bus_pass['route']:
        route = conn.execute('SELECT route_id FROM routes WHERE route_name = ?', (bus_pass['route'],)).fetchone()
        if route:
            conn.execute('UPDATE students SET route_id = ? WHERE student_id = ?', (route['route_id'], bus_pass['student_id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Bus pass approved successfully'})

@app.route('/admin/reject_pass/<int:pass_id>', methods=['POST'])
@login_required
def reject_pass(pass_id):
    if session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    conn = get_db_connection()
    conn.execute('UPDATE bus_passes SET status = ? WHERE pass_id = ?', ('rejected', pass_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Bus pass rejected'})

@app.route('/admin/routes')
@login_required
def admin_routes():
    if session['role'] != 'admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    routes = conn.execute('''
        SELECT r.*, u.username as driver_username
        FROM routes r
        LEFT JOIN users u ON r.driver_id = u.user_id
        ORDER BY r.route_id
    ''').fetchall()
    drivers = conn.execute("SELECT user_id, username FROM users WHERE role = 'driver' ORDER BY username").fetchall()
    conn.close()
    return render_template('admin_routes.html', routes=routes, drivers=drivers)


@app.route('/admin/route/add', methods=['GET', 'POST'])
@login_required
def admin_route_add():
    if session['role'] != 'admin':
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('route_name', '').strip()
        start = request.form.get('start_point', '').strip()
        end = request.form.get('end_point', '').strip()
        stops = request.form.get('stops', '').strip()
        driver_id = request.form.get('driver_id') or None
        if driver_id:
            try:
                driver_id = int(driver_id)
            except ValueError:
                driver_id = None
        if not name:
            flash('Route name required')
            return redirect(url_for('admin_route_add'))
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO routes (route_name, start_point, end_point, stops, driver_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, start, end, stops, driver_id))
            conn.commit()
            flash('Route added.', 'success')
        except sqlite3.IntegrityError:
            flash('Route name already exists.')
        conn.close()
        return redirect(url_for('admin_routes'))
    conn = get_db_connection()
    drivers = conn.execute("SELECT user_id, username FROM users WHERE role = 'driver'").fetchall()
    conn.close()
    return render_template('admin_route_form.html', route=None, drivers=drivers)


@app.route('/admin/route/<int:route_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_route_edit(route_id):
    if session['role'] != 'admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    route = conn.execute('SELECT * FROM routes WHERE route_id = ?', (route_id,)).fetchone()
    if not route:
        conn.close()
        flash('Route not found')
        return redirect(url_for('admin_routes'))
    if request.method == 'POST':
        name = request.form.get('route_name', '').strip()
        start = request.form.get('start_point', '').strip()
        end = request.form.get('end_point', '').strip()
        stops = request.form.get('stops', '').strip()
        driver_id = request.form.get('driver_id') or None
        if driver_id:
            try:
                driver_id = int(driver_id)
            except ValueError:
                driver_id = None
        if not name:
            flash('Route name required')
            conn.close()
            return redirect(url_for('admin_route_edit', route_id=route_id))
        conn.execute('''
            UPDATE routes SET route_name = ?, start_point = ?, end_point = ?, stops = ?, driver_id = ?
            WHERE route_id = ?
        ''', (name, start, end, stops, driver_id, route_id))
        conn.commit()
        conn.close()
        flash('Route updated.', 'success')
        return redirect(url_for('admin_routes'))
    drivers = conn.execute("SELECT user_id, username FROM users WHERE role = 'driver'").fetchall()
    conn.close()
    return render_template('admin_route_form.html', route=route, drivers=drivers)


@app.route('/admin/route/<int:route_id>/delete', methods=['POST'])
@login_required
def admin_route_delete(route_id):
    if session['role'] != 'admin':
        return jsonify({'success': False})
    conn = get_db_connection()
    conn.execute('UPDATE routes SET driver_id = NULL WHERE route_id = ?', (route_id,))
    conn.execute('DELETE FROM routes WHERE route_id = ?', (route_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/admin/students')
@login_required
def admin_students():
    if session['role'] != 'admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    students = conn.execute('''
        SELECT s.*, r.route_name
        FROM students s
        LEFT JOIN routes r ON s.route_id = r.route_id
        ORDER BY s.student_id
    ''').fetchall()
    routes = conn.execute('SELECT route_id, route_name FROM routes ORDER BY route_name').fetchall()
    conn.close()
    return render_template('admin_students.html', students=students, routes=routes)


@app.route('/admin/student/<int:student_id>/assign_route', methods=['POST'])
@login_required
def admin_student_assign_route(student_id):
    if session['role'] != 'admin':
        return jsonify({'success': False})
    route_id = request.form.get('route_id') or (request.get_json(silent=True) or {}).get('route_id')
    if route_id is not None:
        try:
            route_id = int(route_id) if route_id != '' else None
        except ValueError:
            route_id = None
    conn = get_db_connection()
    conn.execute('UPDATE students SET route_id = ? WHERE student_id = ?', (route_id, student_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/admin/attendance_report')
@login_required
def admin_attendance_report():
    if session['role'] != 'admin':
        return redirect(url_for('index'))
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    route_id = request.args.get('route_id')
    student_id = request.args.get('student_id')
    export = request.args.get('export')  # 'excel' or 'pdf'
    conn = get_db_connection()
    q = '''
        SELECT a.date, a.boarding_time, s.name, s.roll_number, s.department, b.pass_number, r.route_name
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        JOIN bus_passes b ON a.pass_id = b.pass_id
        LEFT JOIN routes r ON s.route_id = r.route_id
        WHERE 1=1
    '''
    params = []
    if date_from:
        q += ' AND a.date >= ?'
        params.append(date_from)
    if date_to:
        q += ' AND a.date <= ?'
        params.append(date_to)
    if route_id:
        q += ' AND s.route_id = ?'
        params.append(route_id)
    if student_id:
        q += ' AND s.student_id = ?'
        params.append(student_id)
    q += ' ORDER BY a.date DESC, a.boarding_time DESC LIMIT 500'
    attendance = conn.execute(q, params).fetchall()
    routes = conn.execute('SELECT route_id, route_name FROM routes').fetchall()
    students = conn.execute('SELECT student_id, name FROM students ORDER BY name').fetchall()
    conn.close()
    if export == 'excel':
        try:
            from openpyxl import Workbook
            from io import BytesIO
            wb = Workbook()
            ws = wb.active
            ws.title = 'Attendance'
            ws.append(['Date', 'Boarding Time', 'Student Name', 'Roll Number', 'Department', 'Pass Number', 'Route'])
            for r in attendance:
                ws.append([str(r['date']), str(r['boarding_time'] or ''), str(r['name']), str(r['roll_number'] or ''), str(r['department'] or ''), str(r['pass_number'] or ''), str(r['route_name'] or '')])
            buf = BytesIO()
            wb.save(buf)
            buf.seek(0)
            from flask import send_file
            return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='attendance_report.xlsx')
        except Exception as e:
            flash(f'Export failed: {e}')
    if export == 'pdf':
        return render_template('admin_attendance.html', attendance=attendance, routes=routes or [], students=students or [], pdf_view=True)
    return render_template('admin_attendance.html', attendance=attendance, routes=routes, students=students)

@app.route('/admin/driver_allocation')
@login_required
def admin_driver_allocation():
    if session['role'] != 'admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    # Get all students with their route and driver info
    students = conn.execute('''
        SELECT s.*, r.route_name, r.route_id, u.username as driver_username
        FROM students s
        LEFT JOIN routes r ON s.route_id = r.route_id
        LEFT JOIN users u ON r.driver_id = u.user_id
        ORDER BY s.name
    ''').fetchall()
    # Get all routes with driver info
    routes = conn.execute('''
        SELECT r.*, u.username as driver_username
        FROM routes r
        LEFT JOIN users u ON r.driver_id = u.user_id
        ORDER BY r.route_name
    ''').fetchall()
    # Get all drivers
    drivers = conn.execute("SELECT user_id, username, phone_number FROM users WHERE role = 'driver' ORDER BY username").fetchall()
    conn.close()
    return render_template('admin_driver_allocation.html', students=students, routes=routes, drivers=drivers)

@app.route('/admin/assign_driver_route', methods=['POST'])
@login_required
def admin_assign_driver_route():
    if session['role'] != 'admin':
        return redirect(url_for('index'))
    route_id = request.form.get('route_id')
    driver_id = request.form.get('driver_id')
    if not route_id or not driver_id:
        flash('Please select both route and driver')
        return redirect(url_for('admin_driver_allocation'))
    conn = get_db_connection()
    conn.execute('UPDATE routes SET driver_id = ? WHERE route_id = ?', (driver_id, route_id))
    conn.commit()
    conn.close()
    flash('Driver assigned to route successfully!', 'success')
    return redirect(url_for('admin_driver_allocation'))

@app.route('/admin/assign_students_route', methods=['POST'])
@login_required
def admin_assign_students_route():
    if session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    route_id = request.form.get('route_id')
    student_ids_json = request.form.get('student_ids', '[]')
    try:
        student_ids = json.loads(student_ids_json)
    except:
        return jsonify({'success': False, 'error': 'Invalid student IDs'})
    if not route_id or not student_ids:
        return jsonify({'success': False, 'error': 'Missing data'})
    conn = get_db_connection()
    for sid in student_ids:
        conn.execute('UPDATE students SET route_id = ? WHERE student_id = ?', (route_id, sid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/admin/drivers')
@login_required
def admin_drivers():
    if session['role'] != 'admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    # Get all drivers with their assigned routes
    drivers = conn.execute('''
        SELECT u.user_id, u.username, u.phone_number, r.route_id, r.route_name
        FROM users u
        LEFT JOIN routes r ON r.driver_id = u.user_id
        WHERE u.role = 'driver'
        ORDER BY u.username
    ''').fetchall()
    routes = conn.execute('SELECT route_id, route_name FROM routes ORDER BY route_name').fetchall()
    conn.close()
    return render_template('admin_drivers.html', drivers=drivers, routes=routes)

@app.route('/admin/add_driver', methods=['POST'])
@login_required
def admin_add_driver():
    if session['role'] != 'admin':
        return redirect(url_for('index'))
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    phone_number = request.form.get('phone_number', '').strip()
    route_id = request.form.get('route_id') or None
    
    if not username or not password:
        flash('Username and password are required')
        return redirect(url_for('admin_drivers'))
    
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password, role, phone_number) VALUES (?, ?, ?, ?)',
                      (username, hash_password(password), 'driver', phone_number))
        driver_id = cursor.lastrowid
        
        # Assign route if selected
        if route_id:
            conn.execute('UPDATE routes SET driver_id = ? WHERE route_id = ?', (driver_id, route_id))
        
        conn.commit()
        flash('Driver added successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Username already exists')
    finally:
        conn.close()
    return redirect(url_for('admin_drivers'))

@app.route('/admin/assign_route_to_driver', methods=['POST'])
@login_required
def admin_assign_route_to_driver():
    if session['role'] != 'admin':
        return redirect(url_for('index'))
    driver_id = request.form.get('driver_id')
    route_id = request.form.get('route_id') or None
    
    conn = get_db_connection()
    # First, remove driver from any existing route
    conn.execute('UPDATE routes SET driver_id = NULL WHERE driver_id = ?', (driver_id,))
    # Then assign to new route if selected
    if route_id:
        conn.execute('UPDATE routes SET driver_id = ? WHERE route_id = ?', (driver_id, route_id))
    conn.commit()
    conn.close()
    flash('Route assigned successfully!', 'success')
    return redirect(url_for('admin_drivers'))

@app.route('/admin/delete_driver/<int:driver_id>', methods=['POST'])
@login_required
def admin_delete_driver(driver_id):
    if session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    conn = get_db_connection()
    # Remove driver from routes first
    conn.execute('UPDATE routes SET driver_id = NULL WHERE driver_id = ?', (driver_id,))
    # Delete driver
    conn.execute('DELETE FROM users WHERE user_id = ? AND role = ?', (driver_id, 'driver'))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/test_camera')
def test_camera():
    """Test camera functionality"""
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return jsonify({
                'success': False,
                'error': 'Camera not accessible. Check if camera is connected and not in use.'
            })
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            return jsonify({
                'success': True,
                'message': 'Camera is working properly',
                'resolution': f'{frame.shape[1]}x{frame.shape[0]}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Camera accessible but failed to capture image'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Camera test failed: {str(e)}'
        })

if __name__ == '__main__':
    init_db()
    # Running on HTTP for local development
    app.run(debug=True, host='0.0.0.0', port=5000)
