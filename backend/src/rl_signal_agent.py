"""
Deep Q-Network (DQN) & Q-Learning Reinforcement Learning Traffic Signal Agent
SIH 2026 - Smart City Traffic Intelligence

Combines Tabular Q-Learning + PyTorch Deep Q-Network (DQN) for real-time
adaptive traffic signal control. Learns optimal phase duration policies to
maximize vehicle throughput and minimize delay/queue times.
"""

import numpy as np
import random
import time
from typing import Dict, List, Tuple
from pathlib import Path
import sys

_backend_dir = Path(__file__).parent.parent.resolve()
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

try:
    from src.logger import logger
except ImportError:
    try:
        from logger import logger
    except ImportError:
        import logging
        logger = logging.getLogger("traffic_ai")

# ─── PyTorch Import for Deep Q-Network (DQN) ──────────────────────────────────
HAS_TORCH = False
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    HAS_TORCH = True
    logger.info("PyTorch successfully loaded for Deep Q-Network (DQN) Reinforcement Learning!")
except ImportError:
    logger.warning("PyTorch not found. Falling back to Tabular Q-Learning RL agent.")


if HAS_TORCH:
    class QNetwork(nn.Module):
        """Deep Q-Network (DQN) Neural Architecture for Traffic State Evaluation"""
        def __init__(self, state_dim: int = 4, action_dim: int = 4):
            super(QNetwork, self).__init__()
            self.fc1 = nn.Linear(state_dim, 64)
            self.fc2 = nn.Linear(64, 64)
            self.fc3 = nn.Linear(64, action_dim)
            self.relu = nn.ReLU()

        def forward(self, state):
            x = self.relu(self.fc1(state))
            x = self.relu(self.fc2(x))
            return self.fc3(x)


