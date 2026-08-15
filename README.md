# AI-RTITMS: AI Traffic Digital Twin & Real-Time Intelligent Traffic Management System

An AI-powered smart traffic management system combining real-time computer vision,
a SUMO-based digital twin simulation, and reinforcement-learning signal control —
built for **Decode SIH 2026 (Bharat Nirman track, PS1: AI Traffic Digital Twin)**
and as a Final Year Project (patent filed: AU 2021101076).

## What this project does

1. **Computer Vision Layer** — YOLOv8 + ByteTrack detect and track vehicles from
   live camera feeds, estimating speed, classifying vehicle type, and reading
   license plates (ANPR).
2. **Digital Twin Layer** — Real vehicle counts from the vision layer feed into a
   live [SUMO](https://sumo.dlr.de) traffic simulation via TraCI. Queue lengths,
   delays, and what-if signal-timing results come from SUMO's actual
   car-following engine, not hardcoded formulas.
3. **Signal Control Layer** — An RL agent (`rl_signal_agent.py`) and a SURTRAC-based
   controller (`surtrac_controller.py`) optimize traffic light timing based on
   real-time and simulated conditions.
4. **Forecasting Layer** — An XGBoost model (`congestion_predictor.py`) forecasts
   congestion 15/30/60 minutes ahead, trained on real logged detections once
   enough data accumulates.

## Real intersections modeled

The digital twin currently simulates two real Indian traffic junctions:

| Site | Location | Role |
|---|---|---|
| **Baguiati** | VIP Road x Baguiati Main Road, Kolkata | Primary |
| **Silk Board Junction** | Hosur Road x Outer Ring Road, Bengaluru | Secondary (India's most congested junction) |

A generic 4-way template is also included for quick testing without a specific site.

## Project structure

```
backend/
  main.py                  - Core detection + signal control application
  dashboard_app.py         - Flask web dashboard
  start_all.py             - Launches backend + frontend together
  src/                     - 40+ modules: detection, tracking, digital twin,
                              SUMO bridge, RL agent, ANPR, emergency detection,
                              pedestrian safety, V2X, hardware control, etc.
  templates/                - Dashboard HTML views
  config/, camera_sources.json - Configuration

frontend/                  - React/Vite web command center

sumo/
  baguiati/                - Primary real intersection network
  silk_board/               - Secondary real intersection network
  intersection.*            - Generic template network

hardware/
  arduino_traffic_controller.ino - Physical signal hardware control

docs/                      - Feature guides, architecture docs, troubleshooting
tests/                     - Test suite (camera, detection, ByteTrack, speed)
presentation/              - SIH proposal, ideation deck, reference papers
```

## Setup

### 1. Install Python dependencies
```bash
pip install -r backend/requirements.txt
pip install traci sumolib
```

### 2. Install SUMO
Download from [sumo.dlr.de/docs/Downloads.php](https://sumo.dlr.de/docs/Downloads.php),
or via pip:
```bash
pip install eclipse-sumo
```

### 3. Install frontend dependencies (optional, for the React dashboard)
```bash
cd frontend
npm install
```

### 4. Run everything together
```bash
python start_all.py
```
This starts the Flask backend (port 5000) and React frontend (port 3000).

### 5. Test the digital twin independently
```bash
cd backend/src
python sumo_traci_bridge.py baguiati
python sumo_traci_bridge.py silk_board
```
Look for `traci_status: ACTIVE_SYNC` — confirms a genuine live SUMO connection.

## Notes

- The congestion predictor trains on real detection data from `data/traffic_data.db`
  once ~20+ minutes of camera logging accumulates; it falls back to a clearly
  labeled synthetic baseline before that.
- See `docs/` for detailed guides on ByteTrack integration, speed monitoring,
  and system architecture.
