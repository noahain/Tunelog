![Tunelog Banner](assets/banner.png)

**Tunelog** is a specialized music library manager designed for content creators and editors. It provides a high-performance, local-first workflow to track your music assets, manage episode usage, and organize tracks with a custom tagging system.

## 🚀 Advanced Features

### 🧠 Intelligent Music Management
- **Visual Library Tracking**: Instantly see which tracks are used, unused, or starred across your entire project history.
- **Episode-Based Cataloging**: Track exactly which episode of your series or podcast a specific track was used in to avoid repetitive soundtracks.
- **Real-Time Search**: Filter through thousands of snippets by artist, title, or tags with zero latency.

### 🔒 Privacy & Architecture
- **Local-First Persistence**: Your library data is stored in a structured `data.json` file on your machine. Tunelog operates entirely offline, keeping your curation private.
- **Automated Discovery**: Built-in `FileSystemEventHandler` monitors your music folder and automatically detects new files, adding them to your library without manual entry.
- **Isolated SQLite & JSON**: High-speed retrieval of track metadata ensures the UI remains snappy even with massive local libraries.

### 📂 Data & Configuration
Tunelog creates a private workspace to house your assets and backups:
- **Default Directory:** `%APPDATA%/Tunelog`

---

## 🛠️ Tech Stack

Tunelog is built using a modern, lightweight desktop architecture:
- **Backend**: **Flask (Python 3.12)** handling REST API endpoints for music metadata and system configuration.
- **Frontend**: **HTML5/CSS3/JS** with a sleek, dark-mode CSS Grid layout (220px sidebar architecture).
- **Desktop Wrapper**: **pywebview** provides a native window experience without the overhead of Electron.
- **System Integration**: Socket-based protection and PowerShell integration for silent file operations.

---

## 📥 Installation

### 1. Prerequisites
Ensure you have [Python 3.12](https://www.python.org/) installed.

### 2. Setup
```bash
# Clone the repository
git clone https://github.com/noahain/tunelog

# Enter the project folder
cd tunelog

# Install dependencies
py -3.12 -m pip install -r requirements.txt

# Run the app
py -3.12 main.py
```

---

## 🤖 Agentic Development

Tunelog was developed through an advanced **Human-AI Collaboration** workflow:
- **Lead Architect:** Noahain (Product Vision & Logic Direction)
- **Primary Developer:** **Claude Code** (Powered by **Kimi K2.5**) - Implemented the Flask REST API, SQLite storage logic, and the core frontend state management.
- **Technical Consultant:** **Gemini 3 Flash** - Provided architectural guidance, UI/UX polish, and fixed cross-process communication between Python and the WebView.

---

## ⚖️ License & Disclaimer
Tunelog is an independent productivity tool for creators. 

**License:** MIT 

Built with ❤️ and Artificial Intelligence.
