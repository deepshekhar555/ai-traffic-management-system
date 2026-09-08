import os
import cv2
import pygame

# Set dummy video driver to prevent opening a physical window
os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.simulation import RLIntersectionSim

class WebRLBridge:
    def __init__(self):
        pygame.init()
        self.surface = pygame.Surface((800, 600))
        self.sim = RLIntersectionSim(surface=self.surface)

    def get_frame(self):
        self.sim.update_step()
        self.sim.draw(self.surface)

        # Convert Pygame Surface -> RGB Array -> BGR OpenCV -> JPEG
        view = pygame.surfarray.array3d(self.surface)
        view = view.transpose([1, 0, 2])
        frame = cv2.cvtColor(view, cv2.COLOR_RGB2BGR)

        _, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        return jpeg.tobytes()

web_bridge = WebRLBridge()

def handle_web_action(action, value=None):
    if action == 'weather':
        web_bridge.sim.set_weather(value)
    elif action == 'speed':
        web_bridge.sim.set_simulation_speed(float(value))
    elif action == 'mode':
        web_bridge.sim.set_ai_mode(int(value))
    elif action == 'spawn_car':
        web_bridge.sim.spawn_vehicle()
    elif action == 'spawn_ambulance':
        web_bridge.sim.spawn_emergency()
    elif action == 'toggle_light':
        web_bridge.sim.toggle_phase()
