# domain/facets/physical.py
from dataclasses import dataclass
from baator.kernel import Event, Command, Layer
from baator.domain import Facet
from baator.util import clamp

@dataclass
class PhysicalFacet(Facet):
    layer: Layer = Layer.PHYSICAL
    hp: int = 10
    stamina: int = 5

    def apply_command(self, cmd: Command) -> list[Event]:
        verb = cmd.name
        if verb == "physical.take_damage":
            amt = int(cmd.payload["amount"])
            self.hp = clamp(self.hp - amt, 0, 999)
            return [Event(name="physical.damage_taken", payload={"amount": amt, "hp": self.hp})]
        if verb == "physical.heal":
            amt = int(cmd.payload["amount"])
            self.hp = clamp(self.hp + amt, 0, 999)
            return [Event(name="physical.healed", payload={"amount": amt, "hp": self.hp})]
        return []
