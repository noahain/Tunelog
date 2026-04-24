from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import time
import sys
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__, static_folder='public')
CORS(app)

# Get base directory - works both in script and PyInstaller exe
if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle - use user's AppData for data
    DATA_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'Tunelog')
    os.makedirs(DATA_DIR, exist_ok=True)
    BASE_DIR = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
else:
    # Running in normal script - use current directory
    BASE_DIR = os.getcwd()
    DATA_DIR = BASE_DIR

CONFIG_PATH = os.path.join(DATA_DIR, 'config.json')
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')

def load_config():
    """Load configuration from config.json"""
    if not os.path.exists(CONFIG_PATH):
        # Create default config
        default_config = {
            "music_folder": "music",
            "auto_detect": True,
            "auto_detect_extensions": [".mp3", ".mp4", ".wav", ".flac", ".m4a"],
            "data_file": "data.json",
            "backup_folder": "database"
        }
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        return default_config

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_data_path():
    """Get the absolute path to data.json using relative path from config"""
    config = load_config()
    data_file = config.get('data_file', 'data.json')
    backup_folder = config.get('backup_folder', 'bkp')

    # If data_file is a relative path, resolve it relative to BASE_DIR
    if not os.path.isabs(data_file):
        return os.path.join(DATA_DIR, backup_folder, data_file)
    return data_file

def get_music_folder():
    """Get the absolute path to the music folder"""
    config = load_config()
    music_folder = config.get('music_folder', 'music')

    # If relative path, resolve it relative to BASE_DIR
    if not os.path.isabs(music_folder):
        return os.path.join(BASE_DIR, music_folder)
    return music_folder

def load_data():
    data_path = get_data_path()
    print(f"[DATA] Looking for data at: {data_path}")
    print(f"[DATA] Data file exists: {os.path.exists(data_path)}")
    if not os.path.exists(data_path):
        print(f"[DATA] Creating empty data file")
        return {"tracks": [], "episodes": [], "availableTags": []}
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"[DATA] Loaded {len(data.get('tracks', []))} tracks")
        return data
    except Exception as e:
        print(f"[DATA ERROR] Failed to load: {e}")
        return {"tracks": [], "episodes": [], "availableTags": []}

def save_data(data):
    data_path = get_data_path()
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def normalize_filename(filename):
    """Normalize filename for comparison"""
    name, ext = os.path.splitext(filename)
    # Remove common separators and normalize
    name = name.replace('_', ' ').replace('-', ' ').replace('.', ' ')
    name = ' '.join(name.split())  # Normalize whitespace
    return name.lower(), ext.lower()

def find_existing_track(data, filepath):
    """Check if a file already exists in the database"""
    filename = os.path.basename(filepath)
    normalized_name, ext = normalize_filename(filename)

    for track in data['tracks']:
        if 'location' in track and track['location']:
            existing_file = os.path.basename(track['location'])
            existing_name, existing_ext = normalize_filename(existing_file)
            if normalized_name == existing_name:
                return track
    return None

def extract_metadata_from_path(filepath):
    """Extract title, artist, and folder info from file path"""
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)

    # Try to extract artist from filename (format: "Title - Artist.mp3" or "Title (ARTIST_ Artist )")
    artist = "Unknown"
    title = name

    # Check for ARTIST_ pattern
    if "(ARTIST_" in name:
        parts = name.split("(ARTIST_")
        title = parts[0].strip()
        artist_part = parts[1].split(")")[0].strip()
        artist = artist_part.replace("_", "").strip()
    # Check for " - " pattern
    elif " - " in name:
        parts = name.rsplit(" - ", 1)
        title = parts[0].strip()
        artist = parts[1].strip()

    # Get folder name
    folder = os.path.basename(os.path.dirname(filepath))

    return title, artist, folder

