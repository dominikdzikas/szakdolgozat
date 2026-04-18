import numpy as np
from pathlib import Path

import rclpy
from rclpy.node import Node

from std_msgs.msg import Header
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2


INPUT_DIR = Path.home() / "szakdolgozat" / "evaluation" / "data" / "lidar_fused"

# ROI
X_MIN = 0.0
X_MAX = 30.0
Y_MIN = -10.0
Y_MAX = 10.0

# ground z tartomány
Z_MIN = -2.2
Z_MAX = -1.0

FRAME_ID = "base_link"   # vagy lidar_link, ami nálad helyes
FPS = 10.0


class GroundTruthPlayer(Node):
    def __init__(self):
        super().__init__("ground_truth_player")

        self.pub = self.create_publisher(PointCloud2, "/ground_truth_cloud", 10)

        self.files = sorted(INPUT_DIR.glob("*.npz"))
        if not self.files:
            self.get_logger().error(f"Nincs .npz fájl itt: {INPUT_DIR}")
            self.index = 0
            return

        self.index = 0
        self.timer = self.create_timer(1.0 / FPS, self.publish_next_frame)
        self.get_logger().info(f"{len(self.files)} frame betöltve.")

    def load_points(self, path: Path) -> np.ndarray:
        data = np.load(path)

        # igazítsd a saját fájlstruktúrádhoz
        if "points" in data:
            pts = data["points"]
        else:
            # ha csak egy tömb van benne
            key = list(data.keys())[0]
            pts = data[key]

        return pts

    def ground_filter(self, pts: np.ndarray) -> np.ndarray:
        # ha intenzitás is van, csak az első 3 oszlop kell
        xyz = pts[:, :3]

        mask = (
            (xyz[:, 0] >= X_MIN) & (xyz[:, 0] <= X_MAX) &
            (xyz[:, 1] >= Y_MIN) & (xyz[:, 1] <= Y_MAX) &
            (xyz[:, 2] >= Z_MIN) & (xyz[:, 2] <= Z_MAX)
        )
        return xyz[mask].astype(np.float32)

    def publish_next_frame(self):
        if not self.files:
            return

        path = self.files[self.index]
        pts = self.load_points(path)
        ground_pts = self.ground_filter(pts)

        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = FRAME_ID

        msg = point_cloud2.create_cloud_xyz32(header, ground_pts.tolist())
        self.pub.publish(msg)

        self.get_logger().info(
            f"[{self.index + 1}/{len(self.files)}] {path.name} | ground pts: {len(ground_pts)}"
        )

        self.index += 1
        if self.index >= len(self.files):
            self.index = 0   # loop


def main():
    rclpy.init()
    node = GroundTruthPlayer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()