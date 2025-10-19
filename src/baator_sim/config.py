from __future__ import annotations
from dataclasses import dataclass

@dataclass
class SimulationConfig:
    seed: int = 1337
    max_ticks: int = 6
    log_events: bool = True