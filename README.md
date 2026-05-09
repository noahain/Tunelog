
<div align="center">
  <img src="assets/icon.png" width="144" height="144" alt="Tunelog" />
  <h1>Tunelog</h1>

  <p><strong>Music library manager for content creators and editors</strong></p>

  <p>
    <img src="https://img.shields.io/badge/version-1.0.0-blue" alt="version" />
    <img src="https://img.shields.io/badge/license-MIT-green" alt="license" />
    <img src="https://img.shields.io/badge/platform-Windows-lightgrey" alt="platform" />
    <img src="https://img.shields.io/badge/python-3.12-blue" alt="python" />
  </p>
</div>

---

Tunelog tracks your music library. See which tracks are used, unused, or starred. Tag episodes to avoid repetitive soundtracks. Search by artist, title, or tags. All offline.

## What it does

**Library tracking**
- Visual indicators: used, unused, starred
- Episode-based cataloging, know which track played in which episode
- Real-time search across thousands of tracks

**Automated discovery**
- Monitors your music folder with `FileSystemEventHandler`
- Detects new files automatically — no manual entry

**Storage**
- `data.json` on your machine
- SQLite for metadata retrieval
- Operates entirely offline

## Where data lives

| Platform | Path |
| :--- | :--- |
| **Windows** | `%APPDATA%/Tunelog` |

## Install

**Requirements**
- [Python 3.12](https://www.python.org/)

```bash
git clone https://github.com/noahain/tunelog
cd tunelog
py -3.12 -m pip install -r requirements.txt
py -3.12 main.py
```

## Tech stack

Python 3.12 · Flask · SQLite · pywebview · HTML/CSS/JS

## Development story

- **Lead:** Noahain - product vision, logic direction
- **Primary developer:** Claude Code (Kimi K2.5) - Flask REST API, SQLite storage, frontend state
- **Technical consultant:** Gemini 3 Flash - architecture, UI polish, cross-process communication

## License

MIT

