#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import numpy as np
import cv2

class RectifyNode(Node):
    def __init__(self):
        super().__init__('rectify_node')

        # Paraméterek (bemenet/kimenet topicok)
        self.declare_parameter('image_in',  '/camera/image_raw')
        self.declare_parameter('info_in',   '/camera/camera_info')
        self.declare_parameter('image_out', '/camera/image_rect')
        self.declare_parameter('info_out',  '/camera/camera_info')  # maradhat ugyanaz a név

        img_in  = self.get_parameter('image_in').value
        info_in = self.get_parameter('info_in').value
        self.image_out_name = self.get_parameter('image_out').value
        self.info_out_name  = self.get_parameter('info_out').value

        # Pub/Sub
        self.bridge = CvBridge()
        self.pub_img = self.create_publisher(Image, self.image_out_name, 10)
        self.pub_info = self.create_publisher(CameraInfo, self.info_out_name, 10)
        self.sub_info = self.create_subscription(CameraInfo, info_in, self.info_cb, 10)
        self.sub_img  = self.create_subscription(Image, img_in,  self.image_cb, 10)

        # Állapot: kalibráció + rect map
        self.have_maps = False
        self.K = None
        self.D = None
        self.R = np.eye(3, dtype=np.float64)  # alapból nincs extra rect rotáció
        self.P = None
        self.newK = None
        self.map1 = None
        self.map2 = None
        self.image_size = None  # (w,h)

        self.get_logger().info(f"Rectify node listening: {img_in} + {info_in}")

    def info_cb(self, msg: CameraInfo):
        # Kalibrációs adatok beolvasása
        K = np.array(msg.k, dtype=np.float64).reshape(3,3)
        D = np.array(msg.d, dtype=np.float64).reshape(-1,)

        # Képméret
        w = int(msg.width)
        h = int(msg.height)
        size = (w, h)

        # Változás esetén térkék újraszám,olása 
        need_recompute = (
            self.K is None or
            self.D is None or
            self.image_size != size
        )

        self.K, self.D = K, D
        self.image_size = size

        if need_recompute:
            # Új kamera-mátrix a min/max kihasználásra
            self.newK, _ = cv2.getOptimalNewCameraMatrix(self.K, self.D, size, alpha=0)
            # Rectify map előállítása
            self.map1, self.map2 = cv2.initUndistortRectifyMap(
                self.K, self.D, self.R, self.newK, size, cv2.CV_16SC2
            )
            self.have_maps = True
            self.get_logger().info("Rectify maps (re)computed.")

            # Projection matrix P
            self.P = np.zeros((3,4), dtype=np.float64)
            self.P[:3,:3] = self.newK

        # Frissített CameraInfo publikálása
        out_info = CameraInfo()
        out_info.header = msg.header
        out_info.width  = w
        out_info.height = h
        out_info.distortion_model = 'plumb_bob'
        out_info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        out_info.k = self.newK.flatten().tolist() if self.newK is not None else msg.k
        out_info.r = np.eye(3, dtype=np.float64).flatten().tolist()
        out_info.p = self.P.flatten().tolist() if self.P is not None else msg.p

        self.pub_info.publish(out_info)

    def image_cb(self, msg: Image):
        if not self.have_maps:
            return  # várunk a CameraInfo-ra
        img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        rect = cv2.remap(img, self.map1, self.map2, interpolation=cv2.INTER_LINEAR)
        out = self.bridge.cv2_to_imgmsg(rect, encoding='bgr8')
        out.header = msg.header
        self.pub_img.publish(out)

def main():
    rclpy.init()
    node = RectifyNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
