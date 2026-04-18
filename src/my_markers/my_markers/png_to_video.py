import os
import cv2
image_folder = '/home/dominikdzikas/szakdolgozat/evaluation/data/images'
video_name = 'szechenyi_output.mp4'

images = sorted([img for img in os.listdir(image_folder) if img.endswith(".png")])
frame = cv2.imread(os.path.join(image_folder, images[0]))
height, width, layers = frame.shape

# 10 fps, MP4 kódolás
video = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*'mp4v'), 10, (width, height))

for image in images:
    video.write(cv2.imread(os.path.join(image_folder, image)))

video.release()