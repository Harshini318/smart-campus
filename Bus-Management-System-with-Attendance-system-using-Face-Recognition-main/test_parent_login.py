import sqlite3
import os

def test_parent_login():
    """Test parent login for a specific student"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    print("Testing Parent Login for Navya Sri (CS001)")
    print("=" * 50)
    
    # Simulate parent login for CS001
    student_id = '1'  # Use student_id, not roll_number
    password = 'parent123'
    
    print(f"Attempting login with Student ID: {student_id}")
    print(f"Password: {password}")
    
    # Get student data
    student = conn.execute(
        'SELECT s.*, COALESCE(s.parent_password, "parent123") as pwd FROM students s WHERE s.student_id = ?',
        (student_id,)
    ).fetchone()
    
    if student:
        print(f"✅ Student found: {student[1]}")
        print(f"Route ID: {student[4]}")
        print(f"Parent password: {student[11]}")
        print(f"Password match: {student[11] == password}")
        
        if (student[11] or '').strip() == password.strip():
            print("✅ Login successful!")
            
            # Now test driver info retrieval like in parent dashboard
            driver_info = conn.execute('''
                SELECT u.username as driver_name, u.phone_number as driver_phone, r.route_name
                FROM routes r
                JOIN users u ON r.driver_id = u.user_id
                WHERE r.route_id = ?
            ''', (student[4],)).fetchone()
            
            if driver_info:
                print(f"✅ Driver Info: {driver_info[0]} ({driver_info[1]})")
                print(f"✅ Route: {driver_info[2]}")
            else:
                print("❌ No driver found for this route")
        else:
            print("❌ Password mismatch")
    else:
        print("❌ Student not found")
    
    conn.close()
    print("\n" + "=" * 50)
    print("Parent login test completed!")

if __name__ == '__main__':
    test_parent_login()
