import sqlite3

conn = sqlite3.connect('transit_system.db')
cursor = conn.cursor()

# Check all driver usernames
cursor.execute('SELECT user_id, username, role FROM users WHERE role = ?', ('driver',))
drivers = cursor.fetchall()
print('Available Driver Accounts:')
for driver in drivers:
    print(f'  User ID {driver[0]}: "{driver[1]}" ({driver[2]})')

# Check if 'drier1' exists
cursor.execute('SELECT * FROM users WHERE username = ?', ('drier1',))
drier1_check = cursor.fetchone()
print(f'\nCheck for "drier1": {"Exists" if drier1_check else "Does not exist"}')

# Check if 'driver1' exists
cursor.execute('SELECT * FROM users WHERE username = ?', ('driver1',))
driver1_check = cursor.fetchone()
print(f'Check for "driver1": {"Exists" if driver1_check else "Does not exist"}')

conn.close()
