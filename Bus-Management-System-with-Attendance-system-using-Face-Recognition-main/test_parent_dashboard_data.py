import sqlite3
import os

def test_parent_dashboard_data():
    """Test parent dashboard data flow"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    print("Testing Parent Dashboard Data Flow")
    print("=" * 50)
    
    # Simulate the exact same process as parent dashboard
    student_id = '1'  # Navya Sri
    
    # Step 1: Get student data like parent dashboard
    student = conn.execute('SELECT s.student_id, s.name, s.roll_number, s.route_id FROM students s WHERE s.student_id = ?', (student_id,)).fetchone()
    
    print("Step 1 - Student Query Result:")
    print(f"  Student ID: {student[0] if student else 'None'}")
    print(f"  Name: {student[1] if student else 'None'}")
    print(f"  Roll Number: {student[2] if student else 'None'}")
    print(f"  Route ID: {student[3] if student else 'None'}")
    
    if student and student[3]:  # Has route assigned
        print(f"\nStep 2 - Student has route_id: {student[3]}")
        
        # Step 2: Get driver info like parent dashboard
        driver_info = conn.execute('''
            SELECT u.username as driver_name, u.phone_number as driver_phone, r.route_name
            FROM routes r
            JOIN users u ON r.driver_id = u.user_id
            WHERE r.route_id = ?
        ''', (student[3],)).fetchone()
        
        print("Step 2 - Driver Query Result:")
        print(f"  Driver Info Type: {type(driver_info)}")
        print(f"  Driver Info Value: {driver_info}")
        print(f"  Driver Info is None: {driver_info is None}")
        
        if driver_info:
            print(f"  ✅ Driver Found: {driver_info[0]} ({driver_info[1]})")
            print(f"  ✅ Driver Phone: {driver_info[1]}")
            print(f"  ✅ Route Name: {driver_info[2]}")
            print(f"  ✅ Keys: {list(driver_info.keys())}")
            
            # Step 3: Test template data structure
            print(f"\nStep 3 - Template Data Structure:")
            print(f"  Would be passed to template:")
            print(f"    student: {dict(student) if student else None}")
            print(f"    driver_info: {dict(driver_info) if driver_info else None}")
            
        else:
            print("  ❌ No driver found for this route")
            
            # Step 4: Check if route has driver assigned directly
            route_check = conn.execute('SELECT driver_id FROM routes WHERE route_id = ?', (student[3],)).fetchone()
            print(f"Step 4 - Route driver_id check: {route_check}")
    else:
        print("❌ No route assigned to student")
    
    conn.close()
    print("\n" + "=" * 50)
    print("Parent dashboard data flow test completed!")

if __name__ == '__main__':
    test_parent_dashboard_data()
