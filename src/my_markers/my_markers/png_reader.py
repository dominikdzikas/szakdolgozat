#!/usr/bin/env python3
import os
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import numpy as np
import cv2
from cv_bridge import CvBridge

class PngReader(Node):
    def __init__(self):
        super().__init__("image_publisher")
        img_path = "/home/dominikdzikas/datasets/road_seg/images/5f697884-87beee07.jpg"
        self.png_image = cv2.imread(img_path, cv2.IMREAD_COLOR)
        if self.png_image is None:
            self.get_logger().error(f'Nem sikerült beolvasni a képet: {img_path}')
            raise FileNotFoundError(img_path)
        self.bridge = CvBridge()
        self.pub = self.create_publisher(Image, "camera/image_raw", 10)
        self.timer = self.create_timer(1.0/5.0, self.publish_png)


    def publish_png(self):
        self.get_logger().info(f'PNG töltve')
        msg = self.bridge.cv2_to_imgmsg(self.png_image, encoding='bgr8')
        msg.header.frame_id = 'camera_link'
        self.pub.publish(msg)

    def transform_img(self):
        frame = cv2.resize(self.png_image, (850, 638))

        tl = (200, 400)
        tr = (400, 400)
        bl = (200, 600)
        br = (400, 600)
        
        cv2.circle(frame, tl, 5, (0,0,255), -1)
        cv2.circle(frame, tr, 5, (0,0,255), -1)
        cv2.circle(frame, bl, 5, (0,0,255), -1)
        cv2.circle(frame, br, 5, (0,0,255), -1)

        new_image = frame
        return new_image


def main(args=None):
    rclpy.init(args=args)
    node = PngReader()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()



if __name__ == "__main__":
    main()