import sqlite3
import os
from datetime import datetime

def send_testnew_attendance_message():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Get testnew student info
    student = conn.execute('''
        SELECT s.student_id, s.name, s.roll_number, s.route_id
        FROM students s WHERE s.roll_number = '24xxxx1789'
    ''').fetchone()
    
    if not student:
        print("Student not found")
        return
    
    print(f"Student: {student[1]} (ID: {student[0]}, Route ID: {student[3]})")
    
    if not student[3]:
        print("No route assigned - cannot send message")
        return
    
    # Get route and driver info
    route = conn.execute('''
        SELECT r.route_id, r.route_name, r.driver_id, u.username, u.phone_number
        FROM routes r
        JOIN users u ON r.driver_id = u.user_id
        WHERE r.route_id = ?
    ''', (student[3],)).fetchone()
    
    if not route:
        print("Route not found")
        return
    
    print(f"Route: {route[1]}, Driver: {route[3]} ({route[4]})")
    
    # Get attendance record
    attendance = conn.execute('''
        SELECT date, boarding_time FROM attendance 
        WHERE student_id = ? ORDER BY date DESC LIMIT 1
    ''', (student[0],)).fetchone()
    
    if attendance:
        attendance_time = attendance[1]
        attendance_date = attendance[0]
        print(f"Attendance: {attendance_date} at {attendance_time}")
        
        # Create attendance message
        message = f"""🚌 Attendance Alert!

Student: {student[1]}
Time: {attendance_time}
Route: {route[1]}
Status: Boarded Successfully

Your child has boarded the bus safely. Thank you!
- SRK Transport System"""
        
        # Insert message
        conn.execute('''
            INSERT INTO driver_parent_messages (driver_id, student_id, sender_type, message)
            VALUES (?, ?, ?, ?)
        ''', (route[2], student[0], 'system', message))
        conn.commit()
        print(f"✅ Attendance message sent to parent of {student[1]}")
    else:
        print("No attendance record found")
    
    # Verify messages
    messages = conn.execute('''
        SELECT m.message, m.sender_type, m.created_at
        FROM driver_parent_messages m
        WHERE m.student_id = ?
        ORDER BY m.created_at DESC LIMIT 3
    ''', (student[0],)).fetchall()
    
    print(f"\nMessages for testnew parent ({len(messages)} total):")
    for m in messages:
        print(f"  [{m[1]}] {m[0][:60]}...")
    
    conn.close()

if __name__ == '__main__':
    send_testnew_attendance_message()
