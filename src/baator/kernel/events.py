from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

@dataclass
class Event:
    name: str
    payload: Dict[str, Any]
    occurred_at: datetime = datetime.now()

    def __repr__(self):
        return f"<Event {self.name} at {self.occurred_at.isoformat()}>"
