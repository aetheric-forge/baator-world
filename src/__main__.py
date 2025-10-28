"""Minimal DM TUI entrypoint.

Run as:
python -m dm_tui
"""
import sys
from baator.kernel.event_bus import EventBus
from baator.kernel.systems import CoreLoop

def main(argv=None):
    argv = argv or sys.argv[1:]
    bus = EventBus()
    loop = CoreLoop(bus)
    # subscribe a simple printer for heartbeat events
    bus.subscribe("heartbeat", lambda e: print(f"heartbeat: {e.payload}"))
    loop.run_for(ticks=5, interval=0.05)
    print("dm_tui finished")

if __name__ == '__main__':
    main()
