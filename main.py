import threading
import webview
import python_backend
import time
import sys
import os
import subprocess

# Global reference to window for native drag
drag_window = None

class DragAPI:
    """JavaScript API for native file operations"""
    def select_file_in_explorer(self, file_path):
        """Select file in explorer so user can drag it"""
        import subprocess
        if not os.path.exists(file_path):
            return False
        try:
            folder = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            # Open explorer and select the file
            subprocess.Popen(f'explorer /select,"{file_path}"', shell=True)
            return True
        except Exception as e:
            print(f"Select file error: {e}")
            return False

def start_server():
    """Start Flask backend in a separate thread"""
    python_backend.app.run(port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Initialize the backend (create folders, scan for music, start file watcher)
    print("Initializing backend...")
    python_backend.init_app()

    # Start Flask server in background thread
    print("Starting Flask server...")
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Wait a moment for server to start
    time.sleep(1.5)

    # Create desktop window with JS API
    api = DragAPI()
    drag_window = webview.create_window(
        "Tunelog",
        'http://localhost:5000',
        width=1200,
        height=800,
        js_api=api
    )

    # Start the desktop app
    webview.start()
