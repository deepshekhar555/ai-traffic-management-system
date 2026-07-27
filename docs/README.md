# 🚦 TraffixAI: Multi-Lane Real-Time AI Traffic Digital Twin & Command Center

**Official Entry for DECODE SIH 2026 (Smart India Hackathon)**  
**Team:** CipherSquad (KE5VND)

---

## 📂 Master Directory Structure

```text
ai-traffic-management-system/
│
├── ⚛️ frontend/             # React 18 + Vite Web Command Center Dashboard
│   ├── src/App.jsx         # React UI Components
│   ├── src/index.css       # Glassmorphism Dark Theme Styles
│   └── package.json        # Dependencies (lucide-react, leaflet)
│
├── 🐍 backend/              # Python AI Processing Engine & REST Telemetry Server
│   ├── src/                # 8 AI Innovations & Hardware Controllers
│   ├── main_ultimate.py    # Main Multi-Mode CLI AI Runner
│   ├── main.py             # Real-Time Computer Vision Core
│   ├── dashboard_app.py    # Flask REST Telemetry Server (Port 5000)
│   └── verify_setup.py     # System Verification Checker
│
├── 🗄️ data/                 # System Data and Databases
│   └── traffic_data.db     # SQLite Database
│
├── 🔌 hardware/            # Microcontroller Code (Arduino Uno / ESP32 C++ Sketch)
├── 📊 presentation/        # Official SIH 2026 PowerPoint Presentation Decks
├── 📖 docs/                # Comprehensive Documentation & Architecture Guides
└── 🧪 tests/               # Unit Tests & Debugging Scripts
```

---

## 🚀 How to Run the System

### 1. Launch Python Backend AI Engine & REST Server (Port 5000)
```powershell
cd backend
python main_ultimate.py --camera sample_traffic.mp4 --mode balanced --display detailed
python dashboard_app.py
```

### 2. Launch React Frontend Web Command Center (Port 3000)
```powershell
cd frontend
npm run dev -- --port 3000
```

Access the React Web Dashboard in your browser at: **`http://localhost:3000`**
