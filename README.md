# CNN-alapú vezethető útfelület meghatározása ROS 2-ben

Ez a repository a BSc szakdolgozatomhoz készült:

**Konvolúciós neurális háló-alapú vezethető útfelület meghatározása ROS 2-ben**

A projekt célja a **vezethető útfelület detektálása kameraképekből**, majd az eredmény **Bird’s-Eye View (felülnézeti nézet)** transzformációja és vizualizálása **RViz 2-ben**.

---

## 🚀 Áttekintés

A rendszer egy ROS 2 alapú, moduláris feldolgozási pipeline, amely ötvözi:

- számítógépes látás (OpenCV)
- mélytanulás (U-Net, PyTorch)
- robotikai middleware (ROS 2)
- valós idejű vizualizáció (RViz 2)

A projekt egy egyszerű autonóm jármű érzékelési pipeline működését modellezi.

---

## 🧠 Feldolgozási lánc

```text
/camera/image_raw
        ↓
[seg_node]  (CNN - U-Net)
        ↓
/road/mask_cnn
        ↓
[bev_node]  (perspektíva transzformáció)
        ↓
/road/bev_mask
        ↓
[marker_node]
        ↓
RViz 2 vizualizáció
```
---

## ⚙️ Komponensek

- **seg_node**  
  U-Net alapú neurális háló segítségével meghatározza az útfelületet a bemeneti képen.

- **bev_node**  
  A szegmentált maszkot felülnézeti nézetbe transzformálja homográfia segítségével (`cv2.warpPerspective`).

- **marker_node**  
  A BEV maszkból vizualizációs elemeket (MarkerArray) generál RViz számára.

- **png_reader / image source**  
  Teszteléshez biztosít bemeneti képet.

---

## 📂 Projekt struktúra
```
src/
├── road_seg/        # CNN alapú szegmentáció
├── road_bev/        # BEV transzformáció
├── my_markers/      # vizualizáció és segéd node-ok
├── road_launch/     # launch fájlok
training/            # tanításhoz szükséges kódok
```

---

## 📡 Topicok

### Bemenet
- `/camera/image_raw`

### Köztes eredmény
- `/road/mask_cnn`

### Kimenet
- `/road/bev_mask`

---

## ⚙️ Követelmények

- Ubuntu 22.04
- ROS 2 Humble
- Python 3
- PyTorch
- OpenCV
- cv_bridge
- RViz 2

---

## 🛠️ Build

```bash
cd ~
git clone https://github.com/dominikdzikas/szakdolgozat.git

cd ~/szakdolgozat
colcon build --symlink-install

source /opt/ros/humble/setup.bash
source install/setup.bash
```
---

## ▶️ Futtatás

```bash
ros2 launch road_launch full_pipeline.launch.py
```
Ez elindítja a teljes pipeline-t, beleértve a vizualizációt RViz-ben.

---

## 🧪 Modell

A szegmentáció egy U-Net architektúrán alapuló neurális hálóval történik.
- bináris szegmentáció (út / nem út)
- PyTorch implementáció
- előre betanított modell betöltése futás közben

---

## 🗺️ BEV transzformáció

A felülnézeti nézet egy homográfia mátrix segítségével készül:
`cv2.warpPerspective(...)`
A konfiguráció tartalmazza:
- homográfia mátrix(H)
- kimeneti kép mérete

---

## 🏋️ Tanítás
A training/ mappa tartalmazza:

- adatelőkészítést
- tanító scriptet
- modell definíciót
- kiértékelést

### Alkalmazott módszerek

- **Binary Cross-Entropy (BCE) loss**  
  A pixel szintű bináris osztályozás optimalizálására.

- **Dice loss**  
  A szegmentáció minőségének javítására, különösen az osztályok közötti egyensúlytalanság esetén.

- **Adam optimalizálás**  
  A modell súlyainak hatékony frissítésére adaptív tanulási rátával.

- **Checkpoint mentés**  
  A tanítás során a legjobb modell súlyainak elmentése a későbbi kiértékeléshez és inferenciához.

---

## 📊 Felhasználás

A projekt egy autonóm jármű érzékelési modulját modellezi:

- útfelület detektálás
- jelenetértelmezés
- felülnézeti vetítés
- vizualizáció debug célokra

---

## 🔮 Továbbfejlesztési lehetőségek
- valós idejű kamera integráció
- kvantitatív kiértékelés (pl. LiDAR referencia)
- modell optimalizálás
- pontosabb kalibráció
- szenzorfúzió

---

## 👨‍🎓 Szakdolgozati kontextus

A projekt a szakdolgozatom részeként készült, amelynek fő témái:

- mélytanulás képfeldolgozásban
- ROS 2 alapú rendszerek
- autonóm járművek érzékelése

---

## 👤 Szerző

Dzikas Dominik
https://github.com/dominikdzikas

---

## ⚠️ Megjegyzések
- Egyes fájlok (modell, konfiguráció, bemenet) lokális beállítást igényelhetnek
- A projekt elsősorban kutatási és demonstrációs célokat szolgál
