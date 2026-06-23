import sqlite3
import os
from datetime import datetime, date, timedelta

def test_driver_attendance_data():
    """Test that driver attendance data is properly retrieved"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    
    print("Testing Driver Attendance Data")
    print("=" * 50)
    
    # Get drivers
    drivers = conn.execute('''
        SELECT user_id, username, phone_number 
        FROM users 
        WHERE role = 'driver'
        LIMIT 3
    ''').fetchall()
    
    for driver in drivers:
        print(f"\nDriver: {driver[1]} (ID: {driver[0]})")
        print("-" * 40)
        
        # Get driver's route
        my_route = conn.execute('''
            SELECT * FROM routes WHERE driver_id = ?
        ''', (driver[0],)).fetchone()
        
        if my_route:
            print(f"Route: {my_route[1]} (ID: {my_route[0]})")
            
            # Get today's attendance
            today = date.today()
            attendance_records = conn.execute('''
                SELECT a.student_id, a.date, a.boarding_time, a.drop_time, a.verification_type, a.status,
                       s.name, s.roll_number, s.department, s.year, b.pass_number
                FROM attendance a
                JOIN students s ON a.student_id = s.student_id
                LEFT JOIN bus_passes b ON a.student_id = b.student_id
                WHERE s.route_id = ? AND a.date = ?
                ORDER BY a.boarding_time DESC
            ''', (my_route[0], today)).fetchall()
            
            print(f"Today's Attendance ({len(attendance_records)} records):")
            for record in attendance_records:
                print(f"  - {record[6]} ({record[7]}) - Boarding: {record[2]} Drop: {record[3]} Status: {record[4]}")
            
            # Get attendance summary for last 7 days
            attendance_summary = conn.execute('''
                SELECT a.date, COUNT(DISTINCT a.student_id) as present_count,
                       (SELECT COUNT(*) FROM students s2 WHERE s2.route_id = ?) as total_students
                FROM attendance a
                JOIN students s ON a.student_id = s.student_id
                WHERE s.route_id = ? AND a.date >= date('now', '-7 days')
                GROUP BY a.date
                ORDER BY a.date DESC
            ''', (my_route[0], my_route[0])).fetchall()
            
            print(f"\nLast 7 Days Summary:")
            for summary in attendance_summary:
                percentage = (summary[1] / summary[2]) * 100 if summary[2] > 0 else 0
                print(f"  {summary[0]}: {summary[1]}/{summary[2]} present ({percentage:.1f}%)")
            
            # Get route students
            route_students = conn.execute('''
                SELECT s.student_id, s.name, s.roll_number, s.phone_number,
                       b.pass_number, b.status as pass_status
                FROM students s
                LEFT JOIN bus_passes b ON s.student_id = b.student_id
                WHERE s.route_id = ?
                ORDER BY s.name
                LIMIT 5
            ''', (my_route[0],)).fetchall()
            
            print(f"\nRoute Students (showing first 5):")
            for student in route_students:
                print(f"  - {student[1]} ({student[2]}) - Pass: {student[4]} ({student[5]})")
        else:
            print("No route assigned to this driver")
    
    # Check if there are any attendance records at all
    total_attendance = conn.execute('SELECT COUNT(*) as count FROM attendance').fetchone()[0]
    print(f"\n" + "=" * 50)
    print(f"Total attendance records in database: {total_attendance}")
    
    if total_attendance == 0:
        print("❌ No attendance records found!")
        print("💡 Tip: Mark some attendance first using the face recognition system")
    else:
        print("✅ Attendance records found")
        
        # Show recent attendance
        recent = conn.execute('''
            SELECT a.date, a.boarding_time, s.name, r.route_name
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            JOIN routes r ON s.route_id = r.route_id
            ORDER BY a.date DESC, a.boarding_time DESC
            LIMIT 5
        ''').fetchall()
        
        print("\nRecent Attendance Records:")
        for record in recent:
            print(f"  - {record[2]} on {record[0]} at {record[1]} ({record[3]})")
    
    conn.close()
    print("\n" + "=" * 50)
    print("Driver attendance data test completed!")

if __name__ == '__main__':
    test_driver_attendance_data()
