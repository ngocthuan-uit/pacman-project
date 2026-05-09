# 👾 Pacman Arcade
<p align="center">
  <img src="https://raw.githubusercontent.com/abozanona/pacman-contribution-graph/main/assets/gifs/red_flip.gif" width="100" />
</p>

> 🎮 Tái hiện trò chơi Pacman huyền thoại với các tính năng mới — nơi 4 con Ghost được trang bị các thuật toán di chuyển riêng biệt (A*, BFS, Dijkstra và DFS) tạo ra những thách thức đa dạng và khó lường. Người chơi không chỉ đơn giản là ăn dot mà còn có thể ghé Black Market để trang bị vũ khí, lên xe phóng nhanh hơn, săn lùng bonus item và tích lũy điểm cao.
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/Pygame-2.0+-green?style=for-the-badge&logo=pygame" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />
</p>

---

## 📋 Yêu cầu hệ thống

- Python 3.10+
- Pygame 2.0+

---

## ⚙️ Cài đặt & Chạy game

**1. Clone repo về máy:**
```bash
git clone https://github.com/ngocthuan-uit/pacman-project.git
cd pacman-project
```

**2. Cài thư viện:**
```bash
pip install -r requirements.txt
```

**3. Chạy game:**
```bash
python main.py
```

---

## 🎮 Điều khiển

| Phím | Chức năng |
|:---:|:---|
| ← → ↑ ↓ hoặc W A S D | Di chuyển Pacman |
| S | Mở Shop (Black Market) từ màn hình Start |
| Q / E / R / T | Trang bị vũ khí (Dagger / Fire / Ice / Axe) |
| Z / X | Trang bị xe (Vespa / Sport Bike) |
| ESC | Quay về màn hình Start |

---

## 🤖 Thuật toán di chuyển cho Ghost

| Ghost | Màu | Thuật toán | Đặc điểm |
|:---:|:---:|:---:|:---|
| 🔴 Blinky | Đỏ         | A* Search | Thông minh nhất, luôn tìm đường ngắn nhất đến Pacman |
| 🩷 Pinky  | Hồng       | BFS       | Tiếp cận 4 ô phía trước Pacman                       |
| 🔵 Inky   | Xanh dương | Dijkstra  | Tiếp cận 2 ô phía sau Pacman                         |
| 🟠 Clyde  | Cam        | DFS       | Khó đoán, đi lòng vòng, ẩn góc khi gần               |

---

## ✨ Tính năng

### 🗺️ Gameplay
- 3 màn chơi với bản đồ và màu sắc khác nhau
- Ăn 80% dot để qua màn
- Power Pellet khiến ma hoảng sợ
- Lưu điểm cao nhất (High Score)

### 🛒 Black Market (Shop)

| Vũ khí | Giá | Hiệu ứng |
|:---|:---:|:---|
| 🗡️ Silver Dagger | 50  | Tăng tốc độ khi powered |
| 🔥 Fire Sword    | 150 | x2 điểm và coin         |
| ❄️ Ice Sword     | 300 | Làm chậm ghost khi sợ   |
| 🪓 Battle Axe    | 500 | +1.5s thời gian power   |

| Xe | Giá | Hiệu ứng |
|:---|:---:|:---|
| 🛵 Vespa      | 400 | +0.5 tốc độ  |
| 🏍️ Sport Bike | 800 | +0.75 tốc độ |

### 🍒 Bonus Items
Cherry · Orange · Apple · Melon · ⭐ Star

---

## 📁 Cấu trúc project

* **algorithms/**: A*, BFS, Dijkstra, DFS
* **assets/**: Âm thanh
* **core/**: Constants, Entity, Map
* **entities/**: Pacman, Ghost
* **maps/**: Level definitions
* **systems/**: Highscore, Player state, Sound
* **ui/**: HUD, Particles, Bonus items
* `game.py`
* `main.py`
