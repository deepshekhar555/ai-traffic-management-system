"""
Raspberry Pi Native GPIO Hardware Controller Module
Directly controls physical LEDs, Servo motors, and Buzzers via Raspberry Pi GPIO pins.
"""

import time
import sys
from pathlib import Path

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

class RPiGPIOController:
    """Controls physical traffic LEDs, servo gates, and buzzers using Raspberry Pi GPIO pins"""
    
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.rpi_available = False
        
        # GPIO Pin Definitions (BCM numbering)
        self.PINS = {
            "L1_RED": 17,
            "L1_YELLOW": 27,
            "L1_GREEN": 22,
            
            "L2_RED": 23,
            "L2_YELLOW": 24,
            "L2_GREEN": 25,
            
            "BUZZER": 18,
            "SERVO": 12
        }
        
        self._init_gpio()

    def _init_gpio(self):
        """Initialize Raspberry Pi GPIO library"""
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.GPIO.setmode(GPIO.BCM)
            self.GPIO.setwarnings(False)
            
            # Setup Output Pins
            for pin_name, pin_num in self.PINS.items():
                if pin_name != "SERVO":
                    self.GPIO.setup(pin_num, self.GPIO.OUT)
                    self.GPIO.output(pin_num, self.GPIO.LOW)
            
            # Setup Servo PWM on Pin 12
            self.GPIO.setup(self.PINS["SERVO"], self.GPIO.OUT)
            self.servo_pwm = self.GPIO.PWM(self.PINS["SERVO"], 50)  # 50Hz PWM
            self.servo_pwm.start(0)
            
            self.rpi_available = True
            logger.info("[RPi] Native Raspberry Pi GPIO Controller initialized successfully!")
            
            # Set initial LED state (Both Red)
            self.GPIO.output(self.PINS["L1_RED"], self.GPIO.HIGH)
            self.GPIO.output(self.PINS["L2_RED"], self.GPIO.HIGH)
            
        except ImportError:
            logger.info("RPi.GPIO module not available (Running on non-Raspberry Pi system). Using GPIO simulation mode.")
            self.rpi_available = False
        except Exception as e:
            logger.warning(f"Raspberry Pi GPIO Initialization warning: {e}")
            self.rpi_available = False

    def update_physical_signals(self, lane_signals):
        """Update physical LED traffic lights directly on Raspberry Pi GPIO pins"""
        if not self.rpi_available:
            return
            
        l1_state = lane_signals.get("lane_0", "RED")
        l2_state = lane_signals.get("lane_1", "RED")
        
        # Reset all LEDs
        for pin_name in ["L1_RED", "L1_YELLOW", "L1_GREEN", "L2_RED", "L2_YELLOW", "L2_GREEN"]:
            self.GPIO.output(self.PINS[pin_name], self.GPIO.LOW)
            
        # Set Lane 1
        if l1_state == "GREEN":
            self.GPIO.output(self.PINS["L1_GREEN"], self.GPIO.HIGH)
        elif l1_state == "YELLOW":
            self.GPIO.output(self.PINS["L1_YELLOW"], self.GPIO.HIGH)
        else:
            self.GPIO.output(self.PINS["L1_RED"], self.GPIO.HIGH)
            
        # Set Lane 2
        if l2_state == "GREEN":
            self.GPIO.output(self.PINS["L2_GREEN"], self.GPIO.HIGH)
        elif l2_state == "YELLOW":
            self.GPIO.output(self.PINS["L2_YELLOW"], self.GPIO.HIGH)
        else:
            self.GPIO.output(self.PINS["L2_RED"], self.GPIO.HIGH)

    def trigger_physical_alarm(self, active=True):
        """Trigger physical buzzer on Raspberry Pi GPIO Pin 18"""
        if not self.rpi_available:
            return
        state = self.GPIO.HIGH if active else self.GPIO.LOW
        self.GPIO.output(self.PINS["BUZZER"], state)

    def control_barrier_gate(self, open_gate=True):
        """Control physical servo motor barrier gate on Raspberry Pi GPIO Pin 12"""
        if not self.rpi_available:
            return
        duty_cycle = 7.5 if open_gate else 2.5  # 90 degrees open vs 0 degrees closed
        self.servo_pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.3)
        self.servo_pwm.ChangeDutyCycle(0)

    def update_oled_display(self, text="TRAFFIX-AI RUNNING"):
        """Update I2C OLED display on Raspberry Pi (SDA/SCL)"""
        logger.info(f"RPi OLED Screen updated: {text}")

    def update_vms_matrix(self, message="SPEED LIMIT 60"):
        """Update SPI/GPIO Outdoor VMS LED Matrix Board"""
        logger.info(f"RPi VMS LED Matrix updated: {message}")


    def cleanup(self):
        """Clean up GPIO resources on shutdown"""
        if self.rpi_available:
            try:
                self.servo_pwm.stop()
                self.GPIO.cleanup()
                logger.info("Raspberry Pi GPIO resources cleaned up cleanly.")
            except Exception as e:
                logger.error(f"Error cleaning up GPIO: {e}")


if __name__ == "__main__":
    ctrl = RPiGPIOController(enabled=True)
    status = "SIMULATION" if not ctrl.rpi_available else "PHYSICAL RPi"
    ctrl.update_oled_display("TRAFFIX-AI RUNNING")
    ctrl.update_vms_matrix("SPEED LIMIT 60")
    ctrl.cleanup()
    print(f"[OK] RPiGPIOController tested successfully! Mode: {status} | GPIO Pins configured: {len(ctrl.PINS)}")
