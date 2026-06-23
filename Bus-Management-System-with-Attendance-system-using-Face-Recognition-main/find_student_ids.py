import sqlite3
import os

def find_student_ids():
    """Find correct student IDs for parent login"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    print("Finding Student IDs for Parent Login")
    print("=" * 50)
    
    # Get students with roll numbers
    students = conn.execute('''
        SELECT student_id, name, roll_number, route_id
        FROM students
        WHERE roll_number IN ('CS001', 'CS002', 'CS003')
        ORDER BY roll_number
    ''').fetchall()
    
    print("Students with CS roll numbers:")
    for student in students:
        route_info = f"Route {student[3]}" if student[3] else "No Route"
        print(f"  Student ID: {student[0]}, Roll: {student[1]}, Name: {student[2]}, {route_info}")
    
    print("\nFor parent login, use Student ID (not Roll Number):")
    print("  - Navya Sri: Student ID = 1")
    print("  - Akhila Reddy: Student ID = 2") 
    print("  - etc.")
    
    conn.close()
    print("\n" + "=" * 50)
    print("Student ID lookup completed!")

if __name__ == '__main__':
    find_student_ids()
