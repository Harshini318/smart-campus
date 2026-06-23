import sqlite3
import os

def test_parent_driver_assignment():
    """Test parent driver assignment issue"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    print("Testing Parent Driver Assignment")
    print("=" * 50)
    
    # Get a sample student that should have a driver
    student = conn.execute('''
        SELECT s.student_id, s.name, s.roll_number, s.route_id,
               r.route_name, r.driver_id
        FROM students s
        LEFT JOIN routes r ON s.route_id = r.route_id
        WHERE s.roll_number = 'CS001'
        LIMIT 1
    ''').fetchone()
    
    if student:
        print(f"Student: {student[1]} ({student[2]})")
        print(f"Route ID: {student[3]}")
        print(f"Route Name: {student[4]}")
        print(f"Driver ID: {student[5]}")
        
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
    
    # Check all recent students with routes
    print(f"\nRecent students with route assignments:")
    recent_students = conn.execute('''
        SELECT s.name, s.roll_number, s.route_id, r.route_name, r.driver_id, u.username
        FROM students s
        LEFT JOIN routes r ON s.route_id = r.route_id
        LEFT JOIN users u ON r.driver_id = u.user_id
        WHERE s.route_id IS NOT NULL
        ORDER BY s.student_id DESC
        LIMIT 10
    ''').fetchall()
    
    for stu in recent_students:
        driver_name = stu[5] if stu[5] else "No Driver"
        print(f"  - {stu[1]}: Route {stu[3]} ({stu[4]}) -> Driver: {driver_name}")
    
    conn.close()
    print("\n" + "=" * 50)
    print("Parent driver assignment test completed!")

if __name__ == '__main__':
    test_parent_driver_assignment()
