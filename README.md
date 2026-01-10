# 🎯 X-Annotation YOLO Experience

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)]()
[![Languages](https://img.shields.io/badge/Languages-100%2B-orange.svg)]()

**A state-of-the-art, cross-platform dataset annotation tool for YOLO, built with Python & Tkinter.**

X-Annotation YOLO Experience is a professional-grade GUI for creating, visualizing, and managing object detection datasets. Designed for efficiency and reliability, it supports the latest YOLO formats (v5, v8, v11) and provides advanced features for computer vision workflows.

---

## ✨ Features

### 🚀 Core Experience
*   **Modern Native UI**: Built with standard `tkinter` for maximum performance and native look-and-feel on Windows and Linux (no heavy external dependencies).
*   **Robust Stability**: Validated with an automated macro testing suite to ensure high reliability.
*   **Universal Compatibility**: Optimized for seamless operation across different operating systems with automatic font handling and DPI scaling.

### 🌍 Global Reach
*   **Multi-Language Support**: Complete translations for **100+ languages**.
*   **Searchable Language Selector**: Quickly find your language with a smart, filterable dropdown.
*   **Intelligent Fallback**: Automatic English fallback ensures the interface never breaks, even if a translation is missing.

### 🛠️ Advanced Tooling
*   **Project Management**:
    *   **Automated Setup**: Instantly creates standardized YOLO directory structures (`train`, `valid`, `test`, `data.yaml`).
    *   **Class Manager**: Add, rename, or delete classes dynamically.
*   **Data Analysis**:
    *   **Grid Viewer**: Visualize your dataset in a mosaic grid to spot inconsistencies.
    *   **Dataset Analyzer**: Generating distribution charts and statistics (train/val split ratio, class balance).
    *   **Split Wizard**: Easily redistribute images between training and validation sets with intuitive sliders.

### ✏️ Annotation Power
*   **Smart Drawing**: Rapid bounding box creation with "Draw Mode" (`B`).
*   **Fine Controls**:
    *   Precision resizing with "W" and "H" spinners (with safety checks against inversion).
    *   Pixel-perfect movement using arrow keys or UI controls.
*   **Zoom & Pan**: Smooth navigation using mouse wheel and drag (right/middle click) for detailing high-res images.

---

## 🛠️ Installation

Ensure you have **Python 3.10+** installed.

### 1. Clone the Repository
```bash
git clone https://github.com/SeuUsuario/X-Anotation_YOLO-Experience.git
cd X-Anotation_YOLO-Experience
```

### 2. Create a Virtual Environment (Recommended)
**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Or manually: `pip install pillow pyyaml`)*

---

## 🚀 Usage

Launch the application:
```bash
python main.py
```

### Workflow

1.  **Create Project**: Click `✨ New Project`, define your classes, and choose a save location.
2.  **Add Data**: Drop your images into the created `train/images` folder.
3.  **Annotate**:
    *   Press `B` to toggle **Draw Mode**.
    *   Drag to draw boxes.
    *   Select classes from the right panel.
4.  **Manage**: Use the `Statistics` or `Grid` tabs to audit your dataset quality.
5.  **Export**: Your data is always saved in real-time in standard YOLO format (`.txt` files).

---

## ⌨️ Shortcuts

| Action | Control / Key |
| :--- | :--- |
| **Draw Mode** | `B` (Toggle) |
| **Next Image** | `Right Arrow` |
| **Previous Image** | `Left Arrow` |
| **Delete Box** | `Delete` |
| **Next Annotation** | `S` |
| **Prev Annotation** | `W` |
| **Zoom** | `Mouse Wheel` |
| **Pan Image** | `Right/Middle Click + Drag` |
| **Cancel** | `Esc` |

---

## 📂 Project Structure

X-Annotation adheres to the rigorous YOLO filesystem standard:

```text
MyProject/
├── classes.txt       # Class definitions
├── data.yaml         # Dataset configuration needed for training
├── train/
│   ├── images/       # Source images
│   └── labels/       # YOLO format annotations
├── valid/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

---

## 🔧 Architecture

The project follows a clean, modular Model-View-Controller (MVC) adaptation:

*   **`main.py`**: Application entry point and controller orchestrator.
*   **`ui.py`**: UI definition (View) using pure Tkinter/TTK.
*   **`canvas.py`**: Complex canvas logic (Zoom, Pan, Draw, Resize).
*   **`state.py`**: Centralized application state management.
*   **`localization.py`**: Dynamic translation engine.
*   **`managers.py`**: File I/O for YOLO formats.
*   **`tests/macro/`**: Automated UI test suite for stability verification.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

<p align="center">
  <i>Quality Tools for Computer Vision. Built with ❤️ by the X-Annotation Team.</i>
</p>