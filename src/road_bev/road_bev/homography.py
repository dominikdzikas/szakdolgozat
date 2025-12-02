import cv2, numpy as np, yaml, sys, os

img_path = "/home/dominikdzikas/datasets/road_seg/images/5f697884-87beee07.jpg"
dst_W, dst_H = 720, 480   # BEV kimenet (szabadon állítható)

img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
assert img is not None, f"Nem olvasható: {img_path}"

pts = []
win = "Kattints 4 pontra (BL, BR, TR, TL)"
cv2.namedWindow(win)

def on_click(event,x,y,flags,param):
    if event == cv2.EVENT_LBUTTONDOWN:
        pts.append([x,y])
        vis = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        for i,p in enumerate(pts): cv2.circle(vis, tuple(p), 6, (0,0,255), -1)
        cv2.imshow(win, vis)

cv2.setMouseCallback(win, on_click)
cv2.imshow(win, img); cv2.waitKey(0)
cv2.destroyAllWindows()

if len(pts) != 4:
    raise SystemExit("4 pont kell (bal-alsó, jobb-alsó, jobb-felső, bal-felső)")

src = np.float32(pts)                     # BL, BR, TR, TL
dst = np.float32([[0,dst_H-1],[dst_W-1,dst_H-1],[dst_W-1,0],[0,0]])

H = cv2.getPerspectiveTransform(src, dst)  # 3x3, float64
bev = cv2.warpPerspective(img, H, (dst_W, dst_H), flags=cv2.INTER_NEAREST)

# mentés
params = {"H": H.reshape(-1).tolist(), "bev_width": int(dst_W), "bev_height": int(dst_H)}
with open("/home/dominikdzikas/szakdolgozat/src/road_bev/config/bev.yaml", "w") as f: yaml.safe_dump(params, f)
cv2.imwrite("bev_preview.png", bev)

print("H (row-major):", H.reshape(-1).tolist())
print("Mentve: bev.yaml, bev_preview.png")
