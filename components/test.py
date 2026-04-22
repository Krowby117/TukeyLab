import hashlib
from datetime import datetime

# 1. Grab current time
# Use isoformat() for a standardized string representation
current_time = datetime.now().isoformat()

# 2. Hash the time
# Hashing functions require byte-like objects, so we encode the string
time_hash = hashlib.sha256(current_time.encode()).hexdigest()

print(f"Time: {current_time}")
print(f"Hash: {time_hash}")
