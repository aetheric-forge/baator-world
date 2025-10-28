# domain/facets/mythic.py
from dataclasses import dataclass
from baator.kernel import Event, Command, Layer
from baator.domain import Facet

@dataclass
class MythicFacet(Facet):
    layer: Layer = Layer.MYTHIC
    essence: int = 6
    wards: int = 2

    def apply_command(self, cmd: Command) -> list[Event]:
        if cmd.name == "mythic.invocation":
            cost = int(cmd.payload.get("cost", 1))
            if self.essence < cost:
                return [Event(name="mythic.invocation_failed", payload={"reason": "insufficient_essence"})]
            self.essence -= cost
            return [Event(name="mythic.invoked", payload={"cost": cost, "essence": self.essence})]
        return []
