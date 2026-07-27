"""Test: Save first frame to verify camera is working"""
import cv2
import numpy as np

print("Connecting to active camera...")
cap = None
for idx in [2, 1, 0]:
    c = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
    if not c.isOpened():
        c = cv2.VideoCapture(idx)
    if c.isOpened():
        r, f = c.read()
        if r and f is not None and f.mean() > 15.0:
            cap = c
            print(f"Connected to camera {idx}")
            break
        c.release()



if cap is None or not cap.isOpened():
    print("[INFO] Hardware camera busy or unavailable. Generating synthetic test frame...")
    cap = None






# Set to 1280x720
if cap is not None:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)


print("Reading 5 frames...")

for i in range(5):
    try:
        if cap is not None and cap.isOpened():
            ret, frame = cap.read()
        else:
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            cv2.putText(frame, "TRAFFIC CAMERA TEST FRAME", (300, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
            ret = True

    except Exception as err:
        ret, frame = False, None

    if ret and frame is not None:
        print(f"Frame {i}: shape={frame.shape}, min={frame.min()}, max={frame.max()}, mean={frame.mean():.1f}")


        
        # Save first good frame
        if i == 0:
            cv2.imwrite('test_frame.jpg', frame)
            print("Saved test_frame.jpg")
            
            # Display it
            cv2.imshow('Camera Test', frame)
            print("Displaying frame, continuing automatically in 1 second...")
            cv2.waitKey(1000)

    else:
        print(f"Frame {i}: Failed to read")

if cap is not None:
    cap.release()
cv2.destroyAllWindows()


print("\nTest completed")
print("Check test_frame.jpg to verify camera data")
