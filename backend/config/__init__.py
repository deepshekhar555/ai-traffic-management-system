"""Initialize config package"""

try:
    from .config import *
except ImportError:
    try:
        from config import *
    except ImportError:
        pass

if __name__ == "__main__":
    print("[OK] Config package initialized successfully!")

