import os, time, cv2, torch
from torch import nn, optim
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from model import UNet
from dataset import SegmentationDataset

def dice_loss(pred, target, smooth=1.0):
    pred = torch.sigmoid(pred)
    
    pred = pred.view(pred.size(0), -1)
    target = target.view(target.size(0), -1)

    intersection = (pred * target).sum(dim=1)
    dice = (2. * intersection + smooth) / (pred.sum(dim=1) + target.sum(dim=1) + smooth)
    
    return 1 - dice.mean()

def dice_score(pred, target, threshold=0.5):
    pred = (torch.sigmoid(pred) > threshold).float()
    
    pred = pred.view(pred.size(0), -1)
    target = target.view(target.size(0), -1)

    intersection = (pred * target).sum(dim=1)
    dice = (2. * intersection) / (pred.sum(dim=1) + target.sum(dim=1) + 1e-8)
    
    return dice.mean()

# gyors I/O és cuDNN autotune
cv2.setNumThreads(0)
torch.backends.cudnn.benchmark = True

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("device:", device)

# modell, loss, opt
model = UNet(n_ch=3, n_classes=1).to(device)
# opcionális: channels_last kis gyorsulás
model = model.to(memory_format=torch.channels_last)
criterion = nn.BCEWithLogitsLoss()
optimizer = optim.Adam(model.parameters(), lr=3e-4)

# fájlok
root = "/home/dominikdzikas/datasets/road_seg"
image_paths = sorted(os.listdir(os.path.join(root, "images")))
mask_paths  = sorted(os.listdir(os.path.join(root, "masks")))

# (biztonságosabb a stem-párosítás, de most maradhat így)
train_imgs, val_imgs, train_masks, val_masks = train_test_split(
    image_paths, mask_paths, test_size=0.2, random_state=42
)

# datasetek (ha szeretnél 512x512-t: resize_hw=(512,512))
train_dataset = SegmentationDataset(train_imgs, train_masks, root=root, resize_hw=None)
val_dataset   = SegmentationDataset(val_imgs,   val_masks,   root=root, resize_hw=None)

# dataloader
num_workers = 4
train_loader = DataLoader(
    train_dataset, batch_size=4, shuffle=True,
    num_workers=num_workers, pin_memory=True,
    persistent_workers=True, prefetch_factor=4
)
val_loader = DataLoader(
    val_dataset, batch_size=2, shuffle=False,
    num_workers=num_workers, pin_memory=True,
    persistent_workers=True, prefetch_factor=4
)

# AMP (új API!)
scaler = torch.amp.GradScaler("cuda")

epochs = 50
best_loss = float("inf")
best_dice = 0.0
patience, trigger = 10, 0

try:
    for epoch in range(1, epochs+1):
        t0 = time.time()
        model.train()
        train_loss = 0.0
        train_dice = 0.0
        val_dice = 0.0

        pbar = tqdm(train_loader, desc=f"Epoch {epoch}/{epochs}")
        for imgs, masks in pbar:
            # H2D + channels_last
            imgs  = imgs.to(device, non_blocking=True).to(memory_format=torch.channels_last)
            masks = masks.to(device, non_blocking=True)  # [B,1,H,W] float – a Dataset már így adja

            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda"):
                preds = model(imgs)         # [B,1,H,W]
                loss  = criterion(preds, masks) + dice_loss(preds, masks)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            train_loss += loss.item()
            train_dice += dice_score(preds, masks).item()
            pbar.set_postfix(train_loss=loss.item())
        print("Train epoch finished, starting validation...")
        # validáció
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for imgs, masks in val_loader:
                imgs  = imgs.to(device, non_blocking=True).to(memory_format=torch.channels_last)
                masks = masks.to(device, non_blocking=True)  # [B,1,H,W] float
                with torch.amp.autocast("cuda"):
                    preds = model(imgs)
                    loss  = criterion(preds, masks) + dice_loss(preds, masks)
                val_loss += loss.item()
                val_dice += dice_score(preds, masks).item()
        print("Validation finished.")
        train_loss /= max(1, len(train_loader))
        train_dice /= len(train_loader)
        val_loss   /= max(1, len(val_loader))
        val_dice /= len(val_loader)
        dt = time.time() - t0
        print(f"Epoch {epoch:02d} | Train: {train_loss:.4f} | Val: {val_loss:.4f} | {dt:.1f}s")
        print(f"Train Dice: {train_dice:.4f} | Val Dice: {val_dice:.4f}")

        # mentés loss alapján
        if val_loss < best_loss:
            best_loss = val_loss
            torch.save(model.state_dict(), "best_loss_bce_dice.pth")

        # mentés + early stopping dice alapján
        if val_dice > best_dice:
            best_dice = val_dice
            torch.save(model.state_dict(), "best_dice_bce_dice.pth")
            trigger = 0
        else:
            trigger += 1
            if trigger >= patience:
                print("Early stopping triggered.")
                break
        
        

except KeyboardInterrupt:
    print("\nMegszakítva (Ctrl+C) - checkpoint mentése…")
    torch.save(model.state_dict(), "interrupt_checkpoint.pth")
    raise
