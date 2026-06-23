import sqlite3
import os

def debug_attendance_issue():
    """Debug the attendance issue step by step"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    print("Debugging Attendance Issue")
    print("=" * 50)
    
    # Check one specific attendance record
    record = conn.execute('''
        SELECT a.*, s.name, s.roll_number, s.department, s.year,
               b.pass_number as bus_pass_number
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        LEFT JOIN bus_passes b ON a.pass_id = b.pass_id
        WHERE a.student_id = 1
        LIMIT 1
    ''').fetchone()
    
    if record:
        print("Single attendance record:")
        print(f"  Keys: {list(record.keys())}")
        print(f"  Values: {list(record)}")
        print(f"  pass_number: {record[8]} (index 8)")
        print(f"  bus_pass_number: {record['bus_pass_number']}")
    
    # Check the bus_passes table for this student
    pass_info = conn.execute('''
        SELECT * FROM bus_passes WHERE student_id = 1
    ''').fetchone()
    
    if pass_info:
        print(f"\nBus pass for student 1:")
        print(f"  Keys: {list(pass_info.keys())}")
        print(f"  pass_number: {pass_info[2]} (index 2)")
    
    conn.close()

if __name__ == '__main__':
    debug_attendance_issue()
