import sqlite3
import os

def test_driver_details_display():
    """Test that driver details are properly retrieved for students and parents"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    
    print("Testing Driver Details Display")
    print("=" * 50)
    
    # Test 1: Get students with routes
    students = conn.execute('''
        SELECT s.student_id, s.name, s.roll_number, s.route_id, r.route_name
        FROM students s
        LEFT JOIN routes r ON s.route_id = r.route_id
        WHERE s.route_id IS NOT NULL
        LIMIT 5
    ''').fetchall()
    
    print(f"Found {len(students)} students with assigned routes:")
    
    for student in students:
        print(f"\nStudent: {student[1]} ({student[2]})")
        print(f"Route: {student[3]} - {student[4]}")
        
        # Get driver info for this student
        driver_info = conn.execute('''
            SELECT u.username as driver_name, u.phone_number as driver_phone, r.route_name
            FROM routes r
            JOIN users u ON r.driver_id = u.user_id
            WHERE r.route_id = ?
        ''', (student[3],)).fetchone()
        
        if driver_info:
            print(f"✅ Driver: {driver_info[0]}")
            print(f"✅ Driver Phone: {driver_info[1]}")
            print(f"✅ Route: {driver_info[2]}")
        else:
            print("❌ No driver assigned to this route")
    
    # Test 2: Check all routes and their drivers
    print(f"\n" + "=" * 50)
    print("All Routes and Assigned Drivers:")
    
    routes = conn.execute('''
        SELECT r.route_id, r.route_name, u.username as driver_name, u.phone_number as driver_phone
        FROM routes r
        LEFT JOIN users u ON r.driver_id = u.user_id
        ORDER BY r.route_name
    ''').fetchall()
    
    for route in routes:
        if route[2]:  # Driver assigned
            print(f"✅ {route[1]} - Driver: {route[2]} ({route[3]})")
        else:
            print(f"❌ {route[1]} - No driver assigned")
    
    # Test 3: Check recent messages to see if they have driver info
    print(f"\n" + "=" * 50)
    print("Recent Messages and Driver Info:")
    
    messages = conn.execute('''
        SELECT m.message, m.sender_type, m.created_at, s.name as student_name,
               u.username as driver_username
        FROM driver_parent_messages m
        JOIN students s ON m.student_id = s.student_id
        LEFT JOIN users u ON m.driver_id = u.user_id
        ORDER BY m.created_at DESC
        LIMIT 5
    ''').fetchall()
    
    for msg in messages:
        print(f"\nMessage for: {msg[3]}")
        print(f"From: {msg[4] if msg[4] else 'System'}")
        print(f"Type: {msg[1]}")
        print(f"Content: {msg[0][:50]}...")
    
    conn.close()
    print("\n" + "=" * 50)
    print("Driver details test completed!")

if __name__ == '__main__':
    test_driver_details_display()
