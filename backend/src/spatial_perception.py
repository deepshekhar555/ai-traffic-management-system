"""Calibrated, camera-agnostic spatial perception for an intersection.

This module turns 2D detections into a shared ego-centric (metre) coordinate
frame, merges overlapping camera observations, and maintains stable world IDs.
It is intentionally sensor-optional: a LiDAR range can be supplied when an
edge sensor is available, otherwise a calibrated ground-plane homography is
used.  Camera calibration must be replaced with site measurements before a
production deployment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple
import time

import cv2
import numpy as np


@dataclass
class _WorldTrack:
    world_id: int
    position_m: np.ndarray
    class_name: str
    last_seen: float
    source_track_id: Optional[int] = None


class SpatialPerceptionEngine:
    """Fuse calibrated camera detections into persistent world objects."""

    def __init__(self, camera_homographies: Optional[Dict[str, Iterable]] = None,
                 merge_distance_m: float = 2.5, track_timeout_s: float = 2.0):
        self.homographies = {
            name: np.asarray(matrix, dtype=np.float32)
            for name, matrix in (camera_homographies or {}).items()
        }
        self.merge_distance_m = float(merge_distance_m)
        self.track_timeout_s = float(track_timeout_s)
        self._tracks: Dict[int, _WorldTrack] = {}
        self._next_world_id = 1

    def set_camera_calibration(self, camera_id: str, image_points, world_points) -> None:
        """Set a ground-plane mapping from four or more image/world point pairs."""
        if len(image_points) < 4 or len(world_points) < 4:
            raise ValueError("At least four image and world calibration points are required")
        matrix, _ = cv2.findHomography(np.float32(image_points), np.float32(world_points))
        if matrix is None:
            raise ValueError("Could not compute a valid camera homography")
        self.homographies[camera_id] = matrix.astype(np.float32)

    def image_to_world(self, camera_id: str, image_point: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        matrix = self.homographies.get(camera_id)
        if matrix is None:
            return None
        result = cv2.perspectiveTransform(np.float32([[[image_point[0], image_point[1]]]]), matrix)[0][0]
        if not np.isfinite(result).all():
            return None
        return round(float(result[0]), 2), round(float(result[1]), 2)

    @staticmethod
    def _footpoint(detection: dict) -> Tuple[float, float]:
        x1, y1, x2, y2 = detection["bbox"]
        return (float(x1 + x2) / 2.0, float(y2))

    def _remove_stale_tracks(self, now: float) -> None:
        self._tracks = {key: track for key, track in self._tracks.items()
                        if now - track.last_seen <= self.track_timeout_s}

    def update(self, observations: Iterable[dict], now: Optional[float] = None) -> List[dict]:
        """Merge observations and return one ego-world object per real object.

        Each observation needs ``camera_id`` and ``bbox``. Optional
        ``track_id``, ``class_name``, ``confidence`` and ``lidar_position_m``
        are preserved. LiDAR positions take precedence over camera projection.
        """
        now = time.monotonic() if now is None else float(now)
        self._remove_stale_tracks(now)
        candidates = []
        for observation in observations:
            pos = observation.get("lidar_position_m")
            if pos is None:
                pos = self.image_to_world(observation.get("camera_id", "default"), self._footpoint(observation))
            if pos is None:
                continue  # never invent world positions from uncalibrated video
            item = dict(observation)
            item["world_position_m"] = (float(pos[0]), float(pos[1]))
            candidates.append(item)

        # Associate detections to current world tracks. A source tracker ID is
        # preferred; distance matching handles overlapping camera views.
        # A track may accept observations from several cameras in one sync
        # window, but never two detections from the same camera. That prevents
        # nearby same-view vehicles being accidentally collapsed.
        observed_cameras_by_track = {}
        output_by_world_id = {}
        for item in sorted(candidates, key=lambda x: x.get("confidence", 0.0), reverse=True):
            position = np.asarray(item["world_position_m"], dtype=float)
            source_id = item.get("track_id")
            class_name = item.get("class_name", "vehicle")
            camera_id = item.get("camera_id", "default")
            matches = [track for track in self._tracks.values()
                       if camera_id not in observed_cameras_by_track.get(track.world_id, set())
                       and track.class_name == class_name
                       and ((source_id is not None and source_id == track.source_track_id) or
                            np.linalg.norm(position - track.position_m) <= self.merge_distance_m)]
            if matches:
                track = min(matches, key=lambda t: np.linalg.norm(position - t.position_m))
                track.position_m = (track.position_m + position) / 2.0
                track.last_seen = now
                track.source_track_id = source_id if source_id is not None else track.source_track_id
            else:
                track = _WorldTrack(self._next_world_id, position, class_name, now, source_id)
                self._tracks[track.world_id] = track
                self._next_world_id += 1
            observed_cameras_by_track.setdefault(track.world_id, set()).add(camera_id)
            item["world_id"] = track.world_id
            item["world_position_m"] = tuple(round(float(v), 2) for v in track.position_m)
            # A higher-confidence observation wins the representative metadata,
            # while the position above is the fused position from all cameras.
            previous = output_by_world_id.get(track.world_id)
            if previous is None or item.get("confidence", 0.0) > previous.get("confidence", 0.0):
                output_by_world_id[track.world_id] = item
        return list(output_by_world_id.values())

    def status(self) -> dict:
        return {"active_world_objects": len(self._tracks), "calibrated_cameras": sorted(self.homographies)}
