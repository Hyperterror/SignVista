import mediapipe as mp
print(f"✓ MediaPipe version: {mp.__version__}")
if hasattr(mp, 'solutions'):
    print("✓ MediaPipe solutions API available")
else:
    print("❌ MediaPipe solutions not available - trying alternative import")
    try:
        # Some versions need this
        from mediapipe.python.solutions import pose, hands
        print("✓ MediaPipe imported via alternative method")
    except ImportError as e:
        print(f"❌ Alternative import failed: {e}")
