"""
TraffixAI - Master Root Launcher
SIH 2026 - Smart City Traffic Intelligence

Allows executing `python start_all.py` directly from the project root directory.
Boots the Flask REST Telemetry Server, React Web Command Center, and AI Detection Engine.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from start_all import launch_system
    if __name__ == "__main__":
        launch_system()
except ImportError:
    import subprocess
    script_path = SCRIPTS_DIR / "start_all.py"
    subprocess.run([sys.executable, str(script_path)] + sys.argv[1:])
