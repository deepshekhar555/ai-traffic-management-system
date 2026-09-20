"""Hilti 2023 construction-site SLAM dataset adapter for ROS-style pipelines.

This module models the real-world handheld LiDAR + IMU challenge described by the
Hilti SLAM dataset: construction sites, no wheel odometry, sloped floors,
underground parking, and millimeter ground truth. The implementation is kept
lightweight and deterministic so it can be used from the existing Flask backend
without requiring a full ROS installation in the local environment.
"""

from __future__ import annotations

from typing import Dict, List


class HiltiRosSLAMDataset:
    """High-fidelity dataset metadata and synthetic ROS-ready trajectory."""

    def __init__(self, dataset_name: str = "Hilti 2023 Benchmark Dataset"):
        self.dataset_name = dataset_name
        self.dataset_url = "https://www.hilti-challenge.com/dataset-2023.html"

    def get_sensor_summary(self) -> Dict[str, object]:
        return {
            "platform": "Phasma handheld mapping rig",
            "lidar": {
                "model": "Hesai PandarXT-32",
                "channels": 32,
                "scan_rate_hz": 10,
                "scan_type": "360deg LiDAR",
            },
            "cameras": {
                "count": 5,
                "model": "Alphasense Core",
                "purpose": "visual context, not required for LiDAR-IMU SLAM",
            },
            "imu": {
                "type": "industrial-grade IMU",
                "time_alignment_ms": 1,
                "sampling_rate_hz": 200,
            },
            "ground_truth": {
                "method": "surveyed control points",
                "accuracy": "millimeter-level",
                "note": "ATE and map quality are meaningful because the ground truth is highly accurate",
            },
            "environments": [
                "new multi-storey construction site",
                "underground renovation parking lot",
                "handheld motion with jerk and slope variation",
            ],
            "challenge": "no wheel odometry, no GNSS indoors, sloped floors and staircases",
        }

    def get_ros_runtime(self) -> Dict[str, object]:
        return {
            "runtime": "ROS 2 / ROS bag compatible",
            "framework": "LiDAR + IMU odometry and map optimization",
            "topics": [
                "/points_raw",
                "/imu/data",
                "/camera/front/image_raw",
                "/camera/left/image_raw",
                "/camera/right/image_raw",
                "/tf",
                "/odometry/filtered",
                "/map",
            ],
            "time_sync_ms": 1,
            "odometry_mode": "handheld SLAM / lidar-imu pipeline",
            "no_gnss": True,
            "sensor_fusion": ["LiDAR", "IMU", "optional camera context"],
        }

    def generate_trajectory_points(self) -> List[Dict[str, float]]:
        """Create a deterministic trajectory that resembles handheld motion on a real site.

        The values are intentionally realistic: x,y,z in meters, yaw/pitch/roll in degrees,
        and a small but variable speed profile that captures walking motion and slight
        acceleration changes, without relying on external ROS bags or heavy slam assets.
        """
        samples = [
            {"timestamp_s": 0.0, "x_m": 0.0, "y_m": 0.0, "z_m": 0.0, "roll_deg": 0.0, "pitch_deg": 0.0, "yaw_deg": 0.0, "speed_mps": 0.0},
            {"timestamp_s": 1.0, "x_m": 1.6, "y_m": 0.4, "z_m": 0.05, "roll_deg": 0.8, "pitch_deg": 1.2, "yaw_deg": 12.5, "speed_mps": 1.3},
            {"timestamp_s": 2.0, "x_m": 3.4, "y_m": 0.9, "z_m": 0.09, "roll_deg": 1.3, "pitch_deg": 1.8, "yaw_deg": 21.1, "speed_mps": 1.6},
            {"timestamp_s": 3.0, "x_m": 5.2, "y_m": 1.3, "z_m": 0.11, "roll_deg": 2.0, "pitch_deg": 2.5, "yaw_deg": 31.4, "speed_mps": 1.7},
            {"timestamp_s": 4.0, "x_m": 7.1, "y_m": 1.9, "z_m": 0.18, "roll_deg": 2.8, "pitch_deg": 3.2, "yaw_deg": 48.6, "speed_mps": 1.8},
            {"timestamp_s": 5.0, "x_m": 9.0, "y_m": 2.8, "z_m": 0.22, "roll_deg": 3.1, "pitch_deg": 3.8, "yaw_deg": 64.2, "speed_mps": 1.9},
            {"timestamp_s": 6.0, "x_m": 10.6, "y_m": 3.6, "z_m": 0.29, "roll_deg": 2.9, "pitch_deg": 4.1, "yaw_deg": 80.6, "speed_mps": 1.7},
            {"timestamp_s": 7.0, "x_m": 12.1, "y_m": 4.2, "z_m": 0.36, "roll_deg": 2.5, "pitch_deg": 4.5, "yaw_deg": 96.3, "speed_mps": 1.5},
            {"timestamp_s": 8.0, "x_m": 13.7, "y_m": 4.7, "z_m": 0.41, "roll_deg": 2.2, "pitch_deg": 4.8, "yaw_deg": 114.1, "speed_mps": 1.6},
            {"timestamp_s": 9.0, "x_m": 15.3, "y_m": 5.0, "z_m": 0.48, "roll_deg": 1.8, "pitch_deg": 5.1, "yaw_deg": 129.4, "speed_mps": 1.4},
        ]
        return samples

    def build_payload(self) -> Dict[str, object]:
        return {
            "dataset_name": self.dataset_name,
            "dataset_url": self.dataset_url,
            "description": "Handheld LiDAR + IMU SLAM for real construction-site mapping with millimeter ground truth.",
            "sensor_summary": self.get_sensor_summary(),
            "ros_runtime": self.get_ros_runtime(),
            "trajectory_points": self.generate_trajectory_points(),
            "key_challenges": [
                "jerky handheld motion",
                "no wheel odometry",
                "sloped construction floors",
                "staircases and multi-level geometry",
                "indoor no-GNSS operation",
                "LiDAR-IMU fusion required for stable mapping",
            ],
            "recommended_ros_pipeline": [
                "bag playback with /points_raw and /imu/data",
                "lidar_imu_odometry node",
                "map optimization and loop closure",
                "trajectory evaluation against surveyed control points",
            ],
        }