class ReinforcementLearningSignalAgent:
    """
    Reinforcement Learning Signal Controller (DQN + Tabular Q-Learning).

    State Vector: (Lane 0 Density, Lane 1 Density, Avg Speed, Queued Vehicles)
    Actions:
      0: Lane 0 Green (Short - 15s)
      1: Lane 0 Green (Long - 35s)
      2: Lane 1 Green (Short - 15s)
      3: Lane 1 Green (Long - 35s)
    """

    def __init__(
        self,
        num_lanes: int = 2,
        alpha: float = 0.1,      # Learning rate
        gamma: float = 0.95,     # Discount factor
        epsilon: float = 0.20,   # Exploration rate
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01
    ):
        self.num_lanes = num_lanes
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min

        self.actions = [0, 1, 2, 3]
        self.q_table: Dict[Tuple, List[float]] = {}
        self.cumulative_reward: float = 0.0
        self.step_count: int = 0
        self.last_action: int = 0
        self.last_state = (0, 0, 0, 0)
        self.last_wait_time: float = 0.0

        # PyTorch DQN initialization
        self.use_dqn = HAS_TORCH
        if self.use_dqn:
            self.q_net = QNetwork(state_dim=4, action_dim=4)
            self.target_net = QNetwork(state_dim=4, action_dim=4)
            self.target_net.load_state_dict(self.q_net.state_dict())
            self.optimizer = optim.Adam(self.q_net.parameters(), lr=0.001)
            self.loss_fn = nn.MSELoss()
            self.replay_buffer = []

        logger.info(f"Reinforcement Learning Agent initialized (DQN Active: {self.use_dqn})!")

    def discretize_state(self, lane_data: Dict, avg_speed: float = 30.0) -> Tuple:
        """Convert continuous sensor inputs into discrete state tuple."""
        l0_count = lane_data.get("lane_0", {}).get("count", 0) if lane_data else 0
        l1_count = lane_data.get("lane_1", {}).get("count", 0) if lane_data else 0

        # Discretize density: 0=Low (<3), 1=Mod (3-6), 2=High (7-10), 3=Critical (>10)
        l0_s = min(3, l0_count // 3)
        l1_s = min(3, l1_count // 3)
        spd_s = 0 if avg_speed < 20 else (1 if avg_speed < 50 else 2)
        total_q = min(3, (l0_count + l1_count) // 4)

        return (l0_s, l1_s, spd_s, total_q)

    def choose_action(self, state: Tuple) -> int:
        """Epsilon-greedy policy for action selection."""
        # Exploration
        if random.random() < self.epsilon:
            action = random.choice(self.actions)
        else:
            # Exploitation
            if self.use_dqn:
                with torch.no_grad():
                    state_t = torch.FloatTensor(state).unsqueeze(0)
                    q_vals = self.q_net(state_t)
                    action = int(torch.argmax(q_vals).item())
            else:
                if state not in self.q_table:
                    self.q_table[state] = [0.0] * len(self.actions)
                action = int(np.argmax(self.q_table[state]))

        # Decay exploration
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        self.last_action = action
        self.last_state = state
        return action

    def compute_reward(self, current_wait_time: float, throughput_count: int, congestion_level: str) -> float:
        """
        Bellman Reward Function:
          Reward = +5.0 * Throughput - 1.5 * ΔWaitTime - 10.0 * CongestionPenalty
        """
        wait_delta = current_wait_time - self.last_wait_time
        self.last_wait_time = current_wait_time

        c_penalty = 15.0 if congestion_level == "CRITICAL" else (8.0 if congestion_level == "HIGH" else 0.0)
        reward = (throughput_count * 6.0) - (wait_delta * 1.5) - c_penalty
        self.cumulative_reward += reward
        self.step_count += 1

        return reward

    def update_agent(self, next_state: Tuple, reward: float):
        """Update Q-values using Q-Learning Bellman equation or DQN gradient step."""
        if self.use_dqn:
            # Experience replay training step
            self.replay_buffer.append((self.last_state, self.last_action, reward, next_state))
            if len(self.replay_buffer) > 200:
                self.replay_buffer.pop(0)

            if len(self.replay_buffer) >= 16:
                batch = random.sample(self.replay_buffer, 16)
                s_b = torch.FloatTensor([b[0] for b in batch])
                a_b = torch.LongTensor([b[1] for b in batch]).unsqueeze(1)
                r_b = torch.FloatTensor([b[2] for b in batch]).unsqueeze(1)
                ns_b = torch.FloatTensor([b[3] for b in batch])

                q_eval = self.q_net(s_b).gather(1, a_b)
                q_next = self.target_net(ns_b).detach().max(1)[0].unsqueeze(1)
                q_target = r_b + self.gamma * q_next

                loss = self.loss_fn(q_eval, q_target)
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

                if self.step_count % 20 == 0:
                    self.target_net.load_state_dict(self.q_net.state_dict())
        else:
            # Tabular Q-Learning Bellman Equation: Q(s,a) <- Q(s,a) + alpha * [r + gamma*max Q(s',a') - Q(s,a)]
            s = self.last_state
            ns = next_state
            a = self.last_action

            if s not in self.q_table:
                self.q_table[s] = [0.0] * len(self.actions)
            if ns not in self.q_table:
                self.q_table[ns] = [0.0] * len(self.actions)

            predict = self.q_table[s][a]
            target = reward + self.gamma * max(self.q_table[ns])
            self.q_table[s][a] += self.alpha * (target - predict)

    def get_telemetry(self) -> Dict:
        """Return rich Reinforcement Learning telemetry metrics for Digital Twin XAI & API."""
        max_q = 0.0
        if self.use_dqn:
            with torch.no_grad():
                st = torch.FloatTensor(self.last_state).unsqueeze(0)
                max_q = float(torch.max(self.q_net(st)).item())
        else:
            max_q = max(self.q_table.get(self.last_state, [0.0]))

        action_names = {
            0: "Lane 1 Green (Short 15s)",
            1: "Lane 1 Green (Long 35s)",
            2: "Lane 2 Green (Short 15s)",
            3: "Lane 2 Green (Long 35s)"
        }

        return {
            "algorithm": "Deep Q-Network (DQN) RL" if self.use_dqn else "Tabular Q-Learning RL",
            "cumulative_reward": round(self.cumulative_reward, 1),
            "epsilon_exploration": round(self.epsilon, 3),
            "current_state": self.last_state,
            "last_action_name": action_names.get(self.last_action, "Lane 1 Green"),
            "max_q_value": round(max_q, 3),
            "total_episodes_steps": self.step_count,
            "learning_rate_alpha": self.alpha,
            "discount_gamma": self.gamma
        }


# Alias for backward compatibility
QLearningSignalAgent = ReinforcementLearningSignalAgent


if __name__ == "__main__":
    agent = ReinforcementLearningSignalAgent()
    lanes = {"lane_0": {"count": 6}, "lane_1": {"count": 2}}
    s = agent.discretize_state(lanes, avg_speed=25.0)
    act = agent.choose_action(s)
    rew = agent.compute_reward(current_wait_time=12.0, throughput_count=4, congestion_level="MODERATE")
    agent.update_agent(s, rew)
    telem = agent.get_telemetry()

    print("[OK] Reinforcement Learning Agent tested successfully!")
    print(f"  Algorithm: {telem['algorithm']}")
    print(f"  Action Chosen: {telem['last_action_name']}")
    print(f"  Cumulative Reward: {telem['cumulative_reward']} | Max Q-value: {telem['max_q_value']}")
