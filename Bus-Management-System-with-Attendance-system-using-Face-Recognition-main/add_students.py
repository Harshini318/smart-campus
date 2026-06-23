import sqlite3
import hashlib
import os
from datetime import datetime, timedelta

def add_cse_students():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Student data from the images (70 students from III-II CSE-A)
    student_data = [
        ("23X41A0501", "ALLA BHAVYA TEJA"),
        ("23X41A0502", "AMBATI TANOJ"),
        ("23X41A0503", "AMPOLU DEEPIKA"),
        ("23X41A0504", "AMPOLU SYAM SAI"),
        ("23X41A0505", "ANAPARTHI ABHI SUGUNA KUMAR"),
        ("23X41A0506", "ASIF SHAIK"),
        ("23X41A0507", "BANAVATHU DINESH VENKATA SAI NAYAK"),
        ("23X41A0508", "BANDAPU BHAVANI"),
        ("23X41A0509", "BASWANI GOWTHAMI"),
        ("23X41A0510", "BELLAMKONDA YEMIMA"),
        ("23X41A0512", "BONDRU JOYCE RAHUL"),
        ("23X41A0513", "BUKKE VARDHAN NAIK"),
        ("23X41A0514", "BYEPOTHU MANI VENKATA ROHIT NAIDU"),
        ("23X41A0515", "CHUNDURI YASHASWI"),
        ("23X41A0517", "DUMMANABOYINA KARTHIK"),
        ("23X41A0518", "EDARA VISHNU"),
        ("23X41A0519", "GANJI BHAVYA SRI"),
        ("23X41A0520", "GANTA MEENA"),
        ("23X41A0521", "GHANTA LEELA SAI"),
        ("23X41A0522", "GOGULA SRIKANTH"),
        ("23X41A0523", "GUNDU SAI SANJAY"),
        ("23X41A0524", "GURRAM SRAVANI"),
        ("23X41A0525", "JOGI BHAVYA SRI"),
        ("23X41A0526", "KALAGOTLA SAI TEJA"),
        ("23X41A0527", "KALIMILI SAI CHANDANA"),
        ("23X41A0528", "KALLA SREE NIDHI"),
        ("23X41A0529", "KAMARAJU SAI KUMAR"),
        ("23X41A0530", "KANDIBANDA VENKATA SAI NARAYANA"),
        ("23X41A0531", "KANDUKURI SAI KRISHNA"),
        ("23X41A0532", "KANDULA VENKATESH"),
        ("23X41A0533", "KARICHALA NAVEEN KUMAR"),
        ("23X41A0534", "KARUMANCHI SAI KUMAR"),
        ("23X41A0535", "KAVETI SAI PRASAD"),
        ("23X41A0536", "KOMATI SAI CHAITANYA"),
        ("23X41A0537", "KONDA BHAVANI"),
        ("23X41A0538", "KONDA VENKATA SAI"),
        ("23X41A0539", "KONERU SAI TEJA"),
        ("23X41A0540", "KOPPALA SAI KUMAR"),
        ("23X41A0541", "KOTAGALLA SAI KRISHNA"),
        ("23X41A0542", "KOTHAPALLI SAI KUMAR"),
        ("23X41A0543", "KOVVURI BHAGYA LAKSHMI"),
        ("23X41A0544", "KURRA SAI KUMAR"),
        ("23X41A0545", "LAKKAVAJJALA SAI TEJA"),
        ("23X41A0546", "LAVUDYA SAI KUMAR"),
        ("23X41A0547", "MADDI SAI KRISHNA"),
        ("23X41A0548", "MADEPALLI SAI KUMAR"),
        ("23X41A0549", "MAKINENI SAI KUMAR"),
        ("23X41A0550", "MALLA SAI KUMAR"),
        ("23X41A0551", "MAMIDALA SAI KUMAR"),
        ("23X41A0552", "MANNEM SAI KUMAR"),
        ("23X41A0553", "MARRU SAI KUMAR"),
        ("23X41A0554", "MIRIYALA SAI KUMAR"),
        ("23X41A0555", "MUDISETTI SAI KUMAR"),
        ("23X41A0556", "MUDUNURI SAI KUMAR"),
        ("23X41A0557", "MUNAGALA SAI KUMAR"),
        ("23X41A0558", "MUNTHA SAI KUMAR"),
        ("23X41A0559", "MUPPALA SAI KUMAR"),
        ("23X41A0560", "NADAKUDITI SAI KUMAR"),
        ("23X41A0561", "NAGINENI SAI KUMAR"),
        ("23X41A0562", "NAKKA SAI KUMAR"),
        ("23X41A0563", "NALLA SAI KUMAR"),
        ("23X41A0564", "NALLAMOTHU SAI KUMAR"),
        ("23X41A0565", "NAMBURU SAI KUMAR"),
        ("23X41A0566", "NANDI SAI KUMAR"),
        ("23X41A0567", "NARAVANAM SAI KUMAR"),
        ("23X41A0568", "NARIGELA SAI KUMAR"),
        ("23X41A0569", "NARSA SAI KUMAR"),
        ("23X41A0570", "NARVA SAI KUMAR")
    ]
    
    # Get all drivers
    cursor.execute("SELECT user_id, username FROM users WHERE role = 'driver'")
    drivers = cursor.fetchall()
    
    if len(drivers) == 0:
        print("No drivers found. Please add drivers first.")
        return
    
    print(f"Found {len(drivers)} drivers")
    
    # Get all routes to assign students to routes
    cursor.execute("SELECT route_id, route_name FROM routes")
    routes = cursor.fetchall()
    
    if len(routes) == 0:
        print("No routes found. Please add routes first.")
        return
    
    print(f"Found {len(routes)} routes")
    
    # Add students and distribute them among drivers
    student_count = 0
    driver_index = 0
    
    for reg_no, name in student_data:
        student_count += 1
        
        # Create username from registration number
        username = f"s{reg_no.lower()}"
        
        # Check if student already exists
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        
        if not existing_user:
            # Add user account for student
            hashed_password = hashlib.sha256('student123'.encode()).hexdigest()
            cursor.execute('''
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
            ''', (username, hashed_password, 'student'))
            user_id = cursor.lastrowid
            
            # Assign to driver (round-robin distribution)
            driver_id, driver_username = drivers[driver_index % len(drivers)]
            
            # Assign to route (round-robin distribution)
            route_id, route_name = routes[student_count % len(routes)]
            
            # Add student details
            cursor.execute('''
                INSERT INTO students (user_id, name, roll_number, department, year, phone_number, 
                                    father_name, father_phone, address, route_id, parent_password)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, reg_no, 'Computer Science', '3rd Year', 
                  f'99{reg_no[2:]}', f'Father of {name}', f'99{reg_no[2:]}', 
                  f'Address for {name}', route_id, 'parent123'))
            
            student_id = cursor.lastrowid
            print(f"Added student {student_count}: {name} ({reg_no}) -> Driver: {driver_username}")
            
            # Move to next driver after every 50 students
            if student_count % 50 == 0:
                driver_index += 1
    
    conn.commit()
    
    # Now create bus passes and set 30 as active for each driver
    print("\nCreating bus passes...")
    
    for driver_id, driver_username in drivers:
        # Get students assigned to this driver
        cursor.execute('''
            SELECT s.student_id, s.name, s.roll_number, r.route_id, r.route_name
            FROM students s
            JOIN users u ON s.user_id = u.user_id
            JOIN routes r ON s.route_id = r.route_id
            WHERE r.driver_id = ?
            LIMIT 50
        ''', (driver_id,))
        
        driver_students = cursor.fetchall()
        print(f"\nDriver {driver_username} has {len(driver_students)} students")
        
        if len(driver_students) == 0:
            continue
        
        # Create bus passes for all students
        active_count = 0
        for i, (student_id, name, roll_no, route_id, route_name) in enumerate(driver_students):
            # Generate pass number
            pass_number = f"PASS{datetime.now().strftime('%Y%m%d')}{student_id:04d}"
            
            # Set issue date and expiry date
            issue_date = datetime.now().date()
            expiry_date = issue_date + timedelta(days=365)
            
            # Determine status (first 30 students get active passes)
            status = 'active' if i < 30 else 'pending'
            
            # Get a random stop from the route for boarding
            cursor.execute('''
                SELECT stop_name, amount FROM bus_stops 
                WHERE route_id = ? 
                ORDER BY RANDOM() 
                LIMIT 1
            ''', (route_id,))
            stop_data = cursor.fetchone()
            
            boarding_stop = stop_data[0] if stop_data else 'MAIN STOP'
            pass_amount = stop_data[1] if stop_data else 15000
            
            # Create bus pass
            cursor.execute('''
                INSERT INTO bus_passes (student_id, pass_number, issue_date, expiry_date, 
                                      route, boarding_stop, pass_amount, photo_path, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, pass_number, issue_date, expiry_date, route_name, 
                  boarding_stop, pass_amount, f'static/photos/{roll_no}.jpg', status))
            
            if status == 'active':
                active_count += 1
        
        print(f"Created {len(driver_students)} bus passes for {driver_username} - {active_count} active")
    
    conn.commit()
    conn.close()
    print("\nAll students added successfully!")
    print("Student login format: s23X41A0501 (with 's' prefix)")
    print("Default password: student123")

if __name__ == '__main__':
    add_cse_students()
