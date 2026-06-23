import sqlite3
import os

def debug_student_data():
    """Debug student data structure"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    
    print("Debugging Student Data Structure")
    print("=" * 50)
    
    # Check table schema
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(students)")
    columns = cursor.fetchall()
    
    print("Students table columns:")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")
    
    conn.close()

if __name__ == '__main__':
    debug_student_data()
