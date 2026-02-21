"""
Test live camera detection with real-time feedback.
Press 'q' to quit.
"""

import cv2
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
)

from ml.inference import initialize_isl_modules, predict_from_raw_frame

print("Initializing ISL modules...")
initialize_isl_modules()
print("Ready! Press 'q' to quit.\n")

# Open camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera")
    sys.exit(1)

frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame")
        break
    
    frame_count += 1
    
    # Only process every 5th frame for performance
    if frame_count % 5 == 0:
        # Get prediction with module details
        word, confidence, status, _, module_details = predict_from_raw_frame(
            session_id="live-test",
            frame=frame,
            return_module_details=True
        )
        
        # Display results
        if word:
            print(f"✅ Detected: {word} (confidence: {confidence:.2f})")
            if module_details:
                print(f"   Module: {module_details.get('selected', {}).get('module', 'unknown')}")
                print(f"   All predictions: {module_details.get('predictions', [])}")
        elif status == "low_confidence":
            if module_details and module_details.get('predictions'):
                print(f"⚠️  Low confidence predictions:")
                for pred in module_details['predictions']:
                    print(f"   - {pred['word']}: {pred['confidence']:.2f}")
        elif status == "no_face":
            print("ℹ️  No face detected")
        
        # Draw on frame
        if word:
            cv2.putText(frame, f"{word} ({confidence:.2f})", (10, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        else:
            cv2.putText(frame, status, (10, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # Show frame
    cv2.imshow('ISL Detection Test', frame)
    
    # Check for quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("\nTest complete!")
