# AI-RTITMS: AI Traffic Digital Twin & Real-Time Intelligent Traffic Management System

A software prototype for exploring traffic-camera ingestion, SUMO-based simulation,
and reinforcement-learning concepts. A working webcam frame can be verified locally;
field operation, detection accuracy, and physical signal control are not established
by that check.

Demo video : https://youtu.be/x6F9QH6RAFE

Live Demo : https://deepshekhar555.github.io/ai-traffic-management-system/

## What this project does

1. **Camera and vision experiments** — The repository includes video-ingestion,
   detection, tracking, and ANPR components. The camera verification page checks
   image delivery only; it does not certify those components' accuracy or field
   readiness.
2. **Digital twin and control research** — SUMO and reinforcement-learning
   simulations are available for controlled experiments. A successful simulation
   is not a live-junction deployment or evidence of improved traffic outcomes.
3. **Forecasting experiments** — The congestion predictor can be evaluated after
   suitable historical data and a documented validation method are available.

## Camera verification and demo sources

Run the Flask dashboard with `python backend/dashboard_app.py`, then open
`http://127.0.0.1:5000/webcam`. The status changes to “Webcam frame received”
only after the local webcam route obtains an actual image. This confirms frame
delivery, not traffic detection, camera location, permission, or model accuracy.

The selectable numbered lanes 1–3 are illustrative simulations, not camera feeds.
The local webcam and configured remote-camera routes return an unavailable status
when they cannot obtain frames; they do not substitute synthetic traffic. Missing
counts, accuracy, and field measurements remain unreported until independently
measured and documented.

## SUMO simulation scenarios

These are simulation scenarios and do not imply cameras, field trials, or deployed
signal-control hardware at the named locations.

The digital twin currently simulates two real Indian traffic junctions:

| Site | Location | Role |
|---|---|---|
| **Baguiati** | VIP Road x Baguiati Main Road, Kolkata | Simulation scenario |
| **Silk Board Junction** | Hosur Road x Outer Ring Road, Bengaluru | Simulation scenario |

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

The Flask-hosted React dashboard builds with `/spatial-ai/` by default. The
GitHub Pages workflow sets `VITE_BASE_PATH=/ai-traffic-management-system/` for
the repository's Pages URL.

## Setup

### 1. Install Python dependencies
```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt
pip install traci sumolib
```

The project targets Python 3.10+ and uses a current compatible dependency set for modern CV, simulation, and dashboard tooling.

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
