"""
TraffixAI - Master One-Click All-in-One System Launcher
Boots the AI Traffic Computer Vision Core, REST Telemetry Server, and React Web Command Center in one command.
"""

import subprocess
import sys
import time
from pathlib import Path

CURRENT_DIR = Path(__file__).parent.resolve()
if CURRENT_DIR.name == "backend":
    BACKEND_DIR = CURRENT_DIR
    ROOT_DIR = CURRENT_DIR.parent
else:
    ROOT_DIR = CURRENT_DIR
    BACKEND_DIR = ROOT_DIR / "backend"

FRONTEND_DIR = ROOT_DIR / "frontend"

def launch_system():
    print("=" * 75)
    print("TRAFFIX-AI: ALL-IN-ONE SMART CITY SYSTEM LAUNCHER")
    print("   SIH 2026 Submission - Team CipherSquad")
    print("=" * 75)

    processes = []
    
    try:
        # 1. Start Flask REST Telemetry Server (Port 5000)
        print("\n[1/3] Starting Flask REST Telemetry API Server (Port 5000)...")
        p_flask = subprocess.Popen(
            [sys.executable, str(BACKEND_DIR / "dashboard_app.py")],
            cwd=str(BACKEND_DIR)
        )
        processes.append(("Flask REST API", p_flask))
        time.sleep(2)

        # 2. Start React Web Dashboard (Port 3000)
        print("[2/3] Starting React Web Command Center Dashboard (Port 3000)...")
        p_react = subprocess.Popen(
            ["npx.cmd" if sys.platform == "win32" else "npx", "vite", "--port", "3000"],
            cwd=str(FRONTEND_DIR),
            shell=True
        )
        processes.append(("React Dashboard", p_react))
        time.sleep(2)

        # 3. Start AI Computer Vision Core
        print("[3/3] Launching AI Computer Vision Detection Core...")
        p_ai = subprocess.Popen(
            [sys.executable, str(BACKEND_DIR / "main.py")],
            cwd=str(BACKEND_DIR)
        )
        processes.append(("AI Core Engine", p_ai))

        print("\n" + "=" * 75)
        print("[OK] ALL COMPONENTS STARTED SUCCESSFULLY!")
        print("   - React Command Center UI : http://localhost:3000")
        print("   - Flask REST Telemetry API: http://localhost:5000")
        print("   - Executive Report PDF   : http://localhost:5000/report")
        print("   Press Ctrl+C at any time to stop all services.")
        print("=" * 75 + "\n")


        p_ai.wait()

    except KeyboardInterrupt:
        print("\nShutting down all TraffixAI services...")
        for name, proc in processes:
            print(f"Terminating {name}...")
            proc.terminate()
        print("All services stopped cleanly.")

if __name__ == "__main__":
    launch_system()
