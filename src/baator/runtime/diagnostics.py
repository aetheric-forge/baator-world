from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
from baator.kernel import EventBus, Event

@dataclass
class TraceRecorder:
    events: List[Event] = field(default_factory=list)

    def attach(self, bus: EventBus) -> None:
        for name in ("rules.trace","sim.trace.begin","sim.trace.end",
                     "rng.requested","rng.fulfilled","rng.failed"):
            bus.subscribe(name, self.events.append)  # keep raw events

    def as_log(self) -> List[Dict[str, Any]]:
        return [ {"name": e.name, **e.payload} for e in self.events ]
