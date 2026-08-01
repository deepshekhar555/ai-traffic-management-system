import sys
from pathlib import Path
from datetime import datetime

try:
    from src.logger import logger
except ImportError:
    try:
        from backend.src.logger import logger
    except ImportError:
        import logging
        logger = logging.getLogger("mysql_db")

class MySQLDatabase:
    """
    MySQL Database wrapper that handles table creation and query execution.
    Can be used by TrafficDatabase if a MySQL server is running.
    """
    def __init__(self, host="localhost", user="root", password="", database="traffic_db"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.is_connected = False
        
        self.connect()

    def connect(self):
        """Establish connection and create database/tables if needed"""
        try:
            import mysql.connector
            # First connect without database to create database if it doesn't exist
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                connect_timeout=2
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            cursor.close()
            conn.close()

            # Now connect to the database
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                connect_timeout=2
            )
            self.is_connected = True
            self.init_tables()
            logger.info(f"MySQL connected successfully at {self.host}/{self.database}")
            return True
        except Exception as e:
            self.is_connected = False
            self.conn = None
            logger.warning(f"MySQL connection failed: {e}. TrafficDatabase will fall back to SQLite.")
            return False

    def init_tables(self):
        """Create necessary MySQL tables"""
        if not self.is_connected or not self.conn:
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Vehicles table
            cursor.execute('''CREATE TABLE IF NOT EXISTS vehicles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                track_id INT,
                speed_kmh FLOAT,
                class_name VARCHAR(50),
                confidence FLOAT,
                position_x INT,
                position_y INT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Violations table
            cursor.execute('''CREATE TABLE IF NOT EXISTS violations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                vehicle_id INT,
                violation_type VARCHAR(100),
                speed_kmh FLOAT,
                speed_limit FLOAT,
                excess_speed FLOAT,
                location VARCHAR(255),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Accidents table
            cursor.execute('''CREATE TABLE IF NOT EXISTS accidents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                vehicle_ids TEXT,
                accident_type VARCHAR(100),
                details TEXT,
                location VARCHAR(255),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Emergency calls table
            cursor.execute('''CREATE TABLE IF NOT EXISTS emergency_calls (
                id INT AUTO_INCREMENT PRIMARY KEY,
                service_type VARCHAR(100),
                incident_type VARCHAR(100),
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Daily stats table
            cursor.execute('''CREATE TABLE IF NOT EXISTS daily_stats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                stat_date DATE UNIQUE,
                vehicles_detected INT,
                avg_speed FLOAT,
                max_speed FLOAT,
                speeding_violations INT,
                accidents INT,
                emergency_calls INT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # ANPR table
            cursor.execute('''CREATE TABLE IF NOT EXISTS anpr_violations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                plate_number VARCHAR(50),
                vehicle_type VARCHAR(50),
                speed_kmh FLOAT,
                violation_type VARCHAR(100),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Error initializing MySQL tables: {e}")
            self.is_connected = False

    def execute_query(self, query, params=(), commit=False, fetch=False):
        """Execute standard SQL query. Auto-reconnects if disconnected."""
        if not self.is_connected or not self.conn:
            # Try to reconnect
            if not self.connect():
                raise ConnectionError("MySQL not connected")
        
        try:
            # Check connection
            self.conn.ping(reconnect=True, attempts=3, delay=1)
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute(query, params)
            
            result = None
            if fetch:
                result = cursor.fetchall()
            
            if commit:
                self.conn.commit()
                
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"MySQL query execution failed: {e}. Query: {query}")
            # Try to force reconnect next time
            self.is_connected = False
            raise e
