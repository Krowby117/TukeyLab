import hashlib
from datetime import datetime
from pathlib import Path

# 1. Grab current time
# Use isoformat() for a standardized string representation
current_time = datetime.now().isoformat()

# 2. Hash the time
# Hashing functions require byte-like objects, so we encode the string
time_hash = hashlib.sha256(current_time.encode()).hexdigest()

print(f"Time: {current_time}")
print(f"Hash: {time_hash}")

proj_names = ["bob", "mary", "bob_1"]
name = "anne"
valid: bool = False
index: int = 0
while not valid:
    if index == 0:
        check = name
    else:
        check = name + "_" + str(index)

    if check in proj_names:
        index += 1
    else:
        name = check
        valid = True

print(name)
print(Path(__file__).resolve().parent)