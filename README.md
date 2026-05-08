# 👾 Pacman Arcade

> Đồ án môn IT003 - Ứng dụng các thuật toán tìm đường trong game Pacman.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green?logo=pygame)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🚀 Cài đặt & Chạy game

```bash
pip install -r requirements.txt
python main.py
```

---

## 🤖 Thuật toán di chuyển cho Ghost

| Ghost | Màu | Thuật toán | Đặc điểm |
|:---:|:---:|:---:|:---|
| 🔴 Blinky | Đỏ         | A* Search | Thông minh nhất, luôn tìm đường ngắn nhất đến Pacman |
| 🩷 Pinky  | Hồng       | BFS       | Đảm bảo đường ngắn nhất, dễ đoán hơn                 |
| 🔵 Inky   | Xanh dương | Dijkstra  | Tiếp cận từ phía sau Pacman                          |
| 🟠 Clyde  | Cam        | DFS       | Khó đoán, đi lòng vòng, ẩn góc khi gần               |

---

## ✨ Tính năng

### 🗺️ Gameplay
- 3 màn chơi với bản đồ và màu sắc khác nhau
- Ăn 80% dot để qua màn
- Power Pellet khiến ma hoảng sợ

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

```markdown
### 📁 Cấu trúc project

* **algorithms/**: A*, BFS, Dijkstra, DFS
* **assets/**: Âm thanh
* **core/**: Constants, Entity, Map
* **entities/**: Pacman, Ghost
* **maps/**: Level definitions
* **systems/**: Highscore, Player state, Sound
* **ui/**: HUD, Particles, Bonus items
* `game.py`
* `main.py`
