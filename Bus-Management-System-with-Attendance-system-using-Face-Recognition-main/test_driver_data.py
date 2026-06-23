#!/usr/bin/env python3
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('transit_system.db')
    conn.row_factory = sqlite3.Row
    return conn

def test_driver_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("=== DRIVER 1 (driver1) TEST ===")
    
    # Test driver 1 route
    my_route = conn.execute('SELECT * FROM routes WHERE driver_id = ?', (15,)).fetchone()
    if my_route:
        print(f"✅ Driver 1 Route: {my_route['route_name']}")
        route_id = my_route['route_id']
        
        # Test route students count
        route_students = conn.execute('''
            SELECT COUNT(DISTINCT s.student_id) as count 
            FROM students s
            JOIN bus_passes b ON s.student_id = b.student_id
            WHERE b.route = (SELECT route_name FROM routes WHERE route_id = ?)
        ''', (route_id,)).fetchone()['count']
        print(f"✅ Route Students Count: {route_students}")
        
        # Test detailed student list
        route_student_details = conn.execute('''
            SELECT DISTINCT s.student_id, s.name, s.roll_number, s.department, s.year, s.phone_number,
                   b.pass_number, b.status as pass_status, b.boarding_stop
            FROM students s
            JOIN bus_passes b ON s.student_id = b.student_id
            WHERE b.route = (SELECT route_name FROM routes WHERE route_id = ?)
            ORDER BY s.name
        ''', (route_id,)).fetchall()
        
        print(f"✅ Students assigned to Driver 1:")
        for i, student in enumerate(route_student_details, 1):
            print(f"   {i}. {student['name']} ({student['roll_number']}) - Pass: {student['pass_number']} - Status: {student['pass_status']}")
    else:
        print("❌ No route found for Driver 1")
    
    print("\n=== DRIVER 2 (driver2) TEST ===")
    
    # Test driver 2 route
    my_route2 = conn.execute('SELECT * FROM routes WHERE driver_id = ?', (16,)).fetchone()
    if my_route2:
        print(f"✅ Driver 2 Route: {my_route2['route_name']}")
        route_id2 = my_route2['route_id']
        
        # Test route students count
        route_students2 = conn.execute('''
            SELECT COUNT(DISTINCT s.student_id) as count 
            FROM students s
            JOIN bus_passes b ON s.student_id = b.student_id
            WHERE b.route = (SELECT route_name FROM routes WHERE route_id = ?)
        ''', (route_id2,)).fetchone()['count']
        print(f"✅ Route Students Count: {route_students2}")
        
        # Test detailed student list
        route_student_details2 = conn.execute('''
            SELECT DISTINCT s.student_id, s.name, s.roll_number, s.department, s.year, s.phone_number,
                   b.pass_number, b.status as pass_status, b.boarding_stop
            FROM students s
            JOIN bus_passes b ON s.student_id = b.student_id
            WHERE b.route = (SELECT route_name FROM routes WHERE route_id = ?)
            ORDER BY s.name
        ''', (route_id2,)).fetchall()
        
        print(f"✅ Students assigned to Driver 2:")
        for i, student in enumerate(route_student_details2, 1):
            print(f"   {i}. {student['name']} ({student['roll_number']}) - Pass: {student['pass_number']} - Status: {student['pass_status']}")
    else:
        print("❌ No route found for Driver 2")
    
    conn.close()

if __name__ == "__main__":
    test_driver_data()
