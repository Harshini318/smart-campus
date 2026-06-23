import sqlite3
import hashlib
import os

def add_new_route():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_system.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First, add the driver
    driver_username = 'm_samba_siva_rao'
    driver_password = 'driver123'  # Default password
    driver_phone = '9948752556'
    driver_name = 'M. SAMBA SIVA RAO'
    
    # Check if driver already exists
    cursor.execute("SELECT user_id FROM users WHERE username = ?", (driver_username,))
    existing_driver = cursor.fetchone()
    
    if not existing_driver:
        # Add driver with hashed password
        hashed_password = hashlib.sha256(driver_password.encode()).hexdigest()
        cursor.execute('''
            INSERT INTO users (username, password, role, phone_number)
            VALUES (?, ?, ?, ?)
        ''', (driver_username, hashed_password, 'driver', driver_phone))
        driver_id = cursor.lastrowid
        print(f"Added new driver: {driver_name} (ID: {driver_id})")
    else:
        driver_id = existing_driver[0]
        print(f"Using existing driver: {driver_name} (ID: {driver_id})")
    
    # Add the route
    route_name = 'TENALI TO VIJAYA COLLEGE ROUTE'
    start_point = 'TENALI'
    end_point = 'VIJAYA COLLEGE'
    stops_summary = 'TENALI, KATIVARAM, NANDIVELUGU, DUGGIRALA, MORAMPUDI, THUMMAPUDI, REVENDRA PADU, VADLAPUDI, MANGALAGIRI, MANIPAL HOSPITAL, SRK COLLEGE, VIJAYA COLLEGE'
    
    # Check if route already exists
    cursor.execute("SELECT route_id FROM routes WHERE route_name = ?", (route_name,))
    existing_route = cursor.fetchone()
    
    if not existing_route:
        cursor.execute('''
            INSERT INTO routes (route_name, start_point, end_point, stops, driver_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (route_name, start_point, end_point, stops_summary, driver_id))
        route_id = cursor.lastrowid
        print(f"Added new route: {route_name} (ID: {route_id})")
    else:
        route_id = existing_route[0]
        print(f"Using existing route: {route_name} (ID: {route_id})")
    
    # Add all the bus stops with times and amounts
    bus_stops = [
        ('TENALI', '07:20', 20000, 1),
        ('KATIVARAM', '07:25', 19500, 2),
        ('NANDIVELUGU', '07:30', 19200, 3),
        ('DUGGIRALA', '07:35', 19000, 4),
        ('MORAMPUDI', '07:40', 18500, 5),
        ('THUMMAPUDI', '07:45', 18000, 6),
        ('REVENDRA PADU', '07:48', 17500, 7),
        ('VADLAPUDI', '07:50', 17000, 8),
        ('MANGALAGIRI', '08:00', 16500, 9),
        ('MANIPAL HOSPITAL', '08:10', 16000, 10),
        ('SRK COLLEGE', '08:30', 15500, 11),
        ('VIJAYA COLLEGE', '08:35', 15000, 12)
    ]
    
    # Remove existing stops for this route if any
    cursor.execute("DELETE FROM bus_stops WHERE route_id = ?", (route_id,))
    
    # Add new stops
    for stop_name, stop_time, amount, stop_order in bus_stops:
        cursor.execute('''
            INSERT INTO bus_stops (route_id, stop_name, stop_time, amount, stop_order)
            VALUES (?, ?, ?, ?, ?)
        ''', (route_id, stop_name, stop_time, amount, stop_order))
        print(f"Added stop: {stop_name} at {stop_time} - Amount: {amount}")
    
    conn.commit()
    conn.close()
    print("\nRoute and driver added successfully!")
    print(f"Driver login: Username: {driver_username}, Password: {driver_password}")

if __name__ == '__main__':
    add_new_route()
