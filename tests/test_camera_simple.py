"""Simple camera test"""
import cv2
import sys
import time

print("Testing camera access...")

for camera_id in range(5):
    print(f"\nTrying camera device: {camera_id}")
    cap = cv2.VideoCapture(camera_id)
    
    if cap.isOpened():
        print(f"[OK] Camera {camera_id} opened successfully!")
        
        # Try to read a frame
        ret, frame = cap.read()
        if ret:
            print(f"[OK] Successfully read frame from camera {camera_id}")
            print(f"  Frame shape: {frame.shape}")
            
            # Check if frame is Iriun virtual camera black placeholder image
            mean_val = frame.mean()
            if mean_val < 15.0:
                print(f"  [INFO] Camera {camera_id} is Iriun virtual placeholder (Black/Inactive screen). Scanning next camera...")
                cap.release()
                continue

            # Try to display active camera frame
            cv2.imshow(f"Camera {camera_id}", frame)
            print("[OK] Frame displayed (press any key to continue)")
            cv2.waitKey(1000)
            cv2.destroyAllWindows()
            cap.release()
            break
        else:
            print(f"[X] Failed to read frame from camera {camera_id}")
        
        cap.release()
    else:
        print(f"[X] Camera {camera_id} not available")

else:
    print("\n[INFO] Checking DroidCam IP Stream (http://10.42.231.28:4747/video)...")
    cap_ip = cv2.VideoCapture("http://10.42.231.28:4747/video")
    if cap_ip.isOpened():
        ret, frame = cap_ip.read()
        if ret:
            print("[OK] Successfully connected to DroidCam IP stream!")
            cv2.imshow("DroidCam Stream", frame)
            cv2.waitKey(1000)
            cv2.destroyAllWindows()
        cap_ip.release()
    else:
        print("\n[X] No active physical webcam devices found!")

print("\nCamera test completed successfully!")

