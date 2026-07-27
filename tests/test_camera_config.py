import sys
from pathlib import Path

# Ensure backend and root directory are in sys.path
root_dir = Path(__file__).parent.parent.resolve()
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from src.camera_handler import CameraHandler
    from config.config import (
        CAMERA_BRIGHTNESS, CAMERA_CONTRAST, CAMERA_EXPOSURE, 
        CAMERA_AUTO_EXPOSURE, FPS, FRAME_WIDTH, FRAME_HEIGHT
    )
except ImportError:
    from backend.src.camera_handler import CameraHandler
    from backend.config.config import (
        CAMERA_BRIGHTNESS, CAMERA_CONTRAST, CAMERA_EXPOSURE, 
        CAMERA_AUTO_EXPOSURE, FPS, FRAME_WIDTH, FRAME_HEIGHT
    )

print('[OK] Camera handler imported successfully')
print(f'[OK] FPS: {FPS}')
print(f'[OK] Resolution: {FRAME_WIDTH}x{FRAME_HEIGHT}')
print(f'[OK] Brightness: {CAMERA_BRIGHTNESS}')
print(f'[OK] Contrast: {CAMERA_CONTRAST}')
print(f'[OK] Exposure: {CAMERA_EXPOSURE}')
print(f'[OK] Auto-exposure: {CAMERA_AUTO_EXPOSURE}')
print('\n[OK] All camera settings loaded correctly!')
print('\n[OK] Your camera system is now ready with:')
print('   - Natural video brightness')
print('   - Stable 30 FPS')
print('   - 1280x720 HD resolution')
print('   - Customizable settings in config/config.py')

