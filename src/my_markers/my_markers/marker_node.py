#!/usr/bin/env python3
# cnn_bev_marker_node.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
from cv_bridge import CvBridge
import numpy as np
import cv2
import time


class CNNBEVMarkerNode(Node):
    def __init__(self):
        super().__init__("cnn_bev_marker_node")

        #FIX BEÁLLÍTÁSOK (igény szerint állíthatod)
        self.input_topic   = "/road/bev_mask"     # mono8 BEV maszk
        self.output_topic  = "/road/bev_markers"  # RViz MarkerArray
        self.frame_id      = "base_link"          # RViz frame
        self.min_area_px   = 800                 # kontúr-szűrés (pix)
        self.approx_eps_px = 3.0                 # Douglas-Peucker epsilon
        # px méter skála a BEV-en
        self.METERS_PER_PX_X = 0.01
        self.METERS_PER_PX_Y = 0.01
        self.X_OFFSET_M = 5.0
        self.Y_OFFSET_M = -5.0
        self.SCALE = 0.85   # 2x nagyobb méretű BEV-hez (opcionális)
        self.bridge = CvBridge()
        self.pub = self.create_publisher(MarkerArray, self.output_topic, 10)
        self.sub = self.create_subscription(Image, self.input_topic, self.callback, 10)

        self.marker_ns = "bev_contours"
        self.get_logger().info("cnn_bev_marker_node elindult")
        self.get_logger().info(f"Input:  {self.input_topic}")
        self.get_logger().info(f"Output: {self.output_topic} (MarkerArray)")

        self.last_ts = time.time()
        self.seq = 0

    #BEV pixel -> 2D világ (m) (origó: alul-közép; +Y előre, +X jobbra) ---
    

    def pix_to_xy(self, u, v, W, H):
        x = ((u - (W / 2.0)) * self.METERS_PER_PX_X) * self.SCALE + self.X_OFFSET_M
        y = ((H - 1 - v) * self.METERS_PER_PX_Y) * self.SCALE + self.Y_OFFSET_M
        return x, y

    def callback(self, msg: Image):
        try:
            # ROS → OpenCV (mono8)
            bev = self.bridge.imgmsg_to_cv2(msg, desired_encoding="mono8")
            H, W = bev.shape[:2]

            # Kontúrok kinyerése
            _, binm = cv2.threshold(bev, 127, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(binm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # MarkerArray előkészítés
            marr = MarkerArray()
            now = self.get_clock().now().to_msg()

            # Kontúrok szűrése és poligon approximáció
            marker_id = 0
            for cnt in contours:
                area = float(cv2.contourArea(cnt))
                if area < self.min_area_px:
                    continue

                # simítás / ritkítás
                eps = self.approx_eps_px
                cnt_approx = cv2.approxPolyDP(cnt, eps, True)  # (N,1,2)

                if len(cnt_approx) < 3:
                    continue

                # 5) Marker (LINE_STRIP) létrehozása
                m = Marker()
                m.header.frame_id = self.frame_id
                m.header.stamp = msg.header.stamp
                m.ns = self.marker_ns
                m.id = marker_id
                m.type = Marker.LINE_STRIP
                m.action = Marker.ADD

                # vonalvastagság (m)
                m.scale.x = 0.10

                # szín (RGBA)
                m.color.r = 1.0
                m.color.g = 0.2
                m.color.b = 0.0
                m.color.a = 1.0

                # z magasság (talaj síkja)
                z = 0.01

                # kontúr pontok → világ koordináta (m) → Marker pontok
                pts = []
                for p in cnt_approx.reshape(-1, 2):
                    u, v = float(p[0]), float(p[1])
                    x, y = self.pix_to_xy(u, v, W, H)
                    pt = Point()
                    pt.x = x
                    pt.y = y
                    pt.z = z
                    pts.append(pt)

                # zárjuk a poligont
                if pts and (pts[0].x != pts[-1].x or pts[0].y != pts[-1].y):
                    pts.append(pts[0])

                m.points = pts
                m.lifetime = rclpy.duration.Duration(seconds=0.2).to_msg()  # kicsi életidő frissítéshez

                marr.markers.append(m)
                marker_id += 1

            # 6) Törlő marker, ha kevesebb marker van, mint korábban
            self.pub.publish(marr)

            # 7) FPS log (ritkán)
            self.seq += 1
            if self.seq % 30 == 0:
                t = time.time()
                fps = 30.0 / max(t - self.last_ts, 1e-6)
                self.get_logger().info(f"Markers published: {len(marr.markers)} | FPS ~ {fps:.1f}")
                self.last_ts = t

        except Exception as e:
            self.get_logger().error(f"marker callback error: {repr(e)}")


def main():
    rclpy.init()
    node = CNNBEVMarkerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
