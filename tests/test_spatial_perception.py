import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from src.spatial_perception import SpatialPerceptionEngine


def test_calibrated_cameras_merge_duplicate_and_keep_world_id():
    engine = SpatialPerceptionEngine(merge_distance_m=1.5)
    image = [(0, 0), (100, 0), (100, 100), (0, 100)]
    engine.set_camera_calibration("north", image, image)
    engine.set_camera_calibration("east", image, image)
    result = engine.update([
        {"camera_id": "north", "bbox": (40, 30, 60, 50), "class_name": "car", "confidence": .9},
        {"camera_id": "east", "bbox": (41, 30, 61, 50), "class_name": "car", "confidence": .8},
    ], now=1.0)
    assert len(result) == 1
    again = engine.update([
        {"camera_id": "north", "bbox": (41, 31, 61, 51), "class_name": "car", "confidence": .9}
    ], now=1.1)
    assert again[0]["world_id"] == result[0]["world_id"]


def test_uncalibrated_camera_is_not_assigned_a_fake_position():
    engine = SpatialPerceptionEngine()
    assert engine.update([{"camera_id": "unknown", "bbox": (0, 0, 10, 10)}]) == []
