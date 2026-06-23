import sqlite3
import os

def debug_parent_dashboard():
    """Debug parent dashboard driver info issue"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    print("Debugging Parent Dashboard Driver Info")
    print("=" * 50)
    
    # Test with student_id = 1 (Navya Sri)
    student_id = '1'
    
    # Get student data exactly like parent dashboard
    student = conn.execute('SELECT s.student_id, s.name, s.roll_number, s.route_id FROM students s WHERE s.student_id = ?', (student_id,)).fetchone()
    
    if student:
        print(f"✅ Student found: {student[1]}")
        print(f"Roll Number: {student[2]}")
        print(f"Route ID: {student[3]}")
        
        if student[3]:  # Has route assigned
            print(f"✅ Student has route_id: {student[3]}")
            
            # Get driver info like parent dashboard does
            driver_info = conn.execute('''
                SELECT u.username as driver_name, u.phone_number as driver_phone, r.route_name
                FROM routes r
                JOIN users u ON r.driver_id = u.user_id
                WHERE r.route_id = ?
            ''', (student[3],)).fetchone()
            
            print(f"Driver query result: {driver_info}")
            
            if driver_info:
                print(f"✅ Driver Found: {driver_info[0]} ({driver_info[1]})")
                print(f"✅ Driver Phone: {driver_info[1]}")
                print(f"✅ Route Name: {driver_info[2]}")
                print(f"✅ Keys: {list(driver_info.keys())}")
                print(f"✅ Driver Name by key: {driver_info['driver_name']}")
                print(f"✅ Driver Phone by key: {driver_info['driver_phone']}")
            else:
                print("❌ No driver found for this route")
                
                # Check if route has driver assigned directly
                route_check = conn.execute('SELECT driver_id FROM routes WHERE route_id = ?', (student[3],)).fetchone()
                print(f"Route driver_id check: {route_check}")
        else:
            print("❌ No route assigned to student")
    else:
        print("❌ Student not found")
    
    conn.close()
    print("\n" + "=" * 50)
    print("Parent dashboard debug completed!")

if __name__ == '__main__':
    debug_parent_dashboard()
