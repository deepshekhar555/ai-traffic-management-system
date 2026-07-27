"""SQLite database for traffic events and statistics"""

import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json

_backend_dir = Path(__file__).parent.parent.resolve()
_root_dir = Path(__file__).parent.parent.parent.resolve()
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

try:
    from src.logger import logger
except ImportError:
    from backend.src.logger import logger


class TrafficDatabase:
    """
    SQLite database for storing all traffic events
    Includes vehicles, violations, accidents, and statistics
    """
    
    def __init__(self, db_path='traffic_data.db'):
        db_path_obj = Path(db_path)
        if not db_path_obj.is_absolute():
            # Put database in the project data directory
            data_dir = _root_dir / "data"
            data_dir.mkdir(exist_ok=True)
            self.db_path = str(data_dir / db_path)
        else:
            self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create all necessary tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Vehicles table - log every detection
        c.execute('''CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER,
            speed_kmh REAL,
            class_name TEXT,
            confidence REAL,
            position_x INTEGER,
            position_y INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Violations table - speeding, wrong-way, etc
        c.execute('''CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER,
            violation_type TEXT,
            speed_kmh REAL,
            speed_limit REAL,
            excess_speed REAL,
            location TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Accidents table - collision events
        c.execute('''CREATE TABLE IF NOT EXISTS accidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_ids TEXT,  -- JSON array
            accident_type TEXT,
            details TEXT,  -- JSON
            location TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Emergency calls table
        c.execute('''CREATE TABLE IF NOT EXISTS emergency_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_type TEXT,
            incident_type TEXT,
            details TEXT,  -- JSON
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # System statistics
        c.execute('''CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stat_date DATE UNIQUE,
            vehicles_detected INTEGER,
            avg_speed REAL,
            max_speed REAL,
            speeding_violations INTEGER,
            accidents INTEGER,
            emergency_calls INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # ANPR License Plates Table
        c.execute('''CREATE TABLE IF NOT EXISTS anpr_violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT,
            vehicle_type TEXT,
            speed_kmh REAL,
            violation_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized: {self.db_path}")

    def log_anpr_violation(self, plate_number, vehicle_type, speed_kmh, violation_type="Speeding"):
        """Log ANPR license plate violation"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''INSERT INTO anpr_violations (plate_number, vehicle_type, speed_kmh, violation_type)
                        VALUES (?, ?, ?, ?)''', (plate_number, vehicle_type, speed_kmh, violation_type))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error logging ANPR violation: {e}")
            return False

    def get_anpr_violations_today(self):
        """Get today's ANPR license plate violations"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            today = datetime.now().date()
            c.execute('''SELECT * FROM anpr_violations WHERE DATE(timestamp) = ? ORDER BY timestamp DESC LIMIT 50''', (today,))
            results = [dict(row) for row in c.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting ANPR violations: {e}")
            return []
    
    def log_vehicle(self, track_id, speed_kmh, class_name, confidence, position=None):
        """Log detected vehicle"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            pos_x, pos_y = position if position else (0, 0)
            
            c.execute('''INSERT INTO vehicles 
                        (track_id, speed_kmh, class_name, confidence, position_x, position_y)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (track_id, speed_kmh, class_name, confidence, pos_x, pos_y))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error logging vehicle: {e}")
            return False
    
    def log_violation(self, vehicle_id, violation_type, speed_kmh, speed_limit=60, location='Unknown'):
        """Log speeding or other violation"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            excess = speed_kmh - speed_limit
            
            c.execute('''INSERT INTO violations 
                        (vehicle_id, violation_type, speed_kmh, speed_limit, excess_speed, location)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (vehicle_id, violation_type, speed_kmh, speed_limit, excess, location))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error logging violation: {e}")
            return False
    
    def log_accident(self, vehicle_ids, accident_type, details, location='Unknown'):
        """Log accident"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''INSERT INTO accidents 
                        (vehicle_ids, accident_type, details, location)
                        VALUES (?, ?, ?, ?)''',
                     (json.dumps(vehicle_ids), accident_type, json.dumps(details), location))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error logging accident: {e}")
            return False
    
    def log_emergency_call(self, service_type, incident_type, details):
        """Log emergency service call"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''INSERT INTO emergency_calls 
                        (service_type, incident_type, details)
                        VALUES (?, ?, ?)''',
                     (service_type, incident_type, json.dumps(details)))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error logging emergency call: {e}")
            return False
    
    def get_todays_statistics(self):
        """Get statistics for today"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            today = datetime.now().date()
            
            # Vehicles detected
            vehicles = c.execute(
                'SELECT COUNT(DISTINCT track_id) FROM vehicles WHERE DATE(timestamp) = ?',
                (today,)
            ).fetchone()[0]
            
            # Violations
            violations = c.execute(
                'SELECT COUNT(*) FROM violations WHERE DATE(timestamp) = ?',
                (today,)
            ).fetchone()[0]
            
            # Accidents
            accidents = c.execute(
                'SELECT COUNT(*) FROM accidents WHERE DATE(timestamp) = ?',
                (today,)
            ).fetchone()[0]
            
            # Emergency calls
            calls = c.execute(
                'SELECT COUNT(*) FROM emergency_calls WHERE DATE(timestamp) = ?',
                (today,)
            ).fetchone()[0]
            
            # Average speed
            avg_speed_row = c.execute(
                'SELECT AVG(speed_kmh) FROM vehicles WHERE DATE(timestamp) = ?',
                (today,)
            ).fetchone()
            avg_speed = avg_speed_row[0] if avg_speed_row[0] else 0
            
            # Max speed
            max_speed_row = c.execute(
                'SELECT MAX(speed_kmh) FROM vehicles WHERE DATE(timestamp) = ?',
                (today,)
            ).fetchone()
            max_speed = max_speed_row[0] if max_speed_row[0] else 0
            
            conn.close()
            
            return {
                'date': today.isoformat(),
                'vehicles_detected': vehicles,
                'avg_speed_kmh': round(avg_speed, 1),
                'max_speed_kmh': round(max_speed, 1),
                'speeding_violations': violations,
                'accidents': accidents,
                'emergency_calls': calls
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def get_violations_today(self):
        """Get today's violations"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            today = datetime.now().date()
            
            c.execute('''SELECT * FROM violations 
                        WHERE DATE(timestamp) = ? 
                        ORDER BY timestamp DESC
                        LIMIT 50''', (today,))
            
            violations = [dict(row) for row in c.fetchall()]
            conn.close()
            return violations
        except Exception as e:
            logger.error(f"Error getting violations: {e}")
            return []
    
    def get_top_violators(self, days=1):
        """Get vehicles with most violations"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            cutoff_date = (datetime.now() - timedelta(days=days)).date()
            
            c.execute('''SELECT vehicle_id, COUNT(*) as count, AVG(excess_speed) as avg_excess
                        FROM violations 
                        WHERE DATE(timestamp) >= ?
                        GROUP BY vehicle_id
                        ORDER BY count DESC
                        LIMIT 10''', (cutoff_date,))
            
            violators = [{'vehicle_id': row[0], 'violations': row[1], 'avg_excess': row[2]}
                        for row in c.fetchall()]
            conn.close()
            return violators
        except Exception as e:
            logger.error(f"Error getting top violators: {e}")
            return []
    
    def get_vehicle_history(self, vehicle_id, limit=100):
        """Get history for specific vehicle"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute('''SELECT * FROM vehicles WHERE track_id = ? ORDER BY timestamp DESC LIMIT ?''',
                     (vehicle_id, limit))
            
            history = [dict(row) for row in c.fetchall()]
            conn.close()
            return history
        except Exception as e:
            logger.error(f"Error getting vehicle history: {e}")
            return []
    
    def export_daily_report(self, export_path='daily_report.json'):
        """Export daily statistics to JSON"""
        try:
            path_obj = Path(export_path)
            if not path_obj.is_absolute():
                reports_dir = _root_dir / "reports"
                reports_dir.mkdir(exist_ok=True)
                export_path = str(reports_dir / export_path)
                
            stats = self.get_todays_statistics()
            violations = self.get_violations_today()
            top_violators = self.get_top_violators()
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'statistics': stats,
                'recent_violations': violations[:20],
                'top_violators': top_violators
            }
            
            with open(export_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Report exported to {export_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return False


if __name__ == "__main__":
    db = TrafficDatabase(db_path="traffic_data_test.db")
    # Log test records
    db.log_vehicle(track_id=1, speed_kmh=72.5, class_name="car", confidence=0.94, position=(400, 300))
    db.log_vehicle(track_id=2, speed_kmh=45.0, class_name="truck", confidence=0.91, position=(600, 300))
    db.log_violation(vehicle_id=1, violation_type="SPEEDING", speed_kmh=72.5, speed_limit=60)
    db.log_accident(vehicle_ids=[1, 3], accident_type="COLLISION", details={"iou": 0.35}, location="Junction A")
    db.log_emergency_call(service_type="Ambulance", incident_type="COLLISION", details={"lat": 40.71, "lon": -74.0})
    stats = db.get_todays_statistics()
    report_ok = db.export_daily_report("daily_report_test.json")
    print(f"[OK] TrafficDatabase tested successfully!")
    print(f"  Tables: vehicles, violations, accidents, emergency_calls, daily_stats, anpr_violations")
    print(f"  Today's Stats: Vehicles={stats.get('vehicles_detected',0)} | Violations={stats.get('speeding_violations',0)} | Avg Speed={stats.get('avg_speed_kmh',0)} km/h")
    print(f"  JSON Report exported: {report_ok}")
