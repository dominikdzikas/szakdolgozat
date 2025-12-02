#!/usr/bin/env python3
import os
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import numpy as np
import cv2
from cv_bridge import CvBridge


class Camera_callibration(Node):
    def __init__(self):
        super().__init__("camera_publisher")
        time_period = 1.0/30.0
        self.cap = cv2.VideoCapture(2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        if not self.cap.isOpened():
            self.get_logger().error("Nem tudtam megnyitni a kamerát.")
        self.br = CvBridge()
        self.pub = self.create_publisher(Image, "/camera/image_raw", 10)
        self.timer = self.create_timer(time_period, self.timer_callback)


    def timer_callback(self):
        ret, frame = self.cap.read()
        if ret == True:
            self.pub.publish(self.cv2_to_ros(frame))
        self.get_logger().info(f'video megy')

    def cv2_to_ros(self, img):
        if img.ndim == 2:
            enc = 'mono8'
        elif img.ndim == 3 and img.shape[2] == 3:
            enc = 'bgr8'   # OpenCV alap
        elif img.ndim == 3 and img.shape[2] == 4:
            enc = 'bgra8'
        else:
            raise ValueError(f"Ismeretlen képforma: shape={img.shape}, dtype={img.dtype}")
        return self.br.cv2_to_imgmsg(img, encoding=enc)
        


def main(args=None):
    rclpy.init(args=args)
    node = Camera_callibration()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()



if __name__ == "__main__":
    main()