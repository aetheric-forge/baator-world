from dataclasses import dataclass
from uuid import uuid4, UUID

@dataclass(frozen=True)
class Id:
    value: UUID

    @staticmethod
    def new() -> "Id":
        return Id(uuid4())

    def __str__(self) -> str:
        return str(self.value)
