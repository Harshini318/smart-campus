import sqlite3
import os

def check_pass_numbers():
    """Check what pass numbers exist in the database"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    print("Checking Pass Numbers in Database")
    print("=" * 50)
    
    # Check attendance records with pass info
    records = conn.execute('''
        SELECT a.date, a.boarding_time, a.student_id, a.pass_id,
               s.name, s.roll_number, s.department,
               b.pass_number
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        LEFT JOIN bus_passes b ON a.pass_id = b.pass_id
        LIMIT 5
    ''').fetchall()
    
    print("Sample attendance records with pass info:")
    for record in records:
        print(f"  Student: {record[4]}")
        print(f"  Pass ID: {record[3]}")
        print(f"  Pass Number: {record[7]}")
        print(f"  Department: {record[6]}")
        print("  ---")
    
    # Check bus passes table directly
    passes = conn.execute('''
        SELECT pass_id, pass_number, student_id, status
        FROM bus_passes
        LIMIT 10
    ''').fetchall()
    
    print(f"\nBus passes in database ({len(passes)}):")
    for p in passes:
        print(f"  Pass ID: {p[0]}, Number: {p[1]}, Student: {p[2]}, Status: {p[3]}")
    
    conn.close()

if __name__ == '__main__':
    check_pass_numbers()
