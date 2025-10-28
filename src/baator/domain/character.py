from dataclasses import dataclass, field
from uuid import UUID
from .actor import Actor
from baator.kernel.events import Event

@dataclass
class Character(Actor):
    hp: int = 10
    name: str = ""

    def take_damage(self, amount: int):
        self.hp -= amount
        self.record_event(Event(name="damage_taken", payload={"amount": amount, "hp": self.hp}))
