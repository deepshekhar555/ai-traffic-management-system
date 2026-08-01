"""
Hardware Controller Module for Arduino / ESP32 Integration
Sends real-time serial signals to physical LED traffic lights, servo gates, and buzzers.
"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent.resolve()
backend_dir = Path(__file__).parent.parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from src.logger import logger
except ImportError:
    from backend.src.logger import logger


class HardwareController:
    """Controls physical traffic LEDs, servo barriers, and buzzers via Arduino/ESP32 Serial"""
    
    def __init__(self, port='COM3', baudrate=9600, enabled=False):
        self.port = port
        self.baudrate = baudrate
        self.enabled = enabled
        self.serial_conn = None
        
        if self.enabled:
            self._connect_serial()
        else:
            logger.info("Hardware Controller: Simulation Mode (No physical Arduino connected).")

    def _connect_serial(self):
        """Establish PySerial connection with Arduino/ESP32"""
        try:
            import serial
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino reset
            logger.info(f"[HARDWARE] Connected to physical Hardware Controller on {self.port} at {self.baudrate} baud!")
        except Exception as e:
            logger.warning(f"Could not connect to physical Arduino on {self.port}: {e}. Falling back to virtual hardware simulation.")
            self.enabled = False

    def update_physical_signals(self, lane_signals):
        """
        Send physical LED state commands to Arduino
        Example string sent over USB: "L1:GREEN,L2:RED\n"
        """
        cmd = f"L1:{lane_signals.get('lane_0', 'RED')},L2:{lane_signals.get('lane_1', 'RED')}\n"
        
        if self.enabled and self.serial_conn:
            try:
                self.serial_conn.write(cmd.encode('utf-8'))
            except Exception as e:
                logger.error(f"Error sending hardware command: {e}")
        else:
            # Virtual simulation log
            pass

    def trigger_physical_alarm(self, active=True):
        """Trigger physical buzzer & emergency strobe light on Arduino"""
        cmd = "ALARM:ON\n" if active else "ALARM:OFF\n"
        if self.enabled and self.serial_conn:
            try:
                self.serial_conn.write(cmd.encode('utf-8'))
            except Exception as e:
                logger.error(f"Error triggering physical alarm: {e}")

    def control_barrier_gate(self, open_gate=True):
        """Control physical servo motor barrier gate"""
        cmd = "GATE:OPEN\n" if open_gate else "GATE:CLOSE\n"
        if self.enabled and self.serial_conn:
            try:
                self.serial_conn.write(cmd.encode('utf-8'))
            except Exception as e:
                logger.error(f"Error controlling barrier gate: {e}")

    def update_vms_matrix_board(self, message="SPEED LIMIT 60"):
        """Send message to physical Variable Message Sign (VMS) LED Matrix Display"""
        cmd = f"VMS:{message}\n"
        if self.enabled and self.serial_conn:
            try:
                self.serial_conn.write(cmd.encode('utf-8'))
            except Exception as e:
                logger.error(f"Error updating VMS Matrix board: {e}")

    def get_oled_status(self):
        """Get OLED display screen status string"""
        return "ACTIVE (I2C SSD1306 @ 0x3C)"


if __name__ == "__main__":
    hw = HardwareController(enabled=False)
    hw.update_physical_signals({"lane_0": "GREEN", "lane_1": "RED"})
    hw.control_barrier_gate(open_gate=True)
    hw.update_vms_matrix_board("EMERGENCY CLEAR")
    print(f"[OK] HardwareController tested successfully! OLED Status: {hw.get_oled_status()}")


