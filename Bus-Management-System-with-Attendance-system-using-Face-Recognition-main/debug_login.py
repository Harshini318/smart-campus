import sqlite3
import hashlib

# Test the exact login logic
conn = sqlite3.connect('transit_system.db')
user = conn.execute('SELECT * FROM users WHERE username = ?', ('driver1',)).fetchone()

if user:
    stored_password = user[2]  # password is at index 2
    test_password = 'driver123'
    
    # Current logic (wrong) - this is what's in the code now
    try:
        # This will fail because user['password'] doesn't work on tuple
        current_logic = hashlib.sha256(user['password'].encode()).hexdigest() == user['password']
    except:
        current_logic = "ERROR - user['password'] doesn't work on tuple"
    
    # Correct logic
    correct_logic = hashlib.sha256(test_password.encode()).hexdigest() == stored_password
    
    print(f'Driver1 Debug:')
    print(f'  Stored password: {stored_password}')
    print(f'  Test password: {test_password}')
    print(f'  Current logic result: {current_logic}')
    print(f'  Correct logic result: {correct_logic}')
    
    # Show the correct hash
    correct_hash = hashlib.sha256(test_password.encode()).hexdigest()
    print(f'  Correct hash: {correct_hash}')
    print(f'  Hashes match: {correct_hash == stored_password}')
else:
    print('Driver1 not found')

conn.close()
