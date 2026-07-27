"""
Logging configuration for AI Traffic Management System
"""

import logging
import sys
from pathlib import Path

_backend_dir = Path(__file__).parent.parent.resolve()
_root_dir = Path(__file__).parent.parent.parent.resolve()
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

try:
    from config.config import LOG_FILE, LOG_LEVEL
except ImportError:
    from backend.config.config import LOG_FILE, LOG_LEVEL


# Configure logger
logger = logging.getLogger("traffic_ai")
logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

# Create handlers
if not logger.handlers:
    # File handler
    LOG_FILE.parent.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # Console handler with stdout wrapper or safe encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


if __name__ == "__main__":
    logger.info("Logger self-test: INFO level")
    logger.warning("Logger self-test: WARNING level")
    print(f"[OK] Logger tested successfully! Log file: '{LOG_FILE}' | Level: '{LOG_LEVEL}'")
