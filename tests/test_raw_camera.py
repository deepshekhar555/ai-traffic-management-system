"""Test to display raw camera feed without processing"""
import cv2
import sys

print("Opening raw camera feed test...")

cap = None
for idx in [2, 1, 0]:
    c = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
    if not c.isOpened():
        c = cv2.VideoCapture(idx)
    if c.isOpened():
        r, f = c.read()
        if r and f is not None and f.mean() > 15.0:
            cap = c
            print(f"Connected to camera index {idx}")
            break
        c.release()

if cap is None or not cap.isOpened():
    print("Failed to open camera!")
    sys.exit(1)


print("Camera opened. Press 'q' to quit")

frame_count = 0
while True:
    ret, frame = cap.read()
    
    if not ret:
        print("Failed to read frame")
        break
    
    frame_count += 1
    
    # Add text to frame
    cv2.putText(frame, f"Frame: {frame_count}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Display
    cv2.imshow("Raw Camera Feed", frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

print(f"Total frames: {frame_count}")
cap.release()
cv2.destroyAllWindows()
print("Test completed")
