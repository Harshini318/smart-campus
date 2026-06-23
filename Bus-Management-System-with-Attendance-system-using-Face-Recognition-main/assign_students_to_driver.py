import sqlite3
import os

def assign_students_to_driver():
    """Bulk assign students to a specific driver"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    
    print("Bulk Student to Driver Assignment")
    print("=" * 50)
    
    # Get all drivers
    drivers = conn.execute('SELECT user_id, username FROM users WHERE role = "driver"').fetchall()
    
    print("Available Drivers:")
    for driver in drivers:
        print(f"  ID: {driver[0]}, Username: {driver[1]}")
    
    # Get all routes
    routes = conn.execute('SELECT route_id, route_name FROM routes').fetchall()
    
    print("\nAvailable Routes:")
    for route in routes:
        print(f"  ID: {route[0]}, Name: {route[1]}")
    
    # Example: Assign first 10 students to driver1 (user_id=16)
    driver_id = 16
    route_id = 1  # SRK ROUTE NO-27
    
    # Get students without route assignment
    students = conn.execute('''
        SELECT student_id FROM students 
        WHERE route_id IS NULL OR route_id = ?
        LIMIT 10
    ''', (route_id,)).fetchall()
    
    print(f"\nAssigning {len(students)} students to driver1:")
    
    for student in students:
        conn.execute('UPDATE students SET route_id = ? WHERE student_id = ?', (route_id, student[0]))
        print(f"  - Assigned student {student[0]} to route {route_id}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Successfully assigned {len(students)} students to driver1!")
    print("These students will now appear in driver1's route and parent dashboards.")

if __name__ == '__main__':
    assign_students_to_driver()
