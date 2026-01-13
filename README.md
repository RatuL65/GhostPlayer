# GhostPlayer 👻
**Control your music without breaking your flow.**

![Version](https://img.shields.io/badge/version-2.1-cyan) ![Platform](https://img.shields.io/badge/platform-Windows-blue)

## 🛑 The Problem
Every time you `Alt + Tab` to skip a song, you lose focus. Context switching is the silent killer of productivity for engineers and developers.

## 💡 The Solution
**GhostPlayer** is a "stealth-mode" desktop widget that floats over your workspace (IDE, CAD, PDF). It connects directly to Windows Media Controls to manage Spotify, YouTube Music, or VLC without you ever leaving your active window.

## ✨ Key Features
* **Dynamic Stealth Mode:** Fades to 60% opacity when idle; wakes up to 95% on hover.
* **Panic Key:** Press `Ctrl + Alt + H` to instantly hide/show the widget (Boss Mode).
* **Universal Control:** Works with any media source (Spotify, Chrome, Edge, VLC).
* **Smart Persistence:** Remembers its position on your screen between restarts.
* **Off-Screen Rescue:** Automatically resets position if a monitor is disconnected.

## 🚀 Installation
1.  Download `GhostPlayer.exe` from the Releases page.
2.  Run it. (No installation required).
3.  Drag it to your preferred spot.

## 🛠 Tech Stack
* **Python 3.14**
* **CustomTkinter** (UI)
* **WinRT API** (Media Transport)
* **Pynput** (Global Hotkeys)

## 🎮 Controls
* **Play/Pause/Skip:** Click buttons.
* **Hide/Show:** `Ctrl + Alt + H`
* **Move:** Drag anywhere on the background.
* **Close:** Click '×' (Position is auto-saved).


