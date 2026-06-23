import sqlite3
import os

db_path = 'transit_system.db'
print('Finding and deleting specific students...')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check what tables exist
    cursor.execute('SELECT name FROM sqlite_master WHERE type=?', ('table',))
    tables = cursor.fetchall()
    table_names = [t[0] for t in tables]
    print('Available tables: {}'.format(table_names))
    
    if 'students' in table_names:
        # Find the students to delete
        students_to_delete = ['navya sri', 'sai prudhvi bodempudi', 'SAI PRUDHVI BODEMPUDI']
        
        print('Students to delete:')
        for name in students_to_delete:
            print('  - {}'.format(name))
        
        print('')
        print('Searching for these students in database...')
        
        # Find matching students
        deleted_count = 0
        for name in students_to_delete:
            cursor.execute('SELECT student_id, name, roll_number FROM students WHERE name = ?', (name,))
            students = cursor.fetchall()
            
            if students:
                print('')
                print('Found student(s) matching "{}":'.format(name))
                for student in students:
                    print('  ID {}: {} ({})'.format(student[0], student[1], student[2]))
                    
                    # Check if student has bus passes
                    cursor.execute('SELECT COUNT(*) FROM bus_passes WHERE student_id = ?', (student[0],))
                    pass_count = cursor.fetchone()[0]
                    
                    # Check if student has attendance records
                    cursor.execute('SELECT COUNT(*) FROM attendance WHERE student_id = ?', (student[0],))
                    attendance_count = cursor.fetchone()[0]
                    
                    print('    - Bus passes: {}'.format(pass_count))
                    print('    - Attendance records: {}'.format(attendance_count))
                    
                    # Delete related records first
                    if pass_count > 0:
                        cursor.execute('DELETE FROM bus_passes WHERE student_id = ?', (student[0],))
                        print('    - Deleted {} bus pass(es)'.format(pass_count))
                    
                    if attendance_count > 0:
                        cursor.execute('DELETE FROM attendance WHERE student_id = ?', (student[0],))
                        print('    - Deleted {} attendance record(s)'.format(attendance_count))
                    
                    # Delete the student
                    cursor.execute('DELETE FROM students WHERE student_id = ?', (student[0],))
                    print('    - ✅ Deleted student')
                    deleted_count += 1
            else:
                print('  ❌ Student "{}" not found'.format(name))
        
        conn.commit()
        
        print('')
        print('Total students deleted: {}'.format(deleted_count))
        
        # Show remaining students
        cursor.execute('SELECT student_id, name, roll_number, department FROM students ORDER BY name')
        remaining_students = cursor.fetchall()
        
        print('')
        print('Remaining students:')
        for student in remaining_students:
            print('  ID {}: {} ({}) - {}'.format(student[0], student[1], student[2], student[3]))
    else:
        print('Students table not found')
    
    conn.close()
else:
    print('Database not found')
