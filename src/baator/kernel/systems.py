from typing import Any
from .event_bus import EventBus
from .events import Event
import time

class CoreLoop:
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.ticks = 0
        self.running = False

    def tick(self):
        # example: emit a heartbeat event
        e = Event(name="heartbeat", payload={"tick": self.ticks})
        self.bus.publish(e)
        self.ticks += 1

    def run_for(self, ticks: int = 10, interval: float = 0.1):
        self.running = True
        self.bus.start()
        for _ in range(ticks):
            self.tick()
            time.sleep(interval)
        self.bus.stop()
