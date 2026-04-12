import cv2
import numpy as np


H = np.array([[0.996, 0.020, -18.5], [-0.018, 1.015, -140.2], [0.000027, 0.000002, 1]])



# KÉPMÉRET (amit mondtál)
width = 1392
height = 512

# 👇 EZT KELL MAJD FINOMÍTANI
src = np.float32([
    [200, 500],   # bal alsó
    [1200, 500],  # jobb alsó
    [600, 300],   # bal felső
    [800, 300]    # jobb felső
])

dst = np.float32([
    [300, 1200],
    [900, 1200],
    [300, 0],
    [900, 0]
])

H = cv2.getPerspectiveTransform(src, dst)

print("H =")
print(H)