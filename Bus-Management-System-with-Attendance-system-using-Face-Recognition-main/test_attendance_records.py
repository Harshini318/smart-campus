import sqlite3
import os
from datetime import datetime, date, timedelta

def test_driver_attendance_records():
    """Test what data the driver attendance records route returns"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    print("Testing Driver Attendance Records Route")
    print("=" * 50)
    
    # Get drivers
    drivers = conn.execute('''
        SELECT user_id, username 
        FROM users 
        WHERE role = 'driver'
    ''').fetchall()
    
    for driver in drivers:
        print(f"\nDriver: {driver[1]} (ID: {driver[0]})")
        print("-" * 40)
        
        # Simulate the route query
        my_route = conn.execute('SELECT route_id, route_name FROM routes WHERE driver_id = ?', (driver[0],)).fetchone()
        route_id = my_route['route_id'] if my_route else None
        
        if route_id:
            print(f"Route: {my_route[1]} (ID: {route_id})")
            
            # Build the query exactly like in the app
            q = '''
                SELECT a.date, a.boarding_time, a.drop_time, a.verification_type, a.status,
                       s.name, s.roll_number, s.department, s.year, 
                       COALESCE(b.pass_number, 'No Pass') as pass_number
                FROM attendance a
                JOIN students s ON a.student_id = s.student_id
                LEFT JOIN bus_passes b ON a.pass_id = b.pass_id
                WHERE 1=1
                AND s.route_id = ?
                ORDER BY a.date DESC, a.boarding_time DESC
                LIMIT 10
            '''
            
            records = conn.execute(q, (route_id,)).fetchall()
            
            print(f"Found {len(records)} attendance records:")
            for i, record in enumerate(records, 1):
                print(f"  {i}. {record[4]} - {record[0]} at {record[1]} (Pass: {record[8]}) Status: {record[3]} Drop: {record[2]}")
            
            if len(records) == 0:
                print("❌ No records found!")
                
                # Check if there are any attendance records at all for this route
                total_for_route = conn.execute('''
                    SELECT COUNT(*) FROM attendance a
                    JOIN students s ON a.student_id = s.student_id
                    WHERE s.route_id = ?
                ''', (route_id,)).fetchone()[0]
                
                print(f"Total attendance records for this route: {total_for_route}")
                
                # Check if there are students on this route
                students_on_route = conn.execute('''
                    SELECT COUNT(*) FROM students WHERE route_id = ?
                ''', (route_id,)).fetchone()[0]
                
                print(f"Total students on this route: {students_on_route}")
        else:
            print("No route assigned to this driver")
    
    conn.close()
    print("\n" + "=" * 50)
    print("Driver attendance records test completed!")

if __name__ == '__main__':
    test_driver_attendance_records()
