import sqlite3
import os
from datetime import datetime, date, timedelta
import random

def create_sample_attendance():
    """Create sample attendance records for testing"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating Sample Attendance Records")
    print("=" * 50)
    
    # Get students with valid bus passes
    students = conn.execute('''
        SELECT s.student_id, s.name, s.route_id, b.pass_id, b.pass_number
        FROM students s
        JOIN bus_passes b ON s.student_id = b.student_id
        WHERE b.status = 'active' AND s.route_id IS NOT NULL
        LIMIT 20
    ''').fetchall()
    
    if not students:
        print("❌ No students with active bus passes found!")
        conn.close()
        return
    
    print(f"Found {len(students)} students with active passes")
    
    # Create attendance for today and past few days
    for days_ago in range(3):  # Today, yesterday, day before
        attendance_date = (date.today() - timedelta(days=days_ago))
        
        print(f"\nCreating attendance for {attendance_date}:")
        
        # Randomly select 60-80% of students for attendance each day
        num_students = int(len(students) * random.uniform(0.6, 0.8))
        selected_students = random.sample(students, num_students)
        
        for student in selected_students:
            # Random boarding time between 7:00 AM and 9:00 AM
            boarding_hour = random.randint(7, 8)
            boarding_min = random.randint(0, 59)
            boarding_time = f"{boarding_hour:02d}:{boarding_min:02d}:00"
            
            # Random drop time between 3:00 PM and 6:00 PM
            drop_hour = random.randint(15, 18)
            drop_min = random.randint(0, 59)
            drop_time = f"{drop_hour:02d}:{drop_min:02d}:00"
            
            # Check if attendance already exists
            existing = cursor.execute('''
                SELECT COUNT(*) FROM attendance 
                WHERE student_id = ? AND date = ?
            ''', (student[0], attendance_date)).fetchone()[0]
            
            if existing == 0:
                cursor.execute('''
                    INSERT INTO attendance (student_id, pass_id, date, boarding_time, drop_time, verification_type, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (student[0], student[3], attendance_date, 
                      boarding_time, drop_time, 'face', 'present'))
                
                print(f"  ✓ {student[1]} - Boarding: {boarding_time}, Drop: {drop_time}")
            else:
                print(f"  - {student[1]} - Already recorded")
    
    conn.commit()
    
    # Verify created records
    total_records = cursor.execute('SELECT COUNT(*) FROM attendance').fetchone()[0]
    today_records = cursor.execute('''
        SELECT COUNT(*) FROM attendance WHERE date = ?
    ''', (date.today(),)).fetchone()[0]
    
    print(f"\n" + "=" * 50)
    print(f"✅ Created sample attendance records!")
    print(f"Total records in database: {total_records}")
    print(f"Today's records: {today_records}")
    
    # Show driver-specific stats
    drivers = conn.execute('''
        SELECT u.user_id, u.username, r.route_id, r.route_name
        FROM users u
        LEFT JOIN routes r ON u.user_id = r.driver_id
        WHERE u.role = 'driver' AND r.route_id IS NOT NULL
    ''').fetchall()
    
    print(f"\nDriver Attendance Summary:")
    for driver in drivers:
        if driver[2]:  # Has route assigned
            driver_attendance = cursor.execute('''
                SELECT COUNT(*) FROM attendance a
                JOIN students s ON a.student_id = s.student_id
                WHERE s.route_id = ? AND a.date = ?
            ''', (driver[2], date.today())).fetchone()[0]
            
            print(f"  - {driver[1]} ({driver[3]}): {driver_attendance} students today")
    
    conn.close()
    print("\n" + "=" * 50)
    print("Sample attendance creation completed!")
    print("🚌 Driver dashboard should now show attendance data!")

if __name__ == '__main__':
    create_sample_attendance()
