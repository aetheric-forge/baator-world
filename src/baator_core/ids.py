from __future__ import annotations
from dataclasses import dataclass
import uuid

@dataclass(frozen=True)
class Id:
    value: str

    @staticmethod
    def new() -> "Id":
        return Id(str(uuid.uuid4()))