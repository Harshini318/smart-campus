import sqlite3
from werkzeug.security import check_password_hash

# Test driver1 login
conn = sqlite3.connect('transit_system.db')
user = conn.execute('SELECT * FROM users WHERE username = ?', ('driver1',)).fetchone()

if user:
    stored_password = user['password']
    test_password = 'driver123'
    is_valid = check_password_hash(stored_password, test_password)
    print(f'Driver1 Login Test:')
    print(f'  Stored hash: {stored_password}')
    print(f'  Test password: {test_password}')
    print(f'  Password valid: {is_valid}')
else:
    print('Driver1 not found')

conn.close()
