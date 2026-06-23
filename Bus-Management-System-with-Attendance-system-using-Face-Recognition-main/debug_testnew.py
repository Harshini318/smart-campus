import sqlite3
import os

def debug_testnew_student():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    print("Debugging testnew Student")
    print("=" * 50)
    
    # Find testnew student
    students = conn.execute('''
        SELECT s.student_id, s.name, s.roll_number, s.route_id, s.parent_password,
               u.username
        FROM students s
        JOIN users u ON s.user_id = u.user_id
        WHERE u.username LIKE '%test%' OR s.name LIKE '%test%'
    ''').fetchall()
    
    print(f"Found {len(students)} students matching 'test':")
    for s in students:
        print(f"  Student ID: {s[0]}, Name: {s[1]}, Roll: {s[2]}, Route ID: {s[3]}, Username: {s[5]}")
    
    # Also check by roll number 24xxxx1789
    student = conn.execute('''
        SELECT s.student_id, s.name, s.roll_number, s.route_id, s.parent_password,
               u.username
        FROM students s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.roll_number = '24xxxx1789'
    ''').fetchone()
    
    if student:
        print(f"\ntestnew Student Details:")
        print(f"  Student ID: {student[0]}")
        print(f"  Name: {student[1]}")
        print(f"  Roll: {student[2]}")
        print(f"  Route ID: {student[3]}")
        print(f"  Parent Password: {student[4]}")
        print(f"  Username: {student[5]}")
        
        if student[3]:
            # Check route and driver
            route = conn.execute('SELECT * FROM routes WHERE route_id = ?', (student[3],)).fetchone()
            print(f"\n  Route Details:")
            if route:
                print(f"    Route ID: {route[0]}")
                print(f"    Route Name: {route[1]}")
                print(f"    Driver ID: {route[5]}")
                
                if route[5]:
                    driver = conn.execute('SELECT user_id, username, phone_number FROM users WHERE user_id = ?', (route[5],)).fetchone()
                    print(f"    Driver: {driver[1]} ({driver[2]})")
                else:
                    print(f"    ❌ NO DRIVER ASSIGNED TO THIS ROUTE!")
            else:
                print(f"    ❌ Route not found!")
        else:
            print(f"  ❌ NO ROUTE ASSIGNED TO STUDENT!")
        
        # Check attendance
        attendance = conn.execute('''
            SELECT a.* FROM attendance a WHERE a.student_id = ? ORDER BY a.date DESC LIMIT 5
        ''', (student[0],)).fetchall()
        print(f"\n  Attendance Records: {len(attendance)}")
        for a in attendance:
            print(f"    Date: {a[3]}, Boarding: {a[4]}, Status: {a[6]}")
        
        # Check messages
        messages = conn.execute('''
            SELECT m.*, u.username as driver_username
            FROM driver_parent_messages m
            LEFT JOIN users u ON m.driver_id = u.user_id
            WHERE m.student_id = ?
            ORDER BY m.created_at DESC LIMIT 5
        ''', (student[0],)).fetchall()
        print(f"\n  Messages: {len(messages)}")
        for m in messages:
            print(f"    From: {m[9]}, Type: {m[3]}, Message: {m[4][:50]}...")
    else:
        print("\n❌ Student with roll 24xxxx1789 not found!")
    
    conn.close()

if __name__ == '__main__':
    debug_testnew_student()
