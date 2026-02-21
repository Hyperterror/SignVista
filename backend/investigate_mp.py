import mediapipe as mp
import os
import sys

print(f"Python: {sys.version}")
print(f"MP Path: {mp.__path__}")

for p in mp.__path__:
    if os.path.exists(p):
        print(f"\nListing {p}:")
        for item in os.listdir(p):
            item_path = os.path.join(p, item)
            suffix = "/" if os.path.isdir(item_path) else ""
            print(f"  {item}{suffix}")
            if item == "python":
                print(f"    FOUND PYTHON SUBDIR: {os.listdir(item_path)}")
    else:
        print(f"\nPath does not exist: {p}")
