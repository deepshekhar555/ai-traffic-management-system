"""
Reinforcement Learning (Q-Learning) Traffic Signal Controller
Dynamically learns optimal green light timings to minimize wait times and maximize throughput.
"""

import numpy as np
import random
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

class QLearningSignalAgent:
    """
    Q-Learning Reinforcement Learning Agent for Adaptive Traffic Light Timing
    State: (Lane 1 Density Level, Lane 2 Density Level)
    Action: Choose active green lane & duration [0: Lane 1 (20s), 1: Lane 1 (40s), 2: Lane 2 (20s), 3: Lane 2 (40s)]
    """
    
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.alpha = alpha  # Learning rate
        self.gamma = gamma  # Discount factor
        self.epsilon = epsilon  # Exploration rate
        self.q_table = {}
        self.actions = [0, 1, 2, 3]
        logger.info("Q-Learning AI Reinforcement Learning Signal Controller initialized!")

    def get_state_key(self, lane_densities):
        """Discretize lane density ratios into discrete state levels (0: Low, 1: Mod, 2: High, 3: Critical)"""
        states = []
        for d in lane_densities:
            if d > 0.75:
                states.append(3)
            elif d > 0.50:
                states.append(2)
            elif d > 0.25:
                states.append(1)
            else:
                states.append(0)
        return tuple(states)

    def choose_action(self, state_key):
        """Choose action using epsilon-greedy policy"""
        if state_key not in self.q_table:
            self.q_table[state_key] = [0.0] * len(self.actions)
            
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        return int(np.argmax(self.q_table[state_key]))

    def update_q_value(self, state_key, action, reward, next_state_key):
        """Update Q-value using Q-learning Bellman equation"""
        if next_state_key not in self.q_table:
            self.q_table[next_state_key] = [0.0] * len(self.actions)
            
        predict = self.q_table[state_key][action]
        target = reward + self.gamma * np.max(self.q_table[next_state_key])
        self.q_table[state_key][action] += self.alpha * (target - predict)

    def compute_reward(self, prev_wait_time, current_wait_time, throughput_count):
        """
        Reward Function: Positive reward for increased throughput, 
        Negative penalty for increased vehicle queue wait time
        """
        reward = (throughput_count * 5.0) - (current_wait_time - prev_wait_time)
        return reward


if __name__ == "__main__":
    agent = QLearningSignalAgent(alpha=0.1, gamma=0.9, epsilon=0.1)
    # Simulate: Lane 0 is HIGH density (0.8), Lane 1 is LOW density (0.2)
    lane_densities = [0.8, 0.2]
    state = agent.get_state_key(lane_densities)
    action = agent.choose_action(state)
    # Simulate reward: 3 vehicles passed, wait time reduced by 5s
    reward = agent.compute_reward(prev_wait_time=30, current_wait_time=25, throughput_count=3)
    next_state = agent.get_state_key([0.5, 0.3])
    agent.update_q_value(state, action, reward, next_state)
    action_map = {0: "Lane1 GREEN 20s", 1: "Lane1 GREEN 40s", 2: "Lane2 GREEN 20s", 3: "Lane2 GREEN 40s"}
    print(f"[OK] QLearningSignalAgent tested! State: {state} | Action: {action_map[action]} | Reward: {reward:.1f} | Q-Table entries: {len(agent.q_table)}")
