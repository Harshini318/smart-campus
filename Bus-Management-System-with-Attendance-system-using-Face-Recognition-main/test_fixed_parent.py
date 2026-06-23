import sqlite3
import os

def test_fixed_parent_login():
    """Test the fixed parent login"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    print("Testing Fixed Parent Login")
    print("=" * 50)
    
    # Test with student_id = 1 (Navya Sri)
    student_id = '1'
    
    # Use the exact same query as fixed parent dashboard
    student = conn.execute('SELECT s.student_id, s.name, s.roll_number, s.route_id FROM students s WHERE s.student_id = ?', (student_id,)).fetchone()
    
    if student:
        print(f"✅ Student found: {student[1]}")
        print(f"Roll Number: {student[2]}")
        print(f"Route ID: {student[3]}")
        
        if student[3]:  # Has route assigned
            # Get driver info like parent dashboard does
            driver_info = conn.execute('''
                SELECT u.username as driver_name, u.phone_number as driver_phone, r.route_name
                FROM routes r
                JOIN users u ON r.driver_id = u.user_id
                WHERE r.route_id = ?
            ''', (student[3],)).fetchone()
            
            if driver_info:
                print(f"✅ Driver Found: {driver_info[0]} ({driver_info[1]})")
                print(f"✅ Route: {driver_info[2]}")
            else:
                print("❌ No driver found for this route")
        else:
            print("❌ No route assigned to student")
    else:
        print("❌ Student not found")
    
    conn.close()
    print("\n" + "=" * 50)
    print("Fixed parent login test completed!")

if __name__ == '__main__':
    test_fixed_parent_login()
