# 👾 Pacman Arcade

<p align="center">
  <img src="https://raw.githubusercontent.com/abozanona/pacman-contribution-graph/main/assets/gifs/red_flip.gif" width="100" />
</p>

> 🎮 A reimagining of the legendary Pacman arcade game with a modern twist — where 4 ghosts are each armed with their own distinct pathfinding algorithm (A\*, BFS, Dijkstra and DFS), creating diverse and unpredictable challenges. Players don't just eat dots — they can drop by the Black Market to gear up with weapons, hop on a faster ride, hunt down bonus items, and chase the highest score. And when they reach Level 3, a crown-wearing Boss awaits — faster, smarter, and not going down without a fight.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/Pygame-2.0+-green?style=for-the-badge&logo=pygame" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />
</p>

---

## 🎬 Demo

🎥 [Watch on YouTube](https://www.youtube.com/watch?v=qP3iutrt5wo)

---

## 📋 Requirements

- Python 3.10+
- Pygame 2.0+

---

## ⚙️ Installation & Running

**1. Clone the repository:**
```bash
git clone https://github.com/ngocthuan-uit/pacman-project.git
cd pacman-project
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Run the game:**
```bash
python main.py
```

---

## 🎮 Controls

| Key | Action |
|:---:|:---|
| ← → ↑ ↓ or W A S D | Move Pacman |
| S | Open Shop (Black Market) from the Start screen |
| Q / E / R / T | Equip weapon (Dagger / Fire / Ice / Axe) |
| Z / X | Equip vehicle (Vespa / Sport Bike) |
| ESC | Return to Start screen |

---

## 👻 Ghost AI Algorithms

| Ghost | Colour | Algorithm | Behaviour |
| :--- | :--- | :--- | :--- |
| 🔴 **Blinky** | Red | A* Search | Smartest ghost — always finds the shortest path directly to Pacman |
| 💗 **Pinky** | Pink | BFS | Ambushes by targeting 4 tiles ahead of Pacman's current direction |
| 🔵 **Inky** | Cyan | Dijkstra | Flanks from behind by targeting 2 tiles behind Pacman |
| 🟠 **Clyde** | Orange | DFS | Unpredictable — wanders and retreats to corners when close to Pacman |

---

## ✨ Features

### 🗺️ Gameplay

- 3 levels with distinct map layouts and colour themes
- Eat 80% of dots to advance to the next level
- Power Pellets send ghosts into frightened mode
- Persistent high score saved to disk

### 👹 Level 3 Boss — MegaGhost

A crown-wearing boss that spawns at the start of Level 3 alongside the four regular ghosts.

| State | Behaviour |
|:---|:---|
| **Chasing** | Uses A\* with free U-turns — finds the true shortest path to Pacman |
| **Fleeing** | When Pacman is powered, boss sprints to the furthest map corner — Pacman must actively chase it |
| **Stunned** | After taking a hit: frozen for 1.5 s, flickers grey — contact does not cost a life |
| **Enraged** | Speed increases each time HP drops: HP3 → 2.0, HP2 → 2.5, HP1 → 3.0 |

**How to defeat the boss:**
1. Eat a Power Pellet — boss immediately starts fleeing.
2. Chase and collide with the boss → **HP −1**, boss stunned 1.5 s, all 4 ghosts instantly lose frightened state.
3. Escape the revived ghosts, find another Power Pellet, repeat.
4. Three hits → boss defeated → **+500 coins, +1000 score → WIN**.

**Win condition (Level 3):** defeat the boss **OR** eat 80% of dots — whichever comes first.

### 🛒 Black Market (Shop)

Press **S** on the Start screen to spend coins on weapons and vehicles.

| Weapon | Cost | Effect |
|:---|:---:|:---|
| 🗡️ Silver Dagger | 50 | Increases Pacman speed while powered |
| 🔥 Fire Sword | 150 | ×2 points and coins from ghosts and bonus items |
| ❄️ Ice Sword | 300 | Slows frightened ghosts to half speed |
| 🪓 Battle Axe | 500 | +1.5 s to Power Pellet duration |

| Vehicle | Cost | Effect |
|:---|:---:|:---|
| 🛵 Vespa | 400 | +0.5 base speed |
| 🏍️ Sport Bike | 800 | +0.75 base speed |

> Equip or unequip items mid-game with **Q / E / R / T** (weapons) and **Z / X** (vehicles).

### 🍒 Bonus Items

Random bonus collectibles appear on the map during gameplay.

Cherry · Orange · Apple · Melon · ⭐ Star

Higher levels unlock rarer, higher-value items. Fire Sword doubles their point and coin rewards.

---

## 📁 Project Structure

```
pacman-project/
├── algorithms/       # Ghost AI: A*, BFS, Dijkstra, DFS
├── assets/           # Sound effects
├── core/             # Constants, Entity base class, Map
├── entities/         # Pacman, Ghost, MegaGhost (Boss)
├── maps/             # Level matrix definitions
├── systems/          # High score, Player state, Sound manager
├── ui/               # HUD, Floating text, Particles, Bonus items
├── game.py           # Main game controller (FSM, update, draw)
└── main.py           # Entry point
```
