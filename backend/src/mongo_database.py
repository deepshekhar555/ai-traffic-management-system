import os
import json
import time
from datetime import datetime
from pathlib import Path

# Paths
_backend_dir = Path(__file__).parent.parent.resolve()
_root_dir = Path(__file__).parent.parent.parent.resolve()
DATA_DIR = _root_dir / "data"
DATA_DIR.mkdir(exist_ok=True)

FALLBACK_FILE = DATA_DIR / "mongo_fallback.json"

try:
    from src.logger import logger
except ImportError:
    try:
        from backend.src.logger import logger
    except ImportError:
        import logging
        logger = logging.getLogger("mongo_db")

class MongoDatabase:
    """
    MongoDB Database connector storing login portal credentials, 
    login audit logs, and settings. Automatically falls back to a 
    local JSON database if MongoDB Compass / daemon is offline.
    """
    def __init__(self, uri="mongodb://localhost:27017", db_name="traffix_db"):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None
        self.is_fallback = False
        
        self.connect()
        self.seed_defaults()

    def connect(self):
        """Try connecting to MongoDB server, fallback if unavailable"""
        try:
            import pymongo
            # Set short timeout so we don't block the app startup for too long if offline
            self.client = pymongo.MongoClient(self.uri, serverSelectionTimeoutMS=1500)
            # Test connection
            self.client.server_info()
            self.db = self.client[self.db_name]
            self.is_fallback = False
            logger.info(f"MongoDB connected successfully at {self.uri}")
        except Exception as e:
            self.is_fallback = True
            logger.warning(f"MongoDB connection failed: {e}. Falling back to local JSON database: {FALLBACK_FILE}")
            self._init_fallback_file()

    def _init_fallback_file(self):
        """Initialize local fallback file if not present"""
        if not FALLBACK_FILE.exists():
            data = {
                "users": [],
                "login_logs": [],
                "system_status": {
                    "voice_enabled": True,
                    "voice_rate": 150,
                    "voice_volume": 0.9,
                    "active_node": "node_1",
                    "override_mode": "AUTO",
                    "last_updated": datetime.now().isoformat()
                }
            }
            with open(FALLBACK_FILE, "w") as f:
                json.dump(data, f, indent=2)

    def _read_fallback(self):
        self._init_fallback_file()
        try:
            with open(FALLBACK_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading JSON fallback: {e}")
            return {"users": [], "login_logs": [], "system_status": {}}

    def _write_fallback(self, data):
        try:
            with open(FALLBACK_FILE, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error writing JSON fallback: {e}")
            return False

    def seed_defaults(self):
        """Seed default admin and customer accounts"""
        default_users = [
            {"username": "admin", "password": "admin123", "role": "admin"},
            {"username": "customer", "password": "customer123", "role": "customer"}
        ]
        
        if not self.is_fallback:
            try:
                users_col = self.db["users"]
                for user in default_users:
                    if not users_col.find_one({"username": user["username"]}):
                        users_col.insert_one({
                            "username": user["username"],
                            "password": user["password"],  # In production, use hashed passwords
                            "role": user["role"],
                            "created_at": datetime.now()
                        })
                
                # Seed settings status
                status_col = self.db["system_status"]
                if status_col.count_documents({}) == 0:
                    status_col.insert_one({
                        "voice_enabled": True,
                        "voice_rate": 150,
                        "voice_volume": 0.9,
                        "active_node": "node_1",
                        "override_mode": "AUTO",
                        "last_updated": datetime.now()
                    })
            except Exception as e:
                logger.error(f"Failed to seed defaults in Mongo, switching to fallback: {e}")
                self.is_fallback = True
                self._init_fallback_file()
                
        if self.is_fallback:
            data = self._read_fallback()
            for user in default_users:
                exists = any(u["username"] == user["username"] for u in data["users"])
                if not exists:
                    data["users"].append({
                        "username": user["username"],
                        "password": user["password"],
                        "role": user["role"],
                        "created_at": datetime.now().isoformat()
                    })
            self._write_fallback(data)

    def verify_login(self, username, password, role):
        """Verify login credentials"""
        if not self.is_fallback:
            try:
                users_col = self.db["users"]
                user = users_col.find_one({"username": username, "password": password, "role": role})
                if user:
                    self.log_login_event(username, role, "login_success")
                    return True
                self.log_login_event(username, role, "login_failed")
                return False
            except Exception as e:
                logger.error(f"Mongo verify_login error: {e}. Switching to fallback.")
                self.is_fallback = True
                
        # Fallback Mode
        data = self._read_fallback()
        user = next((u for u in data["users"] if u["username"] == username and u["password"] == password and u["role"] == role), None)
        if user:
            self.log_login_event(username, role, "login_success")
            return True
        self.log_login_event(username, role, "login_failed")
        return False

    def log_login_event(self, username, role, action):
        """Log login history details"""
        log_entry = {
            "username": username,
            "role": role,
            "action": action,
            "timestamp": datetime.now().isoformat() if self.is_fallback else datetime.now()
        }
        
        if not self.is_fallback:
            try:
                self.db["login_logs"].insert_one(log_entry)
                return True
            except Exception as e:
                logger.error(f"Mongo logging error: {e}")
                self.is_fallback = True
                
        # Fallback Mode
        data = self._read_fallback()
        # Convert timestamp to string if it isn't
        if not isinstance(log_entry["timestamp"], str):
            log_entry["timestamp"] = log_entry["timestamp"].isoformat()
        data["login_logs"].append(log_entry)
        # Keep logs capped to last 100 entries in fallback
        data["login_logs"] = data["login_logs"][-100:]
        self._write_fallback(data)
        return True

    def get_login_logs(self, limit=30):
        """Get recent login logs"""
        if not self.is_fallback:
            try:
                logs_col = self.db["login_logs"]
                logs = list(logs_col.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
                # Convert datetime object to string
                for log in logs:
                    if isinstance(log.get("timestamp"), datetime):
                        log["timestamp"] = log["timestamp"].isoformat()
                return logs
            except Exception as e:
                logger.error(f"Mongo get_login_logs error: {e}")
                self.is_fallback = True
                
        # Fallback Mode
        data = self._read_fallback()
        logs = data["login_logs"]
        return sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def get_system_status(self):
        """Get the latest system configuration status"""
        if not self.is_fallback:
            try:
                status_col = self.db["system_status"]
                status = status_col.find_one({}, {"_id": 0})
                if status:
                    if isinstance(status.get("last_updated"), datetime):
                        status["last_updated"] = status["last_updated"].isoformat()
                    return status
            except Exception as e:
                logger.error(f"Mongo get_system_status error: {e}")
                self.is_fallback = True

        # Fallback Mode
        data = self._read_fallback()
        return data["system_status"]

    def update_system_status(self, updates: dict):
        """Update system config settings in database"""
        if not self.is_fallback:
            try:
                status_col = self.db["system_status"]
                updates["last_updated"] = datetime.now()
                status_col.update_many({}, {"$set": updates})
                return True
            except Exception as e:
                logger.error(f"Mongo update_system_status error: {e}")
                self.is_fallback = True

        # Fallback Mode
        data = self._read_fallback()
        status = data["system_status"]
        for k, v in updates.items():
            status[k] = v
        status["last_updated"] = datetime.now().isoformat()
        data["system_status"] = status
        self._write_fallback(data)
        return True

    def get_database_health(self):
        """Returns connection states for diagnostic panels"""
        return {
            "mongodb_connected": not self.is_fallback,
            "mongodb_mode": "Compass/Daemon Active" if not self.is_fallback else "Local JSON Fallback Mode"
        }

if __name__ == "__main__":
    db = MongoDatabase()
    print("Testing Auth verification (Admin):", db.verify_login("admin", "admin123", "admin"))
    print("Testing Auth verification (Customer):", db.verify_login("customer", "customer123", "customer"))
    print("Recent Logs:", db.get_login_logs())
    print("Health Status:", db.get_database_health())
