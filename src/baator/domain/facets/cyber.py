# domain/facets/cyber.py
from dataclasses import dataclass
from baator.kernel import Event, Command, Layer
from baator.domain import Facet

@dataclass
class CyberFacet(Facet):
    layer: Layer = Layer.CYBER
    firewall: int = 3
    integrity: int = 8

    def apply_command(self, cmd: Command) -> list[Event]:
        if cmd.name == "cyber.ice_attack":
            dmg = int(cmd.payload["damage"])
            self.integrity = max(0, self.integrity - dmg)
            return [Event(name="cyber.integrity_damaged", payload={"damage": dmg, "integrity": self.integrity})]
        return []
