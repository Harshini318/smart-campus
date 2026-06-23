import sqlite3
import os

db_path = 'transit_system.db'
print('Removing student SAI PRUDHVI BODEMPUDI from database...')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check what tables exist
    cursor.execute('SELECT name FROM sqlite_master WHERE type=?', ('table',))
    tables = cursor.fetchall()
    table_names = [t[0] for t in tables]
    print('Available tables: {}'.format(table_names))
    
    if 'students' in table_names:
        # Find the student to delete
        student_name = 'SAI PRUDHVI BODEMPUDI'
        cursor.execute('SELECT student_id, name, roll_number FROM students WHERE name = ?', (student_name,))
        student = cursor.fetchone()
        
        if student:
            print('Found student: ID {}, Name: {}, Roll: {}'.format(student[0], student[1], student[2]))
            
            # Check if student has bus passes
            cursor.execute('SELECT COUNT(*) FROM bus_passes WHERE student_id = ?', (student[0],))
            pass_count = cursor.fetchone()[0]
            
            # Check if student has attendance records
            cursor.execute('SELECT COUNT(*) FROM attendance WHERE student_id = ?', (student[0],))
            attendance_count = cursor.fetchone()[0]
            
            print('Related records:')
            print('  - Bus passes: {}'.format(pass_count))
            print('  - Attendance records: {}'.format(attendance_count))
            
            # Delete related records first
            if pass_count > 0:
                cursor.execute('DELETE FROM bus_passes WHERE student_id = ?', (student[0],))
                print('  - Deleted {} bus pass(es)'.format(pass_count))
            
            if attendance_count > 0:
                cursor.execute('DELETE FROM attendance WHERE student_id = ?', (student[0],))
                print('  - Deleted {} attendance record(s)'.format(attendance_count))
            
            # Delete the student
            cursor.execute('DELETE FROM students WHERE student_id = ?', (student[0],))
            print('  - ✅ Deleted student: {}'.format(student_name))
            
            conn.commit()
            
            print('')
            print('✅ Student {} successfully removed from database!'.format(student_name))
            
            # Show remaining students
            cursor.execute('SELECT student_id, name, roll_number FROM students ORDER BY name')
            remaining_students = cursor.fetchall()
            
            print('')
            print('Remaining students:')
            for s in remaining_students:
                print('  ID {}: {} ({})'.format(s[0], s[1], s[2]))
        else:
            print('❌ Student "{}" not found in database'.format(student_name))
    else:
        print('Students table not found - database needs to be initialized')
    
    conn.close()
else:
    print('Database not found')
