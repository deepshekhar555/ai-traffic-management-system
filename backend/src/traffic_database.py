"""SQLite and MySQL database manager for traffic events and statistics"""

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
    from src.mysql_database import MySQLDatabase
except ImportError:
    try:
        from backend.src.logger import logger
        from backend.src.mysql_database import MySQLDatabase
    except ImportError:
        import logging
        logger = logging.getLogger("traffic_db")
        MySQLDatabase = None

class TrafficDatabase:
    """
    SQL Database Controller supporting both MySQL and SQLite.
    Includes automatic failover to local SQLite for high stability.
    """
    
    def __init__(self, db_path='traffic_data.db', use_mysql=True):
        db_path_obj = Path(db_path)
        if not db_path_obj.is_absolute():
            data_dir = _root_dir / "data"
            data_dir.mkdir(exist_ok=True)
            self.db_path = str(data_dir / db_path)
        else:
            self.db_path = db_path
            
        self.use_mysql = use_mysql
        self.mysql_db = None
        
        # Initialize SQLite database (always init tables just in case of failover)
        self.init_sqlite_database()
        
        # Try initializing MySQL database
        if self.use_mysql and MySQLDatabase is not None:
            try:
                self.mysql_db = MySQLDatabase(host="localhost", user="root", password="", database="traffic_db")
                if not self.mysql_db.is_connected:
                    logger.warning("MySQL connection offline. Operating in SQLite Mode.")
                    self.use_mysql = False
                else:
                    logger.info("Operating in MySQL Mode.")
            except Exception as e:
                logger.error(f"Failed to instantiate MySQLDatabase: {e}. Operating in SQLite Mode.")
                self.use_mysql = False
        else:
            self.use_mysql = False

    def init_sqlite_database(self):
        """Create SQLite tables if they do not exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
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
            
            c.execute('''CREATE TABLE IF NOT EXISTS accidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_ids TEXT,
                accident_type TEXT,
                details TEXT,
                location TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS emergency_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_type TEXT,
                incident_type TEXT,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            
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
            logger.info(f"SQLite database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing SQLite database: {e}")

    def execute_sql(self, query, params=(), commit=False, fetch=False):
        """Helper to run parameterized query against MySQL or SQLite fallback"""
        if self.use_mysql and self.mysql_db and self.mysql_db.is_connected:
            try:
                # Convert '?' placeholders to '%s' for MySQL
                mysql_query = query.replace('?', '%s')
                return self.mysql_db.execute_query(mysql_query, params, commit=commit, fetch=fetch)
            except Exception as e:
                logger.error(f"MySQL query error, failing back to SQLite: {e}")
                # We don't disable mysql globally, just perform query on sqlite
        
        # SQLite execution
        try:
            conn = sqlite3.connect(self.db_path)
            if fetch:
                conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(query, params)
            
            result = None
            if fetch:
                result = [dict(row) for row in c.fetchall()]
            
            if commit:
                conn.commit()
            
            conn.close()
            return result
        except Exception as e:
            logger.error(f"SQLite query failed: {e}. Query: {query}")
            return [] if fetch else False

    def log_anpr_violation(self, plate_number, vehicle_type, speed_kmh, violation_type="Speeding"):
        """Log ANPR license plate violation"""
        query = '''INSERT INTO anpr_violations (plate_number, vehicle_type, speed_kmh, violation_type)
                   VALUES (?, ?, ?, ?)'''
        params = (plate_number, vehicle_type, speed_kmh, violation_type)
        res = self.execute_sql(query, params, commit=True)
        return res is not False

    def get_anpr_violations_today(self):
        """Get today's ANPR license plate violations"""
        today = datetime.now().date().isoformat()
        query = '''SELECT * FROM anpr_violations WHERE DATE(timestamp) = ? ORDER BY timestamp DESC LIMIT 50'''
        res = self.execute_sql(query, (today,), fetch=True)
        # Format timestamps as string
        for row in res:
            if isinstance(row.get("timestamp"), datetime):
                row["timestamp"] = row["timestamp"].isoformat()
        return res
    
    def log_vehicle(self, track_id, speed_kmh, class_name, confidence, position=None):
        """Log detected vehicle"""
        pos_x, pos_y = position if position else (0, 0)
        query = '''INSERT INTO vehicles 
                   (track_id, speed_kmh, class_name, confidence, position_x, position_y)
                   VALUES (?, ?, ?, ?, ?, ?)'''
        params = (track_id, speed_kmh, class_name, confidence, pos_x, pos_y)
        res = self.execute_sql(query, params, commit=True)
        return res is not False
    
    def log_violation(self, vehicle_id, violation_type, speed_kmh, speed_limit=60, location='Unknown'):
        """Log speeding or other violation"""
        excess = speed_kmh - speed_limit
        query = '''INSERT INTO violations 
                   (vehicle_id, violation_type, speed_kmh, speed_limit, excess_speed, location)
                   VALUES (?, ?, ?, ?, ?, ?)'''
        params = (vehicle_id, violation_type, speed_kmh, speed_limit, excess, location)
        res = self.execute_sql(query, params, commit=True)
        return res is not False
    
    def log_accident(self, vehicle_ids, accident_type, details, location='Unknown'):
        """Log accident"""
        query = '''INSERT INTO accidents 
                   (vehicle_ids, accident_type, details, location)
                   VALUES (?, ?, ?, ?)'''
        params = (json.dumps(vehicle_ids), accident_type, json.dumps(details), location)
        res = self.execute_sql(query, params, commit=True)
        return res is not False
    
    def log_emergency_call(self, service_type, incident_type, details):
        """Log emergency service call"""
        query = '''INSERT INTO emergency_calls 
                   (service_type, incident_type, details)
                   VALUES (?, ?, ?)'''
        params = (service_type, incident_type, json.dumps(details))
        res = self.execute_sql(query, params, commit=True)
        return res is not False
    
    def get_todays_statistics(self):
        """Get statistics for today"""
        today = datetime.now().date().isoformat()
        
        try:
            # Vehicles detected count
            q_vehicles = 'SELECT COUNT(DISTINCT track_id) as count FROM vehicles WHERE DATE(timestamp) = ?'
            res_veh = self.execute_sql(q_vehicles, (today,), fetch=True)
            vehicles = res_veh[0]['count'] if res_veh else 0
            
            # Violations count
            q_violations = 'SELECT COUNT(*) as count FROM violations WHERE DATE(timestamp) = ?'
            res_viol = self.execute_sql(q_violations, (today,), fetch=True)
            violations = res_viol[0]['count'] if res_viol else 0
            
            # Accidents count
            q_accidents = 'SELECT COUNT(*) as count FROM accidents WHERE DATE(timestamp) = ?'
            res_acc = self.execute_sql(q_accidents, (today,), fetch=True)
            accidents = res_acc[0]['count'] if res_acc else 0
            
            # Emergency calls count
            q_calls = 'SELECT COUNT(*) as count FROM emergency_calls WHERE DATE(timestamp) = ?'
            res_calls = self.execute_sql(q_calls, (today,), fetch=True)
            calls = res_calls[0]['count'] if res_calls else 0
            
            # Average speed
            q_avg = 'SELECT AVG(speed_kmh) as val FROM vehicles WHERE DATE(timestamp) = ?'
            res_avg = self.execute_sql(q_avg, (today,), fetch=True)
            avg_speed = res_avg[0]['val'] if (res_avg and res_avg[0]['val'] is not None) else 0
            
            # Max speed
            q_max = 'SELECT MAX(speed_kmh) as val FROM vehicles WHERE DATE(timestamp) = ?'
            res_max = self.execute_sql(q_max, (today,), fetch=True)
            max_speed = res_max[0]['val'] if (res_max and res_max[0]['val'] is not None) else 0
            
            return {
                'date': today,
                'vehicles_detected': int(vehicles),
                'avg_speed_kmh': round(float(avg_speed), 1),
                'max_speed_kmh': round(float(max_speed), 1),
                'speeding_violations': int(violations),
                'accidents': int(accidents),
                'emergency_calls': int(calls)
            }
        except Exception as e:
            logger.error(f"Error compiling statistics: {e}")
            return {
                'date': today,
                'vehicles_detected': 0,
                'avg_speed_kmh': 0,
                'max_speed_kmh': 0,
                'speeding_violations': 0,
                'accidents': 0,
                'emergency_calls': 0
            }
    
    def get_violations_today(self):
        """Get today's violations"""
        today = datetime.now().date().isoformat()
        query = '''SELECT * FROM violations 
                   WHERE DATE(timestamp) = ? 
                   ORDER BY timestamp DESC
                   LIMIT 50'''
        res = self.execute_sql(query, (today,), fetch=True)
        # Format timestamps as string
        for row in res:
            if isinstance(row.get("timestamp"), datetime):
                row["timestamp"] = row["timestamp"].isoformat()
        return res
    
    def get_top_violators(self, days=1):
        """Get vehicles with most violations"""
        cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        
        # MySQL and SQLite support GROUP BY differently in strict mode. Standardize query.
        query = '''SELECT vehicle_id, COUNT(*) as count, AVG(excess_speed) as avg_excess
                    FROM violations 
                    WHERE DATE(timestamp) >= ?
                    GROUP BY vehicle_id
                    ORDER BY count DESC
                    LIMIT 10'''
        res = self.execute_sql(query, (cutoff_date,), fetch=True)
        
        violators = []
        if res:
            for row in res:
                violators.append({
                    'vehicle_id': row['vehicle_id'],
                    'violations': row['count'],
                    'avg_excess': round(float(row['avg_excess']), 1) if row['avg_excess'] is not None else 0
                })
        return violators
    
    def get_vehicle_history(self, vehicle_id, limit=100):
        """Get history for specific vehicle"""
        query = '''SELECT * FROM vehicles WHERE track_id = ? ORDER BY timestamp DESC LIMIT ?'''
        res = self.execute_sql(query, (vehicle_id, limit), fetch=True)
        for row in res:
            if isinstance(row.get("timestamp"), datetime):
                row["timestamp"] = row["timestamp"].isoformat()
        return res
    
    def get_challans_by_plate(self, plate_number):
        """Get e-challans issued to a specific plate (Customer Portal Feature)"""
        # Search plate_number case insensitively
        query = '''SELECT * FROM anpr_violations WHERE UPPER(plate_number) = UPPER(?) ORDER BY timestamp DESC'''
        res = self.execute_sql(query, (plate_number,), fetch=True)
        
        challans = []
        for idx, item in enumerate(res, 1):
            speed = item.get('speed_kmh', 85.0)
            fine = 5000 if speed > 100 else (2000 if speed > 80 else 1000)
            timestamp_val = item.get('timestamp')
            if isinstance(timestamp_val, datetime):
                timestamp_val = timestamp_val.isoformat()
                
            challans.append({
                "challan_id": f"CHALLAN-{100000 + item.get('id', idx)}",
                "plate_number": item.get('plate_number', plate_number),
                "vehicle_type": item.get('vehicle_type', 'car'),
                "speed_kmh": round(speed, 1),
                "fine_amount_inr": fine,
                "status": "ISSUED",
                "timestamp": timestamp_val
            })
        return challans

    def get_database_health(self):
        """Returns connection states for database configuration panel"""
        health = {
            "sqlite_db_path": self.db_path,
            "mysql_active": self.use_mysql
        }
        if self.use_mysql and self.mysql_db:
            health["mysql_mode"] = f"Connected ({self.mysql_db.host}/{self.mysql_db.database})"
        else:
            health["mysql_mode"] = "SQLite Fallback Mode (MySQL Server Offline)"
        return health

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
    db = TrafficDatabase(db_path="traffic_data_test.db", use_mysql=True)
    db.log_vehicle(track_id=1, speed_kmh=72.5, class_name="car", confidence=0.94, position=(400, 300))
    db.log_violation(vehicle_id=1, violation_type="SPEEDING", speed_kmh=72.5, speed_limit=60)
    db.log_anpr_violation(plate_number="DL-01-AB-1234", vehicle_type="car", speed_kmh=82.4, violation_type="Speeding")
    print("Database Health:", db.get_database_health())
    print("Challans for DL-01-AB-1234:", db.get_challans_by_plate("DL-01-AB-1234"))
    stats = db.get_todays_statistics()
    print("Today's stats:", stats)
