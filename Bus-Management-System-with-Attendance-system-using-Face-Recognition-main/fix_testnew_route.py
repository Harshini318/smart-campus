import sqlite3
import os

def fix_testnew_route():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    
    # Find testnew student
    student = conn.execute('''
        SELECT s.student_id, s.name, s.roll_number, s.route_id
        FROM students s
        WHERE s.roll_number = '24xxxx1789'
    ''').fetchone()
    
    if student:
        print(f"Student: {student[1]} (ID: {student[0]})")
        print(f"Current route_id: {student[3]}")
        
        # Find the route from their bus pass
        bus_pass = conn.execute('''
            SELECT pass_id, route, status FROM bus_passes WHERE student_id = ?
        ''', (student[0],)).fetchone()
        
        if bus_pass:
            print(f"Bus Pass Route: {bus_pass[1]} (Status: {bus_pass[2]})")
            
            # Find the route_id for this route name
            route = conn.execute('''
                SELECT route_id, route_name, driver_id FROM routes WHERE route_name = ?
            ''', (bus_pass[1],)).fetchone()
            
            if route:
                print(f"Found route: {route[1]} (ID: {route[0]}, Driver ID: {route[2]})")
                
                # Assign student to this route
                conn.execute('UPDATE students SET route_id = ? WHERE student_id = ?', (route[0], student[0]))
                conn.commit()
                print(f"✅ Assigned student to route_id: {route[0]}")
                
                # Verify
                updated = conn.execute('SELECT route_id FROM students WHERE student_id = ?', (student[0],)).fetchone()
                print(f"Verified route_id: {updated[0]}")
            else:
                print(f"❌ Route not found in routes table: {bus_pass[1]}")
        else:
            print("❌ No bus pass found for this student")
    else:
        print("❌ Student not found")
    
    # Also fix ALL students who have bus passes with routes but no route_id
    print("\nFixing all students with bus passes but no route assignment...")
    unassigned = conn.execute('''
        SELECT s.student_id, s.name, b.route
        FROM students s
        JOIN bus_passes b ON s.student_id = b.student_id
        WHERE s.route_id IS NULL AND b.route IS NOT NULL AND b.status = 'approved'
    ''').fetchall()
    
    fixed = 0
    for s in unassigned:
        route = conn.execute('SELECT route_id FROM routes WHERE route_name = ?', (s[2],)).fetchone()
        if route:
            conn.execute('UPDATE students SET route_id = ? WHERE student_id = ?', (route[0], s[0]))
            fixed += 1
    
    conn.commit()
    print(f"✅ Fixed {fixed} additional students")
    
    conn.close()

if __name__ == '__main__':
    fix_testnew_route()
