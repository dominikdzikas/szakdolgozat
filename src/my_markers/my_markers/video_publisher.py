import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import cv2
from cv_bridge import CvBridge

class VideoPublisher(Node):
    def __init__(self):
        super().__init__("video_publisher")
        
        # 1. Videófájl megnyitása
        self.video_path = "/home/dominikdzikas/szakdolgozat/kitti_output.mp4"
        self.cap = cv2.VideoCapture(self.video_path)
        
        if not self.cap.isOpened():
            self.get_logger().error(f"Nem sikerült megnyitni a videót: {self.video_path}")
            return

        self.bridge = CvBridge()
        self.pub = self.create_publisher(Image, "camera/image_raw", 10)
        
        # KITTI-hez 10 FPS (0.1 mp) az ideális
        self.timer = self.create_timer(0.1, self.publish_frame)

    def publish_frame(self):
        ret, frame = self.cap.read()
        
        if ret:
            resized_frame = cv2.resize(frame, (1392, 512), interpolation=cv2.INTER_AREA)
            # Itt futtathatod a U-Net-et és a BEV-et a 'frame' változón
            msg = self.bridge.cv2_to_imgmsg(resized_frame, encoding='bgr8')
            self.pub.publish(msg)
            # self.get_logger().info("Képkocka publikálva")
        else:
            self.get_logger().info("Videó vége, újraindítás...")
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Visszaugrik az elejére

def main(args=None):
    rclpy.init(args=args)
    node = VideoPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()