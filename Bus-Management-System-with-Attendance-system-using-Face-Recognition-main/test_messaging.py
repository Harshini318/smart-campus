import sqlite3
import os
from datetime import datetime

def test_attendance_messaging():
    """Test the attendance messaging system"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    
    # Import the messaging function from main app
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from bus_pass_app import send_attendance_message_to_parent
        
        # Get a sample student with parent phone
        student = conn.execute('''
            SELECT s.student_id, s.name, s.father_phone, r.route_name
            FROM students s
            JOIN routes r ON s.route_id = r.route_id
            WHERE s.father_phone IS NOT NULL AND s.father_phone != ''
            LIMIT 5
        ''').fetchall()
        
        print("Testing attendance messaging system...")
        print("=" * 50)
        
        for i, (student_id, name, phone, route_name) in enumerate(student, 1):
            print(f"\nTest {i}: {name}")
            print(f"Parent Phone: {phone}")
            print(f"Route: {route_name}")
            
            # Test boarding message
            current_time = datetime.now().strftime('%H:%M:%S')
            success = send_attendance_message_to_parent(
                student_id, name, current_time, route_name, 'boarding'
            )
            
            if success:
                print("✅ Boarding message sent successfully")
            else:
                print("❌ Failed to send boarding message")
            
            # Test drop-off message
            success = send_attendance_message_to_parent(
                student_id, name, current_time, route_name, 'drop_off'
            )
            
            if success:
                print("✅ Drop-off message sent successfully")
            else:
                print("❌ Failed to send drop-off message")
        
        print("\n" + "=" * 50)
        print("Testing completed!")
        
        # Check messages in database
        messages = conn.execute('''
            SELECT m.message, m.sender_type, m.created_at, s.name as student_name
            FROM driver_parent_messages m
            JOIN students s ON m.student_id = s.student_id
            WHERE m.sender_type = 'system'
            ORDER BY m.created_at DESC
            LIMIT 10
        ''').fetchall()
        
        print(f"\nRecent system messages in database ({len(messages)}):")
        for msg in messages:
            print(f"- {msg[3]}: {msg[0][:50]}...")
        
    except ImportError as e:
        print(f"Error importing messaging function: {e}")
        print("Make sure the bus_pass_app.py is in the same directory")
    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    test_attendance_messaging()