def scan_for_music_files():
    """Scan the music folder for all music files"""
    config = load_config()
    music_folder = get_music_folder()
    extensions = [ext.lower() for ext in config.get('auto_detect_extensions', ['.mp3', '.mp4'])]

    found_files = []

    if not os.path.exists(music_folder):
        return found_files

    for root, dirs, files in os.walk(music_folder):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in extensions:
                full_path = os.path.join(root, file)
                found_files.append(full_path)

    return found_files

def auto_detect_new_tracks():
    """Automatically detect and add new music files"""
    config = load_config()
    if not config.get('auto_detect', True):
        return []

    data = load_data()
    existing_locations = {t.get('location', ''): True for t in data['tracks']}

    found_files = scan_for_music_files()
    new_tracks = []

    for filepath in found_files:
        abs_path = filepath
        # Try to get relative path, fallback to abs path on different drives
        try:
            rel_path = os.path.relpath(filepath, BASE_DIR)
        except ValueError:
            rel_path = abs_path

        # Check if file already exists
        if abs_path in existing_locations or rel_path in existing_locations:
            continue

        # Check if normalized filename matches
        if find_existing_track(data, filepath):
            continue

        # Extract metadata
        title, artist, folder = extract_metadata_from_path(filepath)

        # Create new track
        new_track = {
            "id": int(time.time() * 1000) + len(new_tracks),
            "title": title,
            "artist": artist,
            "tags": [],
            "episodes": [],
            "notes": "",
            "starred": False,
            "used": False,
            "location": abs_path  # Store absolute path for compatibility
        }

        new_tracks.append(new_track)

    if new_tracks:
        data['tracks'].extend(new_tracks)
        save_data(data)
        print(f"Auto-detected {len(new_tracks)} new tracks")

    return new_tracks

class MusicFolderHandler(FileSystemEventHandler):
    """Handler for file system events in the music folder"""

    def on_created(self, event):
        if not event.is_directory:
            config = load_config()
            extensions = [ext.lower() for ext in config.get('auto_detect_extensions', ['.mp3', '.mp4'])]
            ext = os.path.splitext(event.src_path)[1].lower()
            if ext in extensions:
                print(f"New file detected: {event.src_path}")
                # Wait a moment for the file to be fully written
                time.sleep(1)
                auto_detect_new_tracks()

    def on_moved(self, event):
        if not event.is_directory:
            auto_detect_new_tracks()

def start_file_watcher():
    """Start the file system watcher for the music folder"""
    config = load_config()
    if not config.get('auto_detect', True):
        return

    music_folder = get_music_folder()
    if not os.path.exists(music_folder):
        os.makedirs(music_folder, exist_ok=True)

    event_handler = MusicFolderHandler()
    observer = Observer()
    observer.schedule(event_handler, music_folder, recursive=True)
    observer.start()
    print(f"File watcher started for: {music_folder}")
    return observer

# Initialize file watcher
file_watcher = None
app_initialized = False

def ensure_music_folder():
    """Ensure the music folder exists with a README"""
    music_folder = get_music_folder()
    if not os.path.exists(music_folder):
        os.makedirs(music_folder, exist_ok=True)
        readme_path = os.path.join(music_folder, 'README.txt')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write("Put your music files here!\n\n")
            f.write("Supported formats: .mp3, .mp4, .wav, .flac, .m4a\n")
            f.write("Files will be automatically detected and added to Tunelog.\n")
        print(f"Created music folder: {music_folder}")
        print("  Created README.txt with instructions")
    return music_folder

def init_app():
    """Initialize the application"""
    global file_watcher, app_initialized

    # Prevent double initialization
    if app_initialized:
        print("App already initialized, skipping...")
        return

    # Ensure directories exist
    os.makedirs(os.path.dirname(get_data_path()), exist_ok=True)

    # Ensure music folder exists
    ensure_music_folder()

    # Initial scan for new files
    print("Scanning for music files...")
    new_tracks = auto_detect_new_tracks()
    if new_tracks:
        print(f"Added {len(new_tracks)} new tracks on startup")

    # Start file watcher
    file_watcher = start_file_watcher()

    # Mark as initialized
    app_initialized = True

