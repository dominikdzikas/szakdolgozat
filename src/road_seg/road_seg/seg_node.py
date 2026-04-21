#!/usr/bin/env python3

import time
from pathlib import Path

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Header
from cv_bridge import CvBridge
import numpy as np
import cv2
import torch

from .model import UNet


class CNNSegNode(Node):
    def __init__(self):
        super().__init__("seg_node")

        self.declare_parameter("model_path", "")
        self.model_path = Path(self.get_parameter("model_path").value)

        if str(self.model_path) == "":
            self.get_logger().error("A 'model_path' paraméter nincs megadva.")
            raise RuntimeError("Missing required parameter: model_path")

        if not self.model_path.is_file():
            self.get_logger().error(f"A modellfájl nem található: {self.model_path}")
            raise FileNotFoundError(str(self.model_path))
        
        self.input_topic = '/camera/image_raw'
        self.mask_topic = '/road/mask_cnn'
        self.overlay_topic = '/road/mask_overlay'
        self.threshold = 0.5
        self.resize_h, self.resize_w = 720, 1280
        self.frame_count = 0
        self.device = torch.device('cuda' if torch.cuda.is_available else 'cpu')
        self.get_logger().info(f"Device: {self.device}")

        self.model = UNet(3, 1)
        self.model.to(self.device, memory_format=torch.channels_last)
        state = torch.load(self.model_path, map_location=self.device)
        self.model.load_state_dict(state)
        self.model.eval()
        torch.set_grad_enabled(False)
        torch.backends.cudnn.benchmark = True

        self.bridge = CvBridge()

        self.sub = self.create_subscription(Image, self.input_topic, self.callback, 10)
        self.pub_mask = self.create_publisher(Image, self.mask_topic, 10)
        self.pub_overlay = self.create_publisher(Image, self.overlay_topic, 10)

        self.last_t = time.time()
        self.frame_count = 0

    def callback(self, msg: Image):
        cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        h0, w0 = cv_img.shape[:2]
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (self.resize_w, self.resize_h), interpolation=cv2.INTER_LINEAR)
        x = torch.from_numpy(rgb.transpose(2, 0, 1)).unsqueeze(0)/255.0
        x = x.to(self.device, memory_format=torch.channels_last)

        preds = self.model(x)
        probs = torch.sigmoid(preds)[0, 0]
        mask = (probs > self.threshold).to(torch.uint8).cpu().numpy() * 255
        mask = cv2.resize(mask, (w0, h0), interpolation=cv2.INTER_NEAREST)

        mask_msg = self.bridge.cv2_to_imgmsg(mask, encoding="mono8")
        mask_msg.header = Header()
        mask_msg.header.stamp = msg.header.stamp
        mask_msg.header.frame_id = msg.header.frame_id or "camera_link"
        self.pub_mask.publish(mask_msg)

        color_mask = cv2.applyColorMap(mask, cv2.COLORMAP_JET)
        overlay = cv2.addWeighted(cv_img, 1.0, color_mask, 0.4, 0)
        overlay_msg = self.bridge.cv2_to_imgmsg(overlay, encoding="bgr8")
        overlay_msg.header = mask_msg.header
        self.pub_overlay.publish(overlay_msg)

        self.frame_count += 1
        if self.frame_count % 30 == 0:
            now = time.time()
            fps = 30.0 / (now - self.last_t + 1e-6)
            self.get_logger().info(f"Inference FPS ~ {fps:.1f}")
            self.last_t = now


def main():
    rclpy.init()
    node = CNNSegNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()