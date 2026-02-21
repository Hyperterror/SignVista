import mediapipe as mp
import sys

print(f"Python version: {sys.version}")
try:
    print(f"✓ MediaPipe version: {mp.__version__}")
    if hasattr(mp, 'solutions'):
        print("✓ MediaPipe solutions API available")
        print(f"  Available solutions: {dir(mp.solutions)}")
    else:
        print("❌ MediaPipe solutions not available - trying alternative import")
        # Some versions need this
        from mediapipe.python.solutions import pose, hands
        print("✓ MediaPipe imported via alternative method")
except Exception as e:
    print(f"❌ Error during MediaPipe diagnostic: {e}")
    import traceback
    traceback.print_exc()
