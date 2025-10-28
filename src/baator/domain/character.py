from dataclasses import dataclass, field
from uuid import UUID
from baator.kernel.base import AggregateRoot
from baator.kernel.id import Id
from baator.kernel.events import Event

@dataclass
class Character(AggregateRoot):
    hp: int = 10
    name: str = ""

    def take_damage(self, amount: int):
        self.hp -= amount
        self.record_event(Event(name="damage_taken", payload={"amount": amount, "hp": self.hp}))
