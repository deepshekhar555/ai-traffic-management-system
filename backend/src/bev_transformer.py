"""
Bird's Eye View (BEV) Orthographic Perspective Transformer
Converts angled camera perspective into top-down 2D spatial coordinates for exact 3D positioning.
"""

import cv2
import numpy as np

import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent.resolve()
backend_dir = Path(__file__).parent.parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from src.logger import logger
except ImportError:
    from backend.src.logger import logger


class BEVTransformer:
    """Transforms 2D image coordinates into top-down Bird's Eye View (BEV) meter coordinates"""
    
    def __init__(self, src_points=None, dst_points=None):
        # Default perspective transformation points for standard 720p traffic camera
        if src_points is None:
            self.src_pts = np.float32([
                [300, 400], [980, 400],   # Top-left, Top-right of road lane
                [100, 700], [1180, 700]   # Bottom-left, Bottom-right of road lane
            ])
        else:
            self.src_pts = np.float32(src_points)
            
        if dst_points is None:
            self.dst_pts = np.float32([
                [200, 0], [440, 0],
                [200, 600], [440, 600]
            ])
        else:
            self.dst_pts = np.float32(dst_points)
            
        # Compute Homography Matrix
        self.H_matrix = cv2.getPerspectiveTransform(self.src_pts, self.dst_pts)
        logger.info("Bird's-Eye-View (BEV) Perspective Transformer initialized successfully!")

    def transform_point(self, point):
        """Transform image (x, y) point to BEV top-down (x_bev, y_bev) in meters"""
        px, py = point
        pt_matrix = np.array([[[px, py]]], dtype=np.float32)
        bev_pt = cv2.perspectiveTransform(pt_matrix, self.H_matrix)
        bev_x, bev_y = bev_pt[0][0]
        
        # Convert pixels to real-world meters relative to intersection origin
        meters_x = round((bev_x - 320) / 20.0, 2)
        meters_y = round((600 - bev_y) / 20.0, 2)
        return (meters_x, meters_y)

    def generate_bev_map(self, frame):
        """Warp full frame into top-down orthographic BEV representation"""
        h, w = frame.shape[:2]
        bev_frame = cv2.warpPerspective(frame, self.H_matrix, (w, h))
        return bev_frame


if __name__ == "__main__":
    bev = BEVTransformer()
    dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    meter_coords = bev.transform_point((640, 500))
    bev_map = bev.generate_bev_map(dummy_frame)
    print(f"[OK] BEVTransformer tested successfully! Camera (640,500) -> BEV Meter Coords: {meter_coords} (Map Shape: {bev_map.shape})")

