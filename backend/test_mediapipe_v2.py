import mediapipe as mp
import sys

print(f"Python: {sys.version}")
print(f"MediaPipe Version: {mp.__version__}")

try:
    if hasattr(mp, 'solutions'):
        print("✓ mp.solutions found")
        if hasattr(mp.solutions, 'holistic'):
            print("✓ mp.solutions.holistic found")
        else:
            print("❌ mp.solutions.holistic NOT found")
    else:
        print("❌ mp.solutions NOT found")
except Exception as e:
    print(f"Error: {e}")

try:
    from mediapipe.python.solutions import holistic as mp_holistic
    print("✓ mediapipe.python.solutions.holistic imported")
except ImportError:
    print("❌ mediapipe.python.solutions.holistic NOT found")
