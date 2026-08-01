import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, Car, ShieldAlert, Cpu, Leaf, AlertTriangle, 
  MapPin, FileText, Zap, Radio, CheckCircle, Navigation, 
  User, Lock, Key, LogOut, Search, Mic, MicOff, Settings,
  Database, RefreshCw, Volume2, ShieldCheck, CreditCard
} from 'lucide-react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix leaflet icon paths in Webpack/Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

export default function App() {
  // Auth state
  const [user, setUser] = useState(null);
  const [portalSelection, setPortalSelection] = useState('admin');
  const [usernameInput, setUsernameInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  // App metrics & database status state
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
  const [dbStatus, setDbStatus] = useState({
    mysql_active: false,
    mysql_mode: 'SQLite Mode',
    mongodb_connected: false,
    mongodb_mode: 'Fallback Mode'
  });
  const [sessionLogs, setSessionLogs] = useState([]);

  // settings & control panel states
  const [settings, setSettings] = useState({
    voice_enabled: true,
    voice_rate: 150,
    voice_volume: 0.9,
    active_node: 'node_1',
    override_mode: 'AUTO'
  });

  // Client speech states
  const [clientSpeechEnabled, setClientSpeechEnabled] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const [speechError, setSpeechError] = useState('');
  const [speechCommandResult, setSpeechCommandResult] = useState('');

  // Customer challan search states
  const [searchPlate, setSearchPlate] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [challanResults, setChallanResults] = useState([]);
  const [searched, setSearched] = useState(false);

  // Refs for tracking changes to trigger voice alert
  const prevSpeedingRef = useRef(0);
  const prevIncidentRef = useRef(0);

  const mapContainerRef = useRef(null);
  const canvasRef = useRef(null);
  const mapInstanceRef = useRef(null);

  // Browser TTS engine helper
  const speakText = (text) => {
    if (!clientSpeechEnabled || !window.speechSynthesis) return;
    window.speechSynthesis.cancel(); // Cancel any ongoing speech
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.volume = settings.voice_volume;
    utterance.rate = settings.voice_rate / 150.0; // scale rate around standard
    window.speechSynthesis.speak(utterance);
  };

  // Browser STT engine helper (Voice commands)
  const startVoiceRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechError('Speech Recognition is not supported by your browser.');
      speakText('Speech recognition is not supported in this browser. Please use Google Chrome.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      setSpeechError('');
      setSpeechCommandResult('Listening for commands...');
    };

    recognition.onerror = (event) => {
      setIsListening(false);
      setSpeechError('Voice command error: ' + event.error);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.onresult = (event) => {
      const command = event.results[0][0].transcript.toLowerCase().trim();
      setSpeechCommandResult(`Command heard: "${command}"`);
      processVoiceCommand(command);
    };

    recognition.start();
  };

  const processVoiceCommand = (command) => {
    if (command.includes('force green lane one') || command.includes('lane one green')) {
      triggerOverride('LANE_1');
      speakText('Acknowledged. Signal overridden: Force Green Lane One active.');
    } else if (command.includes('force green lane two') || command.includes('lane two green')) {
      triggerOverride('LANE_2');
      speakText('Acknowledged. Signal overridden: Force Green Lane Two active.');
    } else if (command.includes('emergency corridor') || command.includes('activate emergency')) {
      triggerOverride('EMERGENCY');
      speakText('Alert! Emergency green corridor activated. All lane signals cleared.');
    } else if (command.includes('automatic') || command.includes('auto mode') || command.includes('reset override')) {
      triggerOverride('AUTO');
      speakText('Acknowledged. Resuming automatic signal schedule control.');
    } else if (command.includes('export report') || command.includes('download report')) {
      speakText('Generating and opening executive PDF report.');
      window.open('http://localhost:5000/report', '_blank');
    } else if (command.includes('switch to node one') || command.includes('node one camera') || command.includes('select node one')) {
      updateNode('node_1');
      speakText('Switching camera feed to Intersection Node One, Connaught Place.');
    } else if (command.includes('switch to node two') || command.includes('node two camera') || command.includes('select node two')) {
      updateNode('node_2');
      speakText('Switching camera feed to Intersection Node Two, AIIMS Ring Road.');
    } else if (command.includes('switch to node three') || command.includes('node three camera') || command.includes('select node three')) {
      updateNode('node_3');
      speakText('Switching camera view to Intersection Node Three, Cyber Hub Highway.');
    } else if (command.includes('voice on') || command.includes('enable voice')) {
      setClientSpeechEnabled(true);
      speakText('AI Voice alerts turned on.');
    } else if (command.includes('voice off') || command.includes('disable voice')) {
      speakText('Turning AI Voice alerts off.');
      setClientSpeechEnabled(false);
    } else {
      speakText(`Command "${command}" unrecognized. Try saying: emergency corridor, switch to node one, or force green lane one.`);
    }
  };

  // Perform backend login validation
  const handleLogin = (e) => {
    e.preventDefault();
    if (!usernameInput || !passwordInput) {
      setAuthError('Please fill in all authentication fields.');
      return;
    }

    setAuthLoading(true);
    setAuthError('');

    fetch('http://localhost:5000/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: usernameInput,
        password: passwordInput,
        portal: portalSelection
      })
    })
      .then(async (res) => {
        const data = await res.json();
        if (res.ok && data.success) {
          setUser({ username: data.username, role: data.role });
          speakText(`Access granted. Welcome to the Traffix AI ${data.role === 'admin' ? 'Administration Command Center' : 'Customer Portal'}`);
          fetchDatabaseStatus();
          fetchSessionLogs();
        } else {
          setAuthError(data.error || 'Authentication rejected.');
          speakText('Authentication failed. Please verify credentials.');
        }
      })
      .catch((err) => {
        setAuthError('Failed to communicate with Auth API server.');
        speakText('Server communication failure.');
      })
      .finally(() => {
        setAuthLoading(false);
      });
  };

  const handleLogout = () => {
    if (!user) return;
    
    fetch('http://localhost:5000/api/auth/logout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: user.username, role: user.role })
    }).catch(() => {});

    speakText('Logging out. Session terminated safely.');
    setUser(null);
    setUsernameInput('');
    setPasswordInput('');
    setChallanResults([]);
    setSearched(false);
    setSearchPlate('');
  };

  // Fetch Database Connections
  const fetchDatabaseStatus = () => {
    fetch('http://localhost:5000/api/db-status')
      .then(res => res.json())
      .then(data => setDbStatus(data))
      .catch(() => {});
  };

  // Fetch Session logs
  const fetchSessionLogs = () => {
    fetch('http://localhost:5000/api/auth/logs')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setSessionLogs(data);
      })
      .catch(() => {});
  };

  // Trigger signal overrides
  const triggerOverride = (mode) => {
    fetch('http://localhost:5000/api/override', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode })
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setSettings(prev => ({ ...prev, override_mode: mode }));
          fetchSystemSettings();
        }
      })
      .catch(() => {});
  };

  // Update intersection node
  const updateNode = (nodeId) => {
    fetch('http://localhost:5000/api/admin/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active_node: nodeId })
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setSettings(prev => ({ ...prev, active_node: nodeId }));
        }
      })
      .catch(() => {});
  };

  // Update Settings
  const updateSettingsAPI = (updates) => {
    fetch('http://localhost:5000/api/admin/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setSettings(data.settings);
        }
      })
      .catch(() => {});
  };

  // Fetch settings from Mongo DB
  const fetchSystemSettings = () => {
    fetch('http://localhost:5000/api/auth/status')
      .then(res => res.json())
      .then(data => {
        if (data && !data.error) {
          setSettings({
            voice_enabled: data.voice_enabled ?? true,
            voice_rate: data.voice_rate ?? 150,
            voice_volume: data.voice_volume ?? 0.9,
            active_node: data.active_node ?? 'node_1',
            override_mode: data.override_mode ?? 'AUTO'
          });
        }
      })
      .catch(() => {});
  };

  // Customer portal search e-challans
  const handleChallanSearch = (e) => {
    e.preventDefault();
    if (!searchPlate) return;

    setSearchLoading(true);
    setSearched(true);
    setChallanResults([]);

    fetch(`http://localhost:5000/api/challans?plate=${encodeURIComponent(searchPlate)}`)
      .then(res => res.json())
      .then(data => {
        setChallanResults(data);
        if (data.length > 0) {
          speakText(`Found ${data.length} traffic citations for license plate ${searchPlate.toUpperCase()}`);
        } else {
          speakText(`No violations found for plate ${searchPlate.toUpperCase()}`);
        }
      })
      .catch(() => {
        speakText('Failed to query challan details.');
      })
      .finally(() => {
        setSearchLoading(false);
      });
  };

  // Pay challan simulation
  const handlePayChallan = (challanId) => {
    speakText('Initiating payment gateway secure redirection.');
    setTimeout(() => {
      setChallanResults(prev => prev.map(c => c.challan_id === challanId ? { ...c, status: 'PAID' } : c));
      speakText(`Receipt issued. Citation ${challanId} has been successfully settled.`);
    }, 1500);
  };

  // Initialize Telemetry Loop
  useEffect(() => {
    if (!user) return;

    const fetchTelemetry = () => {
      fetch('http://localhost:5000/api/stats')
        .then(res => res.json())
        .then(data => {
          setStats(data);
          
          // Check for new violations to voice out alerts
          const newSpeeding = data.speeding_violations || 0;
          if (newSpeeding > prevSpeedingRef.current && prevSpeedingRef.current !== 0) {
            speakText("Security Alert. Speed limit breach detected. Issuing e-challan.");
          }
          prevSpeedingRef.current = newSpeeding;

          const newIncidents = data.accidents || 0;
          if (newIncidents > prevIncidentRef.current && prevIncidentRef.current !== 0) {
            speakText("Emergency warning. Traffic collision detected. Route dispatch triggered.");
          }
          prevIncidentRef.current = newIncidents;
        })
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
    fetchDatabaseStatus();
    fetchSystemSettings();
    fetchSessionLogs();

    const interval = setInterval(fetchTelemetry, 2500);
    return () => clearInterval(interval);
  }, [user]);

  // Leaflet Map Initialization
  useEffect(() => {
    if (!user || !mapContainerRef.current) return;

    // Clean up previous map if exists
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    const map = L.map(mapContainerRef.current).setView([28.6139, 77.2090], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap'
    }).addTo(map);

    L.marker([28.6139, 77.2090]).addTo(map).bindPopup("<b>Node 1: Connaught Place Intersection</b><br>Status: ACTIVE (25 FPS)");
    L.marker([28.5672, 77.2100]).addTo(map).bindPopup("<b>Node 2: AIIMS Ring Road Signal</b><br>Status: ACTIVE");
    L.circle([28.6139, 77.2090], { color: 'red', fillColor: '#f03', fillOpacity: 0.3, radius: 400 }).addTo(map);

    mapInstanceRef.current = map;

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [user]);

  // 2D Spatial Twin Canvas Animation Loop
  useEffect(() => {
    if (!user || user.role !== 'admin') return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let posy = 0;

    const renderTwin = () => {
      posy = (posy + 2) % 360;
      ctx.fillStyle = '#0a0d16';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw Road Grid
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(320, 0); ctx.lineTo(320, 360);
      ctx.moveTo(0, 180); ctx.lineTo(640, 180);
      ctx.stroke();

      // Road markings (lanes)
      ctx.strokeStyle = '#94a3b8';
      ctx.lineWidth = 1;
      ctx.setLineDash([10, 10]);
      ctx.beginPath();
      ctx.moveTo(270, 0); ctx.lineTo(270, 360);
      ctx.moveTo(370, 0); ctx.lineTo(370, 360);
      ctx.moveTo(0, 130); ctx.lineTo(640, 130);
      ctx.moveTo(0, 230); ctx.lineTo(640, 230);
      ctx.stroke();
      ctx.setLineDash([]); // reset

      // Draw active sensor scope glow
      ctx.fillStyle = 'rgba(0, 242, 254, 0.05)';
      ctx.beginPath();
      ctx.arc(320, 180, 80, 0, Math.PI * 2);
      ctx.fill();

      // Draw Vehicle Vectors (Green for normal, red for speeders)
      ctx.fillStyle = '#10b981';
      ctx.fillRect(300, posy, 20, 12);
      ctx.fillStyle = '#ffffff';
      ctx.font = '9px Inter';
      ctx.fillText('Car-1 (42 km/h)', 210, posy + 8);

      // Speeding truck
      ctx.fillStyle = '#ef4444';
      ctx.fillRect(390, (360 - posy), 24, 16);
      ctx.fillText('⚡ Truck-2 (85 km/h)', 425, (360 - posy) + 12);

      // Emergency ambulance
      ctx.fillStyle = '#3b82f6';
      ctx.fillRect(340, (posy + 60) % 360, 20, 14);
      ctx.fillStyle = '#ef4444';
      ctx.beginPath();
      ctx.arc(350, ((posy + 60) % 360) + 7, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#ffffff';
      ctx.fillText('🚨 Ambulance (64 km/h)', 365, ((posy + 60) % 360) + 10);

      animationFrameId = requestAnimationFrame(renderTwin);
    };

    renderTwin();
    return () => cancelAnimationFrame(animationFrameId);
  }, [user]);

  // LOGIN PAGE VIEW
  if (!user) {
    return (
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <h1 className="logo-text">⚡ TRAFFIX-AI</h1>
            <p className="logo-sub">Smart City AI Traffic Command & Portal Console</p>
          </div>
          
          <div className="portal-selector">
            <button 
              className={`portal-btn ${portalSelection === 'admin' ? 'active' : ''}`}
              onClick={() => { setPortalSelection('admin'); setAuthError(''); }}
            >
              <Cpu size={18} />
              Admin Portal
            </button>
            <button 
              className={`portal-btn ${portalSelection === 'customer' ? 'active' : ''}`}
              onClick={() => { setPortalSelection('customer'); setAuthError(''); }}
            >
              <User size={18} />
              Customer Portal
            </button>
          </div>

          <form onSubmit={handleLogin} className="login-form">
            <div className="input-group">
              <label><User size={14} /> Username</label>
              <input 
                type="text" 
                value={usernameInput} 
                onChange={(e) => setUsernameInput(e.target.value)}
                placeholder="Enter portal username..."
              />
            </div>
            
            <div className="input-group">
              <label><Key size={14} /> Password</label>
              <input 
                type="password" 
                value={passwordInput} 
                onChange={(e) => setPasswordInput(e.target.value)}
                placeholder="Enter portal password..."
              />
            </div>

            {authError && <div className="error-banner"><AlertTriangle size={16} /> {authError}</div>}

            <button type="submit" className="login-submit-btn" disabled={authLoading}>
              {authLoading ? 'Verifying Gateway...' : 'Access Portal Dashboard'}
            </button>
          </form>

          <div className="login-help">
            <h4>💡 Quick Demo Credentials:</h4>
            <div className="help-credentials">
              <div>Admin: <code>admin</code> / <code>admin123</code></div>
              <div>Customer: <code>customer</code> / <code>customer123</code></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // CUSTOMER PORTAL VIEW
  if (user.role === 'customer') {
    return (
      <div className="dashboard-root">
        {/* Header */}
        <header className="main-header">
          <div>
            <h1 className="logo-title green-gradient-text">
              ✨ TRAFFIX-AI CUSTOMER MOBILITY PORTAL
            </h1>
            <p className="sub-tag">
              Logged in as: <strong className="user-indicator">{user.username}</strong> • Smart Citizen Dashboard
            </p>
          </div>
          <button className="btn-action btn-emergency" onClick={handleLogout}>
            <LogOut size={16} /> Log Out
          </button>
        </header>

        {/* 4 Cards Public Grid */}
        <div className="grid-4" style={{ marginBottom: 20 }}>
          <div className="metric-card border-green">
            <div className="label"><Leaf size={14} className="icon-inline" /> Carbon Emission Offset</div>
            <div className="value green-text">{eco.co2_saved_kg} kg CO2</div>
          </div>
          <div className="metric-card border-cyan">
            <div className="label"><Zap size={14} className="icon-inline" /> Saved Fuel volume</div>
            <div className="value cyan-text">{eco.fuel_saved_liters} Liters</div>
          </div>
          <div className="metric-card border-amber">
            <div className="label"><Activity size={14} className="icon-inline" /> Average Speed</div>
            <div className="value">{Math.round(stats.avg_speed || 48)} km/h</div>
          </div>
          <div className="metric-card border-red">
            <div className="label"><ShieldAlert size={14} className="icon-inline" /> Local Safety Compliance</div>
            <div className="value text-white">98.4%</div>
          </div>
        </div>

        {/* Two Columns: Ticket Search & Live Map */}
        <div className="grid-2-custom">
          {/* Challan search widget */}
          <div className="glass-panel">
            <h3 className="panel-title text-amber">
              <Search size={18} /> QUERY & RESOLVE E-CHALLAN SPEED TICKETS
            </h3>
            <p className="panel-subtitle">Search for speed violations and print/pay camera citations instantly</p>
            
            <form onSubmit={handleChallanSearch} className="search-form">
              <input 
                type="text" 
                value={searchPlate} 
                onChange={(e) => setSearchPlate(e.target.value)}
                placeholder="Enter license plate number (e.g. DL-01-AB-1234)..."
                className="search-input"
              />
              <button type="submit" className="search-btn" disabled={searchLoading}>
                {searchLoading ? <RefreshCw className="spin" size={16} /> : <Search size={16} />} Query
              </button>
            </form>

            <div className="challan-results-box">
              {searchLoading ? (
                <div className="loading-state">Accessing traffic records database...</div>
              ) : searched ? (
                challanResults.length > 0 ? (
                  <div className="challan-list">
                    {challanResults.map((challan, idx) => (
                      <div key={idx} className="challan-item">
                        <div className="challan-meta">
                          <div className="challan-id-label">{challan.challan_id}</div>
                          <div>Vehicle Class: <strong>{challan.vehicle_type}</strong></div>
                          <div>Recorded Speed: <strong className="text-red">{challan.speed_kmh} km/h</strong></div>
                          <div className="timestamp-text">Time: {new Date(challan.timestamp).toLocaleString()}</div>
                        </div>
                        <div className="challan-payment">
                          <div className="price-tag">₹{challan.fine_amount_inr} INR</div>
                          {challan.status === 'ISSUED' ? (
                            <button className="pay-btn" onClick={() => handlePayChallan(challan.challan_id)}>
                              <CreditCard size={14} /> Pay Challan
                            </button>
                          ) : (
                            <div className="paid-badge"><ShieldCheck size={14} /> Paid & Settled</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state text-green">
                    <ShieldCheck size={40} style={{ marginBottom: 10, stroke: '#10b981' }} />
                    <p>Clean Record! No speed limit violations are registered for plate <strong>{searchPlate.toUpperCase()}</strong>.</p>
                  </div>
                )
              ) : (
                <div className="empty-state">
                  <Database size={30} style={{ marginBottom: 8, stroke: '#6b7280' }} />
                  <p>Enter your registration number above to search current issued citations.</p>
                </div>
              )}
            </div>
          </div>

          {/* Map widget */}
          <div className="glass-panel">
            <h3 className="panel-title">
              <MapPin size={18} /> LIVE GPS TRAFFIC CAMERA INTERSECTIONS
            </h3>
            <p className="panel-subtitle">Current city intersection tracking and congestion hotspots</p>
            <div ref={mapContainerRef} className="map-view" style={{ height: 350 }} />
          </div>
        </div>
      </div>
    );
  }

  // ADMIN PORTAL VIEW
  return (
    <div className="dashboard-root">
      {/* Header */}
      <header className="main-header">
        <div>
          <h1 className="logo-title cyan-gradient-text">
            ⚛️ TRAFFIX-AI SMART CITY COMMAND CENTER
          </h1>
          <p className="sub-tag">
            <span className="pulse-dot"></span> Logged in as: <strong className="user-indicator">{user.username} (Administrator)</strong> • Hybrid Edge Engine Telemetry
          </p>
        </div>
        <div className="header-actions">
          {/* AI Voice Assistant Mic */}
          <button 
            className={`voice-assistant-btn ${isListening ? 'listening' : ''}`}
            onClick={startVoiceRecognition}
            title="Start voice recognition"
          >
            {isListening ? <Mic size={18} className="pulse-anim" /> : <MicOff size={18} />}
            <span>Voice Assistant</span>
          </button>
          
          <button className="btn-action btn-emergency" onClick={handleLogout}>
            <LogOut size={16} /> Log Out
          </button>
        </div>
      </header>

      {/* Voice feedback banner */}
      {speechCommandResult && (
        <div className="voice-feedback-banner">
          <Volume2 size={16} /> {speechCommandResult}
          {speechError && <span className="speech-error"> ({speechError})</span>}
        </div>
      )}

      {/* 6 Metric Cards Grid */}
      <div className="grid-6" style={{ marginBottom: 20 }}>
        <div className="metric-card border-cyan">
          <div className="label"><Car size={14} className="icon-inline" /> Vehicles Detected</div>
          <div className="value">{stats.vehicles_detected || 0}</div>
        </div>
        <div className="metric-card border-green">
          <div className="label"><Activity size={14} className="icon-inline" /> Average Speed</div>
          <div className="value">{Math.round(stats.avg_speed || 0)} km/h</div>
        </div>
        <div className="metric-card border-amber">
          <div className="label"><Zap size={14} className="icon-inline" /> Maximum Speed</div>
          <div className="value">{Math.round(stats.max_speed || 0)} km/h</div>
        </div>
        <div className="metric-card border-red">
          <div className="label"><AlertTriangle size={14} className="icon-inline" /> Speed Violations</div>
          <div className="value text-red">{stats.speeding_violations || 0}</div>
        </div>
        <div className="metric-card border-purple">
          <div className="label"><ShieldAlert size={14} className="icon-inline" /> Incidents</div>
          <div className="value text-white">{stats.accidents || 0}</div>
        </div>
        <div className="metric-card border-cyan-light">
          <div className="label"><Leaf size={14} className="icon-inline" /> Active DB Engine</div>
          <div className="value-small">{stats.db_mode || "SQLite"}</div>
        </div>
      </div>

      {/* Primary Panels: 2D Spatial Twin Map & Controls */}
      <div className="grid-2-1" style={{ marginBottom: 20 }}>
        <div className="glass-panel">
          <h3 className="panel-title text-cyan">
            <Navigation size={16} /> LIVE 2D INTERSECTION DIGITAL TWIN SPATIAL MAP
          </h3>
          <div className="canvas-wrapper">
            <canvas ref={canvasRef} width={640} height={360} className="twin-canvas" />
          </div>
        </div>

        <div className="glass-panel">
          <h3 className="panel-title">
            <Cpu size={16} /> SIGNAL OVERRIDE & TELEMETRY CONSOLE
          </h3>
          
          <div className="control-section">
            <div className="control-group">
              <label>ACTIVE OVERRIDE STATE: </label>
              <strong className={`status-badge ${settings.override_mode !== 'AUTO' ? 'override-active' : 'override-auto'}`}>
                {settings.override_mode}
              </strong>
            </div>

            <div className="override-btn-group">
              <button 
                className={`btn-action btn-override ${settings.override_mode === 'LANE_1' ? 'btn-active' : ''}`}
                onClick={() => triggerOverride('LANE_1')}
              >
                🟢 Force Green Lane 1
              </button>
              <button 
                className={`btn-action btn-override ${settings.override_mode === 'LANE_2' ? 'btn-active' : ''}`}
                onClick={() => triggerOverride('LANE_2')}
              >
                🟢 Force Green Lane 2
              </button>
              <button 
                className={`btn-action btn-override btn-emergency ${settings.override_mode === 'EMERGENCY' ? 'btn-active' : ''}`}
                onClick={() => triggerOverride('EMERGENCY')}
              >
                🚨 Activate Emergency Corridor
              </button>
              {settings.override_mode !== 'AUTO' && (
                <button 
                  className="btn-action btn-green"
                  onClick={() => triggerOverride('AUTO')}
                >
                  🔄 Reset Override (Auto Mode)
                </button>
              )}
            </div>
          </div>

          <h4 className="sub-section-title">🔌 EDGE HARDWARE STATUS</h4>
          <div className="hardware-telemetry-text">
            <div>• Raspberry Pi GPIO: <strong className="text-green">{hardware.rpi_gpio_status || 'ACTIVE'}</strong></div>
            <div>• Arduino Serial Link: <strong className="text-cyan">{hardware.arduino_usb_status || 'CONNECTED'}</strong></div>
            <div>• VMS Signage Matrix: <strong className="text-amber">{hardware.vms_matrix || 'ACTIVE (LIMIT 60)'}</strong></div>
            <div>• Solar Battery Charge: <strong className="text-green">{hardware.solar_power || '14.2V (96%)'}</strong></div>
            <div>• Air Quality Index: <strong className="text-green">CO2: {hardware.air_quality?.co2_ppm || 450} ppm | PM2.5: {hardware.air_quality?.pm25_ugm3 || 18} µg/m³</strong></div>
            <div>• Edge Processing FPS: <strong className="text-amber">{hardware.edge_fps || 25} FPS</strong></div>
          </div>
        </div>
      </div>

      {/* Secondary Panels: GPS Map & ANPR List */}
      <div className="grid-2" style={{ marginBottom: 20 }}>
        <div className="glass-panel">
          <h3 className="panel-title">
            <MapPin size={16} /> LIVE CAMERA NODES MAP
          </h3>
          <div ref={mapContainerRef} className="map-view" style={{ height: 280 }} />
        </div>

        <div className="glass-panel">
          <h3 className="panel-title text-amber">
            <CheckCircle size={16} /> ANPR LICENSE PLATE ENFORCEMENT & TICKETING
          </h3>
          <div className="anpr-scroller">
            {anprList.length > 0 ? (
              anprList.map((item, idx) => (
                <div key={idx} className="anpr-item">
                  <div>
                    <strong className="text-amber">🏷️ {item.plate_number || 'DL-01-AB-1234'}</strong> 
                    <span className="vehicle-class-tag">({item.vehicle_type || 'car'})</span>
                  </div>
                  <div className="anpr-actions">
                    <span className="speed-marker text-red">{Math.round(item.speed_kmh || 85)} km/h</span>
                    <span className="violation-badge">E-CHALLAN ISSUED</span>
                  </div>
                </div>
              ))
            ) : (
              <p className="empty-scroller-text">Scanning active camera feeds for license plates...</p>
            )}
          </div>
        </div>
      </div>

      {/* Admin Settings & Portal Database Audits */}
      <div className="grid-2-custom">
        {/* Settings and Voice Tuning */}
        <div className="glass-panel">
          <h3 className="panel-title text-purple">
            <Settings size={18} /> AI VOICE & CONTROL INTERSECTION SETTINGS
          </h3>
          
          <div className="settings-controls">
            <div className="settings-toggle">
              <label>🗣️ Client AI Voice Alerts:</label>
              <input 
                type="checkbox"
                checked={clientSpeechEnabled}
                onChange={(e) => {
                  setClientSpeechEnabled(e.target.checked);
                  speakText(e.target.checked ? "AI Voice enabled." : "");
                }}
              />
            </div>

            <div className="settings-slider">
              <label>Speed Level Volume ({settings.voice_volume}):</label>
              <input 
                type="range" 
                min="0.1" 
                max="1.0" 
                step="0.1"
                value={settings.voice_volume}
                onChange={(e) => {
                  const vol = parseFloat(e.target.value);
                  setSettings(prev => ({ ...prev, voice_volume: vol }));
                  updateSettingsAPI({ voice_volume: vol });
                }}
              />
            </div>

            <div className="settings-slider">
              <label>Speech Rate speed ({settings.voice_rate}):</label>
              <input 
                type="range" 
                min="100" 
                max="220" 
                step="10"
                value={settings.voice_rate}
                onChange={(e) => {
                  const rate = parseInt(e.target.value);
                  setSettings(prev => ({ ...prev, voice_rate: rate }));
                  updateSettingsAPI({ voice_rate: rate });
                }}
              />
            </div>

            <div className="settings-select">
              <label>Intersection Feeds Switcher:</label>
              <select 
                value={settings.active_node}
                onChange={(e) => {
                  const nodeId = e.target.value;
                  setSettings(prev => ({ ...prev, active_node: nodeId }));
                  updateNode(nodeId);
                }}
              >
                <option value="node_1">📹 Node 1: Connaught Place Intersection</option>
                <option value="node_2">📹 Node 2: AIIMS Ring Road Signal</option>
                <option value="node_3">📹 Node 3: Cyber Hub Highway Express</option>
              </select>
            </div>
            
            <div style={{ marginTop: 15 }}>
              <a href="http://localhost:5000/report" target="_blank" rel="noreferrer">
                <button className="btn-action btn-green" style={{ width: '100%', justifyContent: 'center' }}>
                  <FileText size={16} /> Generate & View Executive PDF Report
                </button>
              </a>
            </div>
          </div>
        </div>

        {/* Database Health and Login Audit History */}
        <div className="glass-panel">
          <h3 className="panel-title text-cyan">
            <Database size={18} /> PORTAL AUDIT LOGS & DATABASE HEALTH
          </h3>
          <div className="db-health-badge-group">
            <div className={`db-health-badge ${dbStatus.mysql_active ? 'online' : 'offline'}`}>
              MySQL Database: {dbStatus.mysql_mode}
            </div>
            <div className={`db-health-badge ${dbStatus.mongodb_connected ? 'online' : 'offline'}`}>
              MongoDB Compass: {dbStatus.mongodb_mode}
            </div>
          </div>

          <h4 className="sub-section-title">🕒 Portal Access logs (Stored in MongoDB)</h4>
          <div className="audit-scroller">
            {sessionLogs.length > 0 ? (
              sessionLogs.map((log, idx) => (
                <div key={idx} className="audit-item">
                  <div>
                    <strong>{log.username}</strong> ({log.role})
                  </div>
                  <div>
                    <span className={`audit-action-badge ${log.action}`}>{log.action.toUpperCase()}</span>
                    <span className="audit-time">{new Date(log.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))
            ) : (
              <p className="empty-scroller-text">No logins logged yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
