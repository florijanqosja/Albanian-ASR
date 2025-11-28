import os
import sys

# The path we are trying to access
target_file = "videoplaybackmp4_19.338-40.08.wav"
target_dir = "/code/splices/Sample_Perrala"
path = os.path.join(target_dir, target_file)

print(f"--- Debugging File Access ---")
print(f"Target Path: {path}")
print(f"Current User UID: {os.getuid()}")
print(f"Current Group GID: {os.getgid()}")

if os.path.exists(path):
    print(f"[OK] File exists")
    print(f"Size: {os.path.getsize(path)} bytes")
    stat = os.stat(path)
    print(f"Permissions: {oct(stat.st_mode)}")
    print(f"Owner UID: {stat.st_uid}")
    print(f"Owner GID: {stat.st_gid}")
    
    try:
        with open(path, "rb") as f:
            print("[OK] File is readable")
            data = f.read(10)
            print(f"First 10 bytes: {data}")
    except Exception as e:
        print(f"[ERROR] Error reading file: {e}")
else:
    print(f"[ERROR] File does not exist")
    
    print(f"Checking directory: {target_dir}")
    if os.path.exists(target_dir):
        print(f"[OK] Directory exists")
        try:
            files = os.listdir(target_dir)
            print(f"Files in directory ({len(files)}):")
            for f in files:
                print(f" - {f}")
        except Exception as e:
            print(f"[ERROR] Error listing directory: {e}")
    else:
        print(f"[ERROR] Directory does not exist")
        print(f"Listing /code/splices:")
        try:
            print(os.listdir("/code/splices"))
        except Exception as e:
            print(f"Error listing /code/splices: {e}")
