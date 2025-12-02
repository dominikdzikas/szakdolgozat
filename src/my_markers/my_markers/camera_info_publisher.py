#!/usr/bin/env python3
import rclpy, yaml
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo


class CameraInfoPublisher(Node):
    def __init__(self, yaml_path):
        super().__init__('camera_info_publisher')
        self.publisher = self.create_publisher(CameraInfo, '/camera/camera_info', 10)
        with open(yaml_path, 'r') as f:
            calib = yaml.safe_load(f)

        msg = CameraInfo()
        msg.width = calib['image_width']
        msg.height = calib['image_height']
        msg.k = calib['camera_matrix']['data']
        msg.d = calib['distortion_coefficients']['data']
        msg.r = calib['rectification_matrix']['data']
        msg.p = calib['projection_matrix']['data']
        msg.distortion_model = calib['distortion_model']
        msg.header.frame_id = 'camera_link'
        self.msg = msg

        self.timer = self.create_timer(0.1, self._tick)
        self.counter = 0

    def _tick(self):
        self.msg.header.stamp = self.get_clock().now().to_msg()
        self.publisher.publish(self.msg)


def main(args=None):
    rclpy.init(args=args)
    node = CameraInfoPublisher('/Users/dominikdzikas/ros2_ws/src/my_markers/config/my_cam.yaml')
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
