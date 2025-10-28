from dataclasses import dataclass, field
from typing import Any, Dict, List
from uuid import UUID

@dataclass
class Entity:
    id: UUID

@dataclass
class AggregateRoot(Entity):
    _events: List[Any] = field(default_factory=list)

    def record_event(self, event: Any) -> None:
        self._events.append(event)

    def pull_events(self) -> List[Any]:
        evts = list(self._events)
        self._events.clear()
        return evts