@app.route('/api/music', methods=['GET'])
def get_music():
    try:
        data = load_data()
        print(f"[API] Returning {len(data.get('tracks', []))} tracks, {len(data.get('episodes', []))} episodes")
        return jsonify(data)
    except Exception as e:
        print(f"[API ERROR] Failed to load data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"tracks": [], "episodes": [], "availableTags": []}), 200

@app.route('/api/tracks', methods=['POST'])
def create_track():
    data = load_data()
    body = request.json
    new_track = {
        "id": int(time.time() * 1000),
        "title": body.get('title', ''),
        "artist": body.get('artist', 'Unknown'),
        "tags": body.get('tags', []),
        "episodes": body.get('episodes', []),
        "notes": body.get('notes', ''),
        "starred": False,
        "used": False
    }
    data['tracks'].append(new_track)
    save_data(data)
    return jsonify(new_track)

@app.route('/api/tracks/<int:track_id>', methods=['PUT'])
def update_track(track_id):
    data = load_data()
    idx = next((i for i, t in enumerate(data['tracks']) if t['id'] == track_id), None)
    if idx is None:
        return '', 404
    data['tracks'][idx] = {**data['tracks'][idx], **request.json}
    save_data(data)
    return jsonify(data['tracks'][idx])

@app.route('/api/tracks/<int:track_id>/location', methods=['PUT'])
def update_track_location(track_id):
    """Update track file location (for drag & drop)"""
    data = load_data()
    idx = next((i for i, t in enumerate(data['tracks']) if t['id'] == track_id), None)
    if idx is None:
        return '', 404
    location = request.json.get('location', '')
    if location:
        data['tracks'][idx]['location'] = location
        save_data(data)
    return jsonify(data['tracks'][idx])

@app.route('/api/tracks/<int:track_id>', methods=['DELETE'])
def delete_track(track_id):
    data = load_data()
    data['tracks'] = [t for t in data['tracks'] if t['id'] != track_id]
    save_data(data)
    return jsonify({"ok": True})

@app.route('/api/episodes', methods=['POST'])
def add_episode():
    data = load_data()
    name = request.json.get('name')
    if name and name not in data['episodes']:
        data['episodes'].append(name)
        save_data(data)
    return jsonify(data['episodes'])

@app.route('/api/tags', methods=['POST'])
def add_tag():
    data = load_data()
    name = request.json.get('name')
    if name and name not in data['availableTags']:
        data['availableTags'].append(name)
        save_data(data)
    return jsonify(data['availableTags'])

@app.route('/api/tracks/<int:track_id>/play', methods=['GET'])
def play_track(track_id):
    data = load_data()
    track = next((t for t in data['tracks'] if t['id'] == track_id), None)
    if track is None:
        return '', 404

    location = track.get('location', '').strip()
    if not location:
        return jsonify({"error": "No location set for this track"}), 400

    if not os.path.exists(location):
        return jsonify({"error": f"File not found: {location}"}), 404

    try:
        os.startfile(location)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tracks/<int:track_id>/reveal', methods=['POST'])
def reveal_track(track_id):
    """Reveal track file in folder"""
    data = load_data()
    track = next((t for t in data['tracks'] if t['id'] == track_id), None)
    if track is None:
        return '', 404

    location = track.get('location', '').strip()
    if not location:
        return jsonify({"error": "No location set for this track"}), 400

    if not os.path.exists(location):
        return jsonify({"error": f"File not found: {location}"}), 404

    try:
        folder = os.path.dirname(location)
        # Windows: explorer /select,path_to_file
        if sys.platform == 'win32':
            subprocess.run(['explorer', '/select,', location], check=False)
        else:
            os.startfile(folder)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tracks/<int:track_id>/file', methods=['GET'])
def get_track_file(track_id):
    """Get track file information"""
    data = load_data()
    track = next((t for t in data['tracks'] if t['id'] == track_id), None)
    if track is None:
        return '', 404

    location = track.get('location', '').strip()
    if not location:
        return jsonify({"error": "No location set for this track"}), 400

    if not os.path.exists(location):
        return jsonify({"error": f"File not found: {location}"}), 404

    try:
        filename = os.path.basename(location)
        filesize = os.path.getsize(location)
        _, file_extension = os.path.splitext(location)

        return jsonify({
            "ok": True,
            "filename": filename,
            "filesize": filesize,
            "path": location,
            "extension": file_extension.lower(),
            "download_url": f"{request.host_url}api/tracks/{track_id}/download"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tracks/<int:track_id>/download', methods=['GET'])
def download_track(track_id):
    """Serve track file for download"""
    data = load_data()
    track = next((t for t in data['tracks'] if t['id'] == track_id), None)
    if track is None:
        return '', 404

    location = track.get('location', '').strip()
    if not location:
        return jsonify({"error": "No location set for this track"}), 400

    if not os.path.exists(location):
        return jsonify({"error": f"File not found: {location}"}), 404

    try:
        filename = os.path.basename(location)

        # Guess MIME type from extension
        _, ext = os.path.splitext(filename.lower())
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.mp4': 'video/mp4',
            '.wav': 'audio/wav',
            '.flac': 'audio/flac',
            '.m4a': 'audio/mp4',
            '.ogg': 'audio/ogg',
            '.aac': 'audio/aac'
        }
        mime_type = mime_types.get(ext, 'application/octet-stream')

        return send_from_directory(
            os.path.dirname(location),
            filename,
            mimetype=mime_type,
            as_attachment=False
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify(load_config())

@app.route('/api/config', methods=['PUT'])
def update_config():
    """Update configuration"""
    config = load_config()
    updates = request.json

    # Validate required fields
    allowed_fields = ['music_folder', 'data_file', 'backup_folder', 'auto_detect', 'auto_detect_extensions']
    for key in updates:
        if key not in allowed_fields:
            return jsonify({"error": f"Invalid config field: {key}"}), 400

    # Validate extensions
    if 'auto_detect_extensions' in updates:
        extensions = updates['auto_detect_extensions']
        if not isinstance(extensions, list):
            return jsonify({"error": "auto_detect_extensions must be a list"}), 400
        for ext in extensions:
            if not isinstance(ext, str) or not ext.startswith('.'):
                return jsonify({"error": f"Invalid extension format: {ext}"}), 400

    config.update(updates)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    return jsonify(config)

@app.route('/api/scan', methods=['POST'])
def manual_scan():
    """Manually trigger a scan for new music files"""
    new_tracks = auto_detect_new_tracks()
    return jsonify({"added": len(new_tracks), "tracks": new_tracks})

@app.route('/api/startup', methods=['POST'])
def startup():
    """Initialize app - call this when app starts"""
    try:
        init_app()
        return jsonify({"ok": True, "message": "Startup complete"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/log', methods=['POST'])
def log_message():
    """Receive log messages from frontend"""
    try:
        data = request.json
        level = data.get('level', 'INFO')
        message = data.get('message', '')
        print(f"[JS {level}] {message}")
        return jsonify({"ok": True})
    except Exception as e:
        print(f"[LOG ERROR] {e}")
        return jsonify({"ok": False}), 500

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(PUBLIC_DIR, path)

@app.route('/', methods=['GET'])
def index():
    # TEMPORARY: Inline HTML to test JavaScript
    return send_from_directory(PUBLIC_DIR, 'index.html')

if __name__ == '__main__':
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"CONFIG_PATH: {CONFIG_PATH}")
    print(f"DATA_PATH: {get_data_path()}")
    print(f"MUSIC_FOLDER: {get_music_folder()}")
    print(f"Public exists: {os.path.exists(PUBLIC_DIR)}")

    print("Tunelog server running on http://localhost:5000")
    try:
        app.run(port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        if file_watcher:
            file_watcher.stop()
        print("\nShutting down...")

