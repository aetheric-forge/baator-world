# domain/actor.py
from dataclasses import dataclass, field
from typing import Dict, Optional
from uuid import UUID
from baator.kernel.base import AggregateRoot
from baator.kernel.events import Event
from baator.kernel.commands import Command
from baator.kernel.layers import Layer

class Facet:
    layer: Layer
    def apply_command(self, cmd: Command) -> list[Event]:  # returns domain events
        raise NotImplementedError

@dataclass
class Actor(AggregateRoot):
    name: str = ""
    facets: Dict[Layer, Facet] = field(default_factory=dict)

    def attach_facet(self, facet: Facet) -> None:
        self.facets[facet.layer] = facet

    def act(self, cmd: Command) -> None:
        # cmd.payload should include layer, verb, etc.
        layer = Layer(cmd.payload.get("layer"))
        facet = self.facets.get(layer)
        if not facet:
            raise ValueError(f"No facet for layer {layer} on actor {self.id}")
        events = facet.apply_command(cmd)
        for ev in events:
            # enrich with actor metadata + layer for routing/observability
            ev.payload.setdefault("actor_id", self.id)
            ev.payload.setdefault("layer", layer.value)
            self.record_event(ev)

