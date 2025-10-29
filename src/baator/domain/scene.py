from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import UUID

@dataclass
class Participant:
    actor_id: UUID
    name: str
    initiative: int
    # optional: layer routing preferences, team tags, etc.

@dataclass
class Scene:
    scene_id: str
    participants: List[Participant] = field(default_factory=list)
    round: int = 1
    turn_index: int = 0

    def order(self) -> List[Participant]:
        return sorted(self.participants, key=lambda p: p.initiative, reverse=True)

    def current(self) -> Optional[Participant]:
        o = self.order()
        return o[self.turn_index] if o else None

    def next_turn(self) -> Participant | None:
        if not self.participants: return None
        self.turn_index += 1
        if self.turn_index >= len(self.participants):
            self.turn_index = 0
            self.round += 1
        return self.current()
