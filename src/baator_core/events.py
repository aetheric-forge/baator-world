from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
from .ids import Id

@dataclass(frozen=True)
class Event:
    tick: int
    kind: str
    data: Dict[str, Any]

# Example events: ActorJoined, AttackResolved, SceneAdvanced