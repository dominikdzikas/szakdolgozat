from torch.utils.data import Dataset
from pathlib import Path
import cv2
import numpy as np
import torch
import os

class SegmentationDataset(Dataset):
    def __init__(self, image_list, mask_list,
                 root="/home/dominikdzikas/datasets/road_seg",
                 img_subdir="images", mask_subdir="masks",
                 resize_hw=None, transform=None):
        
        assert len(image_list) == len(mask_list)
        self.img_dir  = Path(root) / img_subdir
        self.msk_dir  = Path(root) / mask_subdir
        self.images   = image_list
        self.masks    = mask_list
        self.resize_hw = resize_hw
        self.transform = transform

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_p  = str(self.img_dir / self.images[idx])
        mask_p = str(self.msk_dir / self.masks[idx])

        img  = cv2.imread(img_p, cv2.IMREAD_COLOR)
        msk  = cv2.imread(mask_p, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise FileNotFoundError(img_p)
        if msk is None:
            raise FileNotFoundError(mask_p)

        # BGR -> RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Opcionális egységesítés
        if self.resize_hw is not None:
            H, W = self.resize_hw
            img = cv2.resize(img, (W, H), interpolation=cv2.INTER_LINEAR)
            msk = cv2.resize(msk, (W, H), interpolation=cv2.INTER_NEAREST)

        # Albumentations (ha használsz)
        if self.transform is not None:
            augmented = self.transform(image=img, mask=msk)
            img = augmented["image"]
            msk = augmented["mask"]

        # Tenzorok: kép float [0..1], maszk float [0/1], csatornával
        if isinstance(img, np.ndarray):
            img = torch.from_numpy(img.transpose(2, 0, 1)).float() / 255.0  # [3,H,W]
        if isinstance(msk, np.ndarray):
            # binarizáljuk 0/1-re, majd [1,H,W]
            if msk.max() > 1:
                msk = (msk > 127).astype(np.uint8)
            msk = torch.from_numpy(msk).float().unsqueeze(0)

        return img, msk
