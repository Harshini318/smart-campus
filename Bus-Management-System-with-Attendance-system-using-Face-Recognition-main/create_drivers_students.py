#!/usr/bin/env python3
import sqlite3
import hashlib
from datetime import datetime, timedelta
import random

def get_db_connection():
    conn = sqlite3.connect('transit_system.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Student data for Driver 1 (first 15 students)
driver1_students = [
    {'htno': '24X41A0567', 'name': 'BADI DURGA PRASAD'},
    {'htno': '24X41A0568', 'name': 'BADITHA BHANU PRASAD'},
    {'htno': '24X41A0569', 'name': 'BANAVATH HARSHITHA BAI'},
    {'htno': '24X41A0570', 'name': 'BEJAGAM HEMANTH'},
    {'htno': '24X41A0571', 'name': 'BHEEMARASETTY LAVANYA'},
    {'htno': '24X41A0572', 'name': 'BIKKI VENKATA NAGALAKSHMI'},
    {'htno': '24X41A0573', 'name': 'BOBBA SYAM SITARAM'},
    {'htno': '24X41A0574', 'name': 'BODDEBOYENA GREESHMA'},
    {'htno': '24X41A0575', 'name': 'BOTSA RUCHITHA'},
    {'htno': '24X41A0576', 'name': 'CHANDA JASWANTH'},
    {'htno': '24X41A0577', 'name': 'CHIKKULA JYOTHIRMAI'},
    {'htno': '24X41A0578', 'name': 'CHINTAPALLI NAGARAJU NAIDU'},
    {'htno': '24X41A0579', 'name': 'DALLI APARNA'},
    {'htno': '24X41A0580', 'name': 'DAMATHOTI BINDU KRUTHIKA'},
    {'htno': '24X41A0581', 'name': 'DARSHANAPU SUJITHA'}
]

# Student data for Driver 2 (next 15 students)
driver2_students = [
    {'htno': '24X41A0582', 'name': 'DASARI SUJITHA'},
    {'htno': '24X41A0583', 'name': 'DATTI HEMA DEVI'},
    {'htno': '24X41A0584', 'name': 'DHARA ABHISHEK'},
    {'htno': '24X41A0585', 'name': 'DUGGEMPUDI VENKATA RAVI'},
    {'htno': '24X41A0586', 'name': 'GEDELA SOUMYA SREE'},
    {'htno': '24X41A0587', 'name': 'GURRAM TEJA SRI'},
    {'htno': '24X41A0588', 'name': 'KAGGA JITHENDRA'},
    {'htno': '24X41A0589', 'name': 'KAKARLA HASHWITH RAM'},
    {'htno': '24X41A0590', 'name': 'KALUVA SAI VARSHITHA'},
    {'htno': '24X41A0591', 'name': 'KARICHETI ASHOK'},
    {'htno': '24X41A0592', 'name': 'KILARI VENKATESWARLU'},
    {'htno': '24X41A0593', 'name': 'KODALI DEEPIKA'},
    {'htno': '24X41A0594', 'name': 'KOLLIMARLA HARSHA VARDHINI'},
    {'htno': '24X41A0595', 'name': 'KOLLURU SRI SAI JAHNAVI'},
    {'htno': '24X41A0596', 'name': 'MALLAVALLI RAMA TEJASWINI'}
]

def create_drivers_and_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Driver 1
    cursor.execute('''
        INSERT INTO users (username, password, role, phone_number, status)
        VALUES (?, ?, ?, ?, ?)
    ''', ('driver1', hash_password('driver123'), 'driver', '9876543210', 'active'))
    driver1_id = cursor.lastrowid
    
    # Create Driver 2  
    cursor.execute('''
        INSERT INTO users (username, password, role, phone_number, status)
        VALUES (?, ?, ?, ?, ?)
    ''', ('driver2', hash_password('driver123'), 'driver', '9876543211', 'active'))
    driver2_id = cursor.lastrowid
    
    # Create routes for both drivers
    cursor.execute('''
        INSERT INTO routes (route_name, driver_id, start_point, end_point, driver_name, driver_phone, vehicle_no)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('SRK INSTITUTE OF TECHNOLOGY - ENIKEPADU ROUTE', driver1_id, 'SRK INSTITUTE OF TECHNOLOGY', 'ENIKEPADU-VIJAYAWADA', 'Driver 1', '9876543210', 'AP01AB1234'))
    route1_id = cursor.lastrowid
    
    cursor.execute('''
        INSERT INTO routes (route_name, driver_id, start_point, end_point, driver_name, driver_phone, vehicle_no)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('SRK INSTITUTE OF TECHNOLOGY - VIJAYAWADA ROUTE', driver2_id, 'SRK INSTITUTE OF TECHNOLOGY', 'VIJAYAWADA', 'Driver 2', '9876543211', 'AP02AB5678'))
    route2_id = cursor.lastrowid
    
    print(f"Created Driver 1 (ID: {driver1_id}) with Route {route1_id}")
    print(f"Created Driver 2 (ID: {driver2_id}) with Route {route2_id}")
    
    # Create students and their parents
    for i, student_data in enumerate(driver1_students, 1):
        # Create student
        cursor.execute('''
            INSERT INTO students (name, roll_number, department, year, phone_number, route_id, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student_data['name'], student_data['htno'], 'CSE-B', 'II', f'900000{1000+i}', route1_id, driver1_id))
        student1_id = cursor.lastrowid
        
        # Create parent login (using parent_password field in students table)
        parent_username = f"parent_{student1_id}"
        cursor.execute('''
            INSERT INTO users (username, password, role, phone_number, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (parent_username, hash_password('parent123'), 'parent', f'800000{1000+i}', 'active'))
        parent1_id = cursor.lastrowid
        
        # Update student with parent_password
        cursor.execute('''
            UPDATE students SET parent_password = ? WHERE student_id = ?
        ''', ('parent123', student1_id))
        
        # Create approved bus pass
        pass_number = f"PASS2025{1000+i:04d}"
        cursor.execute('''
            INSERT INTO bus_passes (student_id, pass_number, issue_date, expiry_date, route, boarding_stop, pass_amount, status, photo_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (student1_id, pass_number, datetime.now().date(), (datetime.now() + timedelta(days=365)).date(), 
               'SRK INSTITUTE OF TECHNOLOGY - ENIKEPADU ROUTE', 'MAIN CAMPUS', 12000, 'approved', 'static/pass_photos/default.jpg'))
        
        print(f"Created Student {i}: {student_data['name']} (ID: {student1_id}) with Parent {parent_username}")
    
    for i, student_data in enumerate(driver2_students, 16):
        # Create student
        cursor.execute('''
            INSERT INTO students (name, roll_number, department, year, phone_number, route_id, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student_data['name'], student_data['htno'], 'CSE-B', 'II', f'900000{2000+i}', route2_id, driver2_id))
        student2_id = cursor.lastrowid
        
        # Create parent login
        parent_username = f"parent_{student2_id}"
        cursor.execute('''
            INSERT INTO users (username, password, role, phone_number, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (parent_username, hash_password('parent123'), 'parent', f'800000{2000+i}', 'active'))
        parent2_id = cursor.lastrowid
        
        # Update student with parent_password
        cursor.execute('''
            UPDATE students SET parent_password = ? WHERE student_id = ?
        ''', ('parent123', student2_id))
        
        # Create approved bus pass
        pass_number = f"PASS2025{2000+i:04d}"
        cursor.execute('''
            INSERT INTO bus_passes (student_id, pass_number, issue_date, expiry_date, route, boarding_stop, pass_amount, status, photo_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (student2_id, pass_number, datetime.now().date(), (datetime.now() + timedelta(days=365)).date(), 
               'SRK INSTITUTE OF TECHNOLOGY - VIJAYAWADA ROUTE', 'MAIN CAMPUS', 12000, 'approved', 'static/pass_photos/default.jpg'))
        
        print(f"Created Student {i}: {student_data['name']} (ID: {student2_id}) with Parent {parent_username}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Successfully created:")
    print("👥 2 Drivers (driver1, driver2) with password: driver123")
    print("👨‍🎓 30 Students (15 for each driver)")
    print("👨‍👩‍👧‍👦 30 Parent accounts with password: parent123")
    print("🎫 30 Approved bus passes")
    print("\n📋 Login Credentials:")
    print("Driver 1: username=driver1, password=driver123")
    print("Driver 2: username=driver2, password=driver123")
    print("Parents: username=parent_{student_id}, password=parent123")

if __name__ == "__main__":
    create_drivers_and_students()
