import hashlib
from werkzeug.security import generate_password_hash

# Test if both methods produce same hash
password = 'driver123'
hashlib_hash = hashlib.sha256(password.encode()).hexdigest()
werkzeug_hash = generate_password_hash(password)

print(f'Password: {password}')
print(f'hashlib.sha256: {hashlib_hash}')
print(f'werkzeug.security: {werkzeug_hash}')
print(f'Same result: {hashlib_hash == werkzeug_hash}')
