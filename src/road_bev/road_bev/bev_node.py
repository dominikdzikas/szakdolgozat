#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import yaml
import os


class BEVNode(Node):
    def __init__(self):
        super().__init__('bev_node')

        self.input_topic = "/road/mask_cnn"
        self.output_topic = "/road/bev_mask"
        self.param_file = "/home/dominikdzikas/szakdolgozat/src/road_bev/config/bev.yaml"

        self.bridge = CvBridge()

        if not os.path.exists(self.param_file):
            self.get_logger().error(f"BEV paraméterfájl nem található: {self.param_file}")
            rclpy.shutdown()
            return

        with open(self.param_file, 'r') as f:
            params = yaml.safe_load(f)

        # Kamera és homográfia paraméterek
        self.h_matrix = np.array(params["H"]).reshape((3, 3))
        self.bev_width = params["bev_width"]
        self.bev_height = params["bev_height"]

        # Publisher & Subscriber
        self.pub = self.create_publisher(Image, self.output_topic, 10)
        self.sub = self.create_subscription(Image, self.input_topic, self.callback, 10)

        self.get_logger().info("BEV Node elindult")
        self.get_logger().info(f"Input: {self.input_topic}")
        self.get_logger().info(f"Output: {self.output_topic}")

    def callback(self, msg: Image):
        try:
            mask = self.bridge.imgmsg_to_cv2(msg, desired_encoding="mono8")

            bev = cv2.warpPerspective(
                mask,
                self.h_matrix,
                (self.bev_width, self.bev_height),
                flags=cv2.INTER_NEAREST
            )

            bev = cv2.rotate(bev, cv2.ROTATE_90_CLOCKWISE)

            bev_msg = self.bridge.cv2_to_imgmsg(bev, encoding="mono8")
            bev_msg.header = msg.header
            self.pub.publish(bev_msg)

        except Exception as e:
            self.get_logger().error(f"BEV callback error: {repr(e)}")


def main(args=None):
    rclpy.init(args=args)
    node = BEVNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
