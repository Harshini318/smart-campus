import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
import random

def balance_student_distribution():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all drivers
    cursor.execute("SELECT user_id, username FROM users WHERE role = 'driver'")
    drivers = cursor.fetchall()
    
    # Get all routes
    cursor.execute("SELECT route_id, route_name FROM routes")
    routes = cursor.fetchall()
    
    # Check current student distribution
    print("Current student distribution:")
    for driver_id, driver_username in drivers:
        cursor.execute('''
            SELECT COUNT(*) as student_count
            FROM students s
            JOIN users u ON s.user_id = u.user_id
            JOIN routes r ON s.route_id = r.route_id
            WHERE r.driver_id = ?
        ''', (driver_id,))
        
        count = cursor.fetchone()[0]
        print(f"  {driver_username}: {count} students")
    
    # Generate additional students to reach 50 per driver
    first_names = ["RAVI", "PRIYA", "AJAY", "NEHA", "KARAN", "ANJALI", "VIKRAM", "SNEHA", "ROHIT", "KAVYA"]
    last_names = ["KUMAR", "SHARMA", "VERMA", "MEHTA", "GUPTA", "RAO", "REDDY", "NAIDU", "SINGH", "YADAV"]
    
    student_counter = 1000  # Start from 1000 to avoid conflicts
    
    for driver_id, driver_username in drivers:
        # Get current student count for this driver
        cursor.execute('''
            SELECT COUNT(*) as student_count
            FROM students s
            JOIN users u ON s.user_id = u.user_id
            JOIN routes r ON s.route_id = r.route_id
            WHERE r.driver_id = ?
        ''', (driver_id,))
        
        current_count = cursor.fetchone()[0]
        students_needed = 50 - current_count
        
        if students_needed > 0:
            print(f"\nAdding {students_needed} students to {driver_username}")
            
            # Get routes for this driver
            cursor.execute("SELECT route_id, route_name FROM routes WHERE driver_id = ?", (driver_id,))
            driver_routes = cursor.fetchall()
            
            if not driver_routes:
                # Assign a route to this driver if they don't have one
                if routes:
                    route_id, route_name = routes[0]
                    cursor.execute("UPDATE routes SET driver_id = ? WHERE route_id = ?", (driver_id, route_id))
                    driver_routes = [(route_id, route_name)]
                    print(f"  Assigned route {route_name} to driver {driver_username}")
                else:
                    print(f"  No routes available for {driver_username}")
                    continue
            
            route_id, route_name = driver_routes[0]
            
            for i in range(students_needed):
                student_counter += 1
                
                # Generate student details
                reg_no = f"23X41A{student_counter:04d}"
                name = f"{random.choice(first_names)} {random.choice(last_names)}"
                username = f"s{reg_no.lower()}"
                
                # Add user account
                hashed_password = hashlib.sha256('student123'.encode()).hexdigest()
                cursor.execute('''
                    INSERT INTO users (username, password, role)
                    VALUES (?, ?, ?)
                ''', (username, hashed_password, 'student'))
                user_id = cursor.lastrowid
                
                # Add student details
                cursor.execute('''
                    INSERT INTO students (user_id, name, roll_number, department, year, phone_number, 
                                        father_name, father_phone, address, route_id, parent_password)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, name, reg_no, 'Computer Science', '3rd Year', 
                      f'99{reg_no[2:]}', f'Father of {name}', f'99{reg_no[2:]}', 
                      f'Address for {name}', route_id, 'parent123'))
                
                student_id = cursor.lastrowid
                
                # Create bus pass
                pass_number = f"PASS{datetime.now().strftime('%Y%m%d')}{student_id:04d}"
                issue_date = datetime.now().date()
                expiry_date = issue_date + timedelta(days=365)
                
                # Get a random stop from the route
                cursor.execute('''
                    SELECT stop_name, amount FROM bus_stops 
                    WHERE route_id = ? 
                    ORDER BY RANDOM() 
                    LIMIT 1
                ''', (route_id,))
                stop_data = cursor.fetchone()
                
                boarding_stop = stop_data[0] if stop_data else 'MAIN STOP'
                pass_amount = stop_data[1] if stop_data else 15000
                
                # Set status (active if total active passes < 30)
                cursor.execute('''
                    SELECT COUNT(*) FROM bus_passes bp
                    JOIN students s ON bp.student_id = s.student_id
                    JOIN routes r ON s.route_id = r.route_id
                    WHERE r.driver_id = ? AND bp.status = 'active'
                ''', (driver_id,))
                
                active_count = cursor.fetchone()[0]
                status = 'active' if active_count < 30 else 'pending'
                
                # Create bus pass
                cursor.execute('''
                    INSERT INTO bus_passes (student_id, pass_number, issue_date, expiry_date, 
                                          route, boarding_stop, pass_amount, photo_path, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (student_id, pass_number, issue_date, expiry_date, route_name, 
                      boarding_stop, pass_amount, f'static/photos/{reg_no}.jpg', status))
                
                print(f"  Added: {name} ({reg_no})")
    
    conn.commit()
    
    # Final distribution check
    print("\nFinal student distribution:")
    for driver_id, driver_username in drivers:
        cursor.execute('''
            SELECT COUNT(*) as total_students,
                   SUM(CASE WHEN bp.status = 'active' THEN 1 ELSE 0 END) as active_passes
            FROM students s
            JOIN users u ON s.user_id = u.user_id
            JOIN routes r ON s.route_id = r.route_id
            LEFT JOIN bus_passes bp ON s.student_id = bp.student_id
            WHERE r.driver_id = ?
        ''', (driver_id,))
        
        total, active = cursor.fetchone()
        print(f"  {driver_username}: {total} students, {active} active bus passes")
    
    conn.close()
    print("\nStudent distribution balanced successfully!")

if __name__ == '__main__':
    balance_student_distribution()
