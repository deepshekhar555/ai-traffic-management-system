"""
TraffixAI - Master One-Click All-in-One System Launcher
Boots the AI Traffic Computer Vision Core, REST Telemetry Server, and React Web Command Center in one command.
"""

import subprocess
import sys
import time
from pathlib import Path

CURRENT_DIR = Path(__file__).parent.resolve()
if CURRENT_DIR.name == "backend" or CURRENT_DIR.name == "scripts":
    BACKEND_DIR = CURRENT_DIR if CURRENT_DIR.name == "backend" else CURRENT_DIR.parent / "backend"
    ROOT_DIR = CURRENT_DIR.parent
else:
    ROOT_DIR = CURRENT_DIR
    BACKEND_DIR = ROOT_DIR / "backend"

FRONTEND_DIR = ROOT_DIR / "frontend"

def kill_stale_ports(ports=(5000, 3000)):
    """Automatically kill any leftover ghost processes listening on ports 5000 or 3000"""
    for port in ports:
        try:
            if sys.platform == "win32":
                cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }}"'
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

def launch_system():
    print("=" * 75)
    print("TRAFFIX-AI: ALL-IN-ONE SMART CITY SYSTEM LAUNCHER")
    print("   SIH 2026 Submission - Team CipherSquad")
    print("=" * 75)

    kill_stale_ports((5000, 3000))
    processes = []
    
    try:
        # 1. Start Flask REST Telemetry Server (Port 5000)
        print("\n[1/3] Starting Flask REST Telemetry API Server (Port 5000)...")
        p_flask = subprocess.Popen(
            [sys.executable, str(BACKEND_DIR / "dashboard_app.py")],
            cwd=str(BACKEND_DIR)
        )
        processes.append(("Flask REST API", p_flask))
        
        # Wait until Flask port 5000 is ready
        import urllib.request
        print("      Waiting for Flask server initialization...", end="", flush=True)
        for _ in range(15):
            try:
                urllib.request.urlopen("http://localhost:5000/api/stats", timeout=1)
                print(" [READY!]")
                break
            except Exception:
                print(".", end="", flush=True)
                time.sleep(1)
        print()

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
        ai_cmd = [sys.executable, str(BACKEND_DIR / "main.py")] + sys.argv[1:]
        p_ai = subprocess.Popen(
            ai_cmd,
            cwd=str(BACKEND_DIR)
        )
        processes.append(("AI Core Engine", p_ai))

        print("\n" + "=" * 75)
        print("[OK] ALL COMPONENTS STARTED SUCCESSFULLY!")
        print("   - React Command Center UI   : http://localhost:3000")
        print("   - Flask REST Telemetry API  : http://localhost:5000")
        print("   - Real-Time 3D City Twin UI : http://localhost:5000/twin3d")
        print("   - Executive Report PDF     : http://localhost:5000/report")
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
