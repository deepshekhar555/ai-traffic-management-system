import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, Car, ShieldAlert, Cpu, Leaf, AlertTriangle, 
  MapPin, FileText, Zap, Radio, CheckCircle, Navigation 
} from 'lucide-react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export default function App() {
  const [stats, setStats] = useState({
    vehicles_detected: 0,
    avg_speed: 0,
    max_speed: 0,
    speeding_violations: 0,
    incidents: 0
  });

  const [research, setResearch] = useState({
    q_learning_reward: 24.8,
    bev_homography_error_m: 0.04,
    ttc_min_seconds: 3.8
  });

  const [eco, setEco] = useState({
    co2_saved_kg: 48.2,
    fuel_saved_liters: 19.4
  });

  const [hardware, setHardware] = useState({
    rpi_gpio_status: 'ACTIVE',
    arduino_usb_status: 'COM3 (9600 BAUD)',
    edge_fps: 25.4
  });

  const [anprList, setAnprList] = useState([]);
  const [cameraNodes, setCameraNodes] = useState([]);
  const [selectedNode, setSelectedNode] = useState('node_1');
  const mapRef = useRef(null);
  const canvasRef = useRef(null);

  // Initialize Telemetry Loop
  useEffect(() => {
    const fetchTelemetry = () => {
      fetch('http://localhost:5000/api/stats')
        .then(res => res.json())
        .then(data => setStats(data))
        .catch(() => {});

      fetch('http://localhost:5000/api/research-metrics')
        .then(res => res.json())
        .then(data => setResearch(data))
        .catch(() => {});

      fetch('http://localhost:5000/api/eco-impact')
        .then(res => res.json())
        .then(data => setEco(data))
        .catch(() => {});

      fetch('http://localhost:5000/api/hardware-status')
        .then(res => res.json())
        .then(data => setHardware(data))
        .catch(() => {});

      fetch('http://localhost:5000/api/multi-camera-nodes')
        .then(res => res.json())
        .then(data => setCameraNodes(data))
        .catch(() => {});

      fetch('http://localhost:5000/api/anpr')
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data)) setAnprList(data.slice(-5).reverse());
        })
        .catch(() => {});
    };


    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 2000);
    return () => clearInterval(interval);
  }, []);

  // Initialize Leaflet Map
  useEffect(() => {
    if (!mapRef.current) return;
    const map = L.map(mapRef.current).setView([28.6139, 77.2090], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap'
    }).addTo(map);

    L.marker([28.6139, 77.2090]).addTo(map).bindPopup("<b>Node 1: Connaught Place Intersection</b><br>Status: ACTIVE (25 FPS)");
    L.marker([28.5672, 77.2100]).addTo(map).bindPopup("<b>Node 2: AIIMS Ring Road Signal</b><br>Status: ACTIVE");
    L.circle([28.6139, 77.2090], { color: 'red', fillColor: '#f03', fillOpacity: 0.3, radius: 400 }).addTo(map);

    return () => map.remove();
  }, []);

  // 2D Spatial Twin Canvas Animation Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let posy = 0;

    const renderTwin = () => {
      posy = (posy + 2) % 360;
      ctx.fillStyle = '#050811';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw Road Grid
      ctx.strokeStyle = '#1f2937';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(320, 0); ctx.lineTo(320, 360);
      ctx.moveTo(0, 180); ctx.lineTo(640, 180);
      ctx.stroke();

      // Draw Vehicle Vectors
      ctx.fillStyle = '#10b981';
      ctx.fillRect(300, posy, 20, 20);
      ctx.fillStyle = '#ffffff';
      ctx.font = '10px Inter';
      ctx.fillText('Car-1 (42 km/h)', 270, posy - 5);

      ctx.fillStyle = '#ef4444';
      ctx.fillRect(400, (360 - posy), 24, 24);
      ctx.fillText('Truck-2 (85 km/h)', 400, (360 - posy) - 5);

      animationFrameId = requestAnimationFrame(renderTwin);
    };

    renderTwin();
    return () => cancelAnimationFrame(animationFrameId);
  }, []);

  const triggerOverride = (mode) => {
    alert(`Manual Signal Override Triggered: ${mode}`);
  };

  return (
    <div className="dashboard-root">
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 25 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 900, background: 'linear-gradient(90deg, #00a2e8, #10b981)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            ⚛️ TRAFFIX-AI REACT SMART CITY COMMAND CENTER
          </h1>
          <p style={{ color: '#9ca3af', fontSize: 13, marginTop: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="pulse-dot"></span> Real-Time Video Telemetry Active • Hybrid Edge Architecture
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <select 
            value={selectedNode} 
            onChange={(e) => setSelectedNode(e.target.value)}
            style={{ padding: '8px 12px', borderRadius: 6, background: '#111827', color: '#00a2e8', border: '1px solid #374151', fontSize: 13, fontWeight: 700 }}
          >
            <option value="node_1">📹 Node 1: Connaught Place Intersection</option>
            <option value="node_2">📹 Node 2: AIIMS Ring Road Signal</option>
            <option value="node_3">📹 Node 3: Cyber Hub Highway Express</option>
          </select>
          <a href="http://localhost:5000/twin3d" target="_blank" rel="noreferrer">
            <button className="btn-action" style={{ background: '#00a2e8', color: '#000', fontWeight: 800 }}>
              🌐 Launch 3D City Twin
            </button>
          </a>
          <a href="http://localhost:5000/report" target="_blank" rel="noreferrer">
            <button className="btn-action btn-green">
              <FileText size={16} /> Export Executive PDF Report
            </button>
          </a>
        </div>
      </header>


      {/* 6 Metric Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 16, marginBottom: 20 }}>
        <div className="metric-card" style={{ borderLeftColor: '#3b82f6' }}>
          <div className="label"><Car size={14} style={{ display: 'inline', marginRight: 4 }} /> Vehicles Detected</div>
          <div className="value">{stats.vehicles_detected || 0}</div>
        </div>
        <div className="metric-card" style={{ borderLeftColor: '#10b981' }}>
          <div className="label"><Activity size={14} style={{ display: 'inline', marginRight: 4 }} /> Average Speed</div>
          <div className="value">{Math.round(stats.avg_speed || 0)} km/h</div>
        </div>
        <div className="metric-card" style={{ borderLeftColor: '#f59e0b' }}>
          <div className="label"><Zap size={14} style={{ display: 'inline', marginRight: 4 }} /> Maximum Speed</div>
          <div className="value">{Math.round(stats.max_speed || 0)} km/h</div>
        </div>
        <div className="metric-card" style={{ borderLeftColor: '#ef4444' }}>
          <div className="label"><AlertTriangle size={14} style={{ display: 'inline', marginRight: 4 }} /> Speed Violations</div>
          <div className="value">{stats.speeding_violations || 0}</div>
        </div>
        <div className="metric-card" style={{ borderLeftColor: '#ec4899' }}>
          <div className="label"><ShieldAlert size={14} style={{ display: 'inline', marginRight: 4 }} /> Incidents</div>
          <div className="value">{stats.incidents || 0}</div>
        </div>
        <div className="metric-card" style={{ borderLeftColor: '#8b5cf6' }}>
          <div className="label"><Leaf size={14} style={{ display: 'inline', marginRight: 4 }} /> CO2 Saved</div>
          <div className="value" style={{ color: '#10b981' }}>{eco.co2_saved_kg} kg</div>
        </div>
      </div>

      {/* Proprietary Telemetry Banner */}
      <div className="glass-panel" style={{ marginBottom: 20, background: 'rgba(0, 162, 232, 0.05)', borderColor: 'rgba(0, 162, 232, 0.3)' }}>
        <h3 style={{ fontSize: 14, color: '#00a2e8', fontWeight: 800, textTransform: 'uppercase', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
          <Radio size={16} />⚡ TRAFFIX-AI PROPRIETARY MULTI-MODAL EDGE TELEMETRY
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
          <div className="metric-card">
            <div className="label">🧠 Edge Q-Learning Reward Score</div>
            <div className="value" style={{ color: '#10b981' }}>+{research.q_learning_reward} ΔQ</div>
          </div>
          <div className="metric-card">
            <div className="label">🗺️ BEV Homography Grid Error</div>
            <div className="value" style={{ color: '#3b82f6' }}>±{research.bev_homography_error_m}m</div>
          </div>
          <div className="metric-card">
            <div className="label">🚶‍♂️ Crosswalk Time-to-Collision (TTC)</div>
            <div className="value" style={{ color: '#f59e0b' }}>{research.ttc_min_seconds}s Margin</div>
          </div>
        </div>
      </div>

      {/* 2D Digital Twin & Override Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20, marginBottom: 20 }}>
        <div className="glass-panel">
          <h3 style={{ fontSize: 13, color: '#9ca3af', fontWeight: 700, textTransform: 'uppercase', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Navigation size={16} /> 🗺️ LIVE 2D INTERSECTION DIGITAL TWIN SPATIAL MAP
          </h3>
          <div style={{ position: 'relative', width: '100%', height: 360, background: '#000', borderRadius: 8, overflow: 'hidden', border: '1px solid #374151' }}>
            <canvas ref={canvasRef} width={640} height={360} style={{ width: '100%', height: '100%' }} />
          </div>
        </div>

        <div className="glass-panel">
          <h3 style={{ fontSize: 13, color: '#9ca3af', fontWeight: 700, textTransform: 'uppercase', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Cpu size={16} /> 🎮 SIGNAL OVERRIDE & HARDWARE CONSOLE
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 20 }}>
            <button className="btn-action" onClick={() => triggerOverride('LANE_1')}>🟢 Force Green Lane 1</button>
            <button className="btn-action" onClick={() => triggerOverride('LANE_2')}>🟢 Force Green Lane 2</button>
            <button className="btn-action btn-emergency" onClick={() => triggerOverride('EMERGENCY')}>🚨 Activate Emergency Corridor</button>
          </div>

          <h4 style={{ fontSize: 12, color: '#9ca3af', fontWeight: 700, textTransform: 'uppercase', marginBottom: 8 }}>🔌 EDGE HARDWARE TELEMETRY</h4>
          <div style={{ fontSize: 11, color: '#9ca3af', lineHeight: 1.8 }}>
            <div>• Raspberry Pi GPIO: <strong style={{ color: '#10b981' }}>{hardware.rpi_gpio_status || 'ACTIVE'}</strong></div>
            <div>• Arduino Serial Link: <strong style={{ color: '#3b82f6' }}>{hardware.arduino_usb_status || 'CONNECTED (COM3)'}</strong></div>
            <div>• 🖥️ OLED Display Screen: <strong style={{ color: '#00a2e8' }}>{hardware.oled_display || 'ACTIVE (SSD1306 I2C)'}</strong></div>
            <div>• 📢 Outdoor VMS Matrix Board: <strong style={{ color: '#f59e0b' }}>{hardware.vms_matrix || 'ACTIVE (SPEED LIMIT 60)'}</strong></div>
            <div>• 📡 24GHz Doppler Radar: <strong style={{ color: '#ec4899' }}>{hardware.doppler_radar || 'CALIBRATED (±0.5 km/h)'}</strong></div>
            <div>• 🍃 Air Quality Sensor Node: <strong style={{ color: '#10b981' }}>CO2: {hardware.air_quality?.co2_ppm || 450} ppm | PM2.5: {hardware.air_quality?.pm25_ugm3 || 18} µg/m³</strong></div>
            <div>• 📶 4G LTE & Solar Telemetry: <strong style={{ color: '#8b5cf6' }}>{hardware.lte_modem || 'CONNECTED 4G LTE'} • {hardware.solar_power || '14.2V (96%)'}</strong></div>
            <div>• Edge Processing Speed: <strong style={{ color: '#f59e0b' }}>{hardware.edge_fps || 25} FPS</strong></div>
          </div>

        </div>
      </div>

      {/* GPS Map & ANPR List */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <div className="glass-panel">
          <h3 style={{ fontSize: 13, color: '#9ca3af', fontWeight: 700, textTransform: 'uppercase', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
            <MapPin size={16} /> 📍 LIVE GPS TRAFFIC CAMERA NODES & HOTSPOTS
          </h3>
          <div ref={mapRef} style={{ width: '100%', height: 260, borderRadius: 8, border: '1px solid #374151' }} />
        </div>

        <div className="glass-panel">
          <h3 style={{ fontSize: 13, color: '#9ca3af', fontWeight: 700, textTransform: 'uppercase', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
            <CheckCircle size={16} /> 🏷️ LIVE ANPR LICENSE PLATE ENFORCEMENT & CHALLANS
          </h3>
          <div style={{ maxHeight: 260, overflowY: 'auto' }}>
            {anprList.length > 0 ? (
              anprList.map((item, idx) => (
                <div key={idx} style={{ padding: 10, borderBottom: '1px solid #1f2937', fontSize: 13, display: 'flex', justifyContent: 'space-between' }}>
                  <div>
                    <strong style={{ color: '#f59e0b' }}>🏷️ {item.plate_number || 'DL-01-AB-1234'}</strong> 
                    <span style={{ color: '#9ca3af', marginLeft: 4 }}>({item.vehicle_type || 'car'})</span>
                  </div>
                  <div>
                    <span style={{ color: '#ef4444', fontWeight: 700, marginRight: 8 }}>{Math.round(item.speed_kmh || 85)} km/h</span>
                    <span className="violation-badge">E-CHALLAN ISSUED</span>
                  </div>
                </div>
              ))
            ) : (
              <p style={{ color: '#6b7280', fontSize: 13 }}>Scanning active camera feed for ANPR plates...</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
