#!/usr/bin/env python3
import sqlite3
import hashlib
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('transit_system.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_new_route():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create new driver for this route
    cursor.execute('''
        INSERT INTO users (username, password, role, phone_number, status)
        VALUES (?, ?, ?, ?, ?)
    ''', ('driver3', hash_password('driver123'), 'driver', '9876543212', 'active'))
    driver3_id = cursor.lastrowid
    
    # Create the new route
    route_name = "SRK INSTITUTE OF TECHNOLOGY - BENZ CIRCLE ROUTE"
    stops_text = "SRK INSTITUTE OF TECHNOLOGY,BENZ CIRCLE,RAMAVARAPPADU,SITARA CENTER,RTC WORK SHOP,CHURCH,HB COLONY,SRK COLLEGE"
    
    cursor.execute('''
        INSERT INTO routes (route_name, start_point, end_point, stops, driver_id, vehicle_no, driver_name, driver_phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (route_name, 'SRK INSTITUTE OF TECHNOLOGY', 'BENZ CIRCLE', stops_text, driver3_id, 'AP03AB9999', 'Driver 3', '9876543212'))
    route_id = cursor.lastrowid
    
    print(f"Created Driver 3 (ID: {driver3_id}) with Route {route_id}")
    print(f"Route Name: {route_name}")
    print(f"Route: SRK INSTITUTE OF TECHNOLOGY -> BENZ CIRCLE")
    print(f"Boarding Points: {stops_text}")
    
    # Create sample students for this route (10 students)
    students_data = [
        {'htno': '24X41A0597', 'name': 'ANAPARTHI SAI KUMAR'},
        {'htno': '24X41A0598', 'name': 'ANASUYA DEVI'},
        {'htno': '24X41A0599', 'name': 'ARUN KUMAR'},
        {'htno': '24X41A0600', 'name': 'BHAVANI SHANKAR'},
        {'htno': '24X41A0601', 'name': 'CHANDRA SEKHAR'},
        {'htno': '24X41A0602', 'name': 'DEEPTHI SRI'},
        {'htno': '24X41A0603', 'name': 'GANESH BABU'},
        {'htno': '24X41A0604', 'name': 'HARISH KUMAR'},
        {'htno': '24X41A0605', 'name': 'INDIRA PRIYADARSHINI'},
        {'htno': '24X41A0606', 'name': 'JAYA KRISHNA'}
    ]
    
    for i, student_data in enumerate(students_data, 1):
        # Create student
        cursor.execute('''
            INSERT INTO students (name, roll_number, department, year, phone_number, route_id, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student_data['name'], student_data['htno'], 'CSE-B', 'II', f'900000{3000+i}', route_id, driver3_id))
        student_id = cursor.lastrowid
        
        # Create parent login
        parent_username = f"parent_{student_id}"
        cursor.execute('''
            INSERT INTO users (username, password, role, phone_number, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (parent_username, hash_password('parent123'), 'parent', f'800000{3000+i}', 'active'))
        parent_id = cursor.lastrowid
        
        # Update student with parent_password
        cursor.execute('''
            UPDATE students SET parent_password = ? WHERE student_id = ?
        ''', ('parent123', student_id))
        
        # Create approved bus pass
        pass_number = f"PASS2025{3000+i:04d}"
        cursor.execute('''
            INSERT INTO bus_passes (student_id, pass_number, issue_date, expiry_date, route, boarding_stop, pass_amount, status, photo_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (student_id, pass_number, datetime.now().date(), (datetime.now() + timedelta(days=365)).date(), 
               route_name, 'SRK INSTITUTE OF TECHNOLOGY', 12000, 'approved', 'static/pass_photos/default.jpg'))
        
        print(f"Created Student {i}: {student_data['name']} (ID: {student_id}) with Parent {parent_username}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("NEW ROUTE SUCCESSFULLY ADDED!")
    print("="*60)
    print(f"Route: {route_name}")
    print(f"Driver: driver3 (password: driver123)")
    print(f"Students: 10 students assigned")
    print(f"Parent Accounts: 10 parent accounts created")
    print(f"Bus Passes: 10 approved passes created")
    print("\nBoarding Points:")
    boarding_points = stops_text.split(',')
    for i, point in enumerate(boarding_points, 1):
        print(f"  {i}. {point.strip()}")
    print("\nLogin Credentials:")
    print("Driver 3: username=driver3, password=driver123")
    print("Parents: username=parent_{student_id}, password=parent123")

if __name__ == "__main__":
    from datetime import timedelta
    add_new_route()
