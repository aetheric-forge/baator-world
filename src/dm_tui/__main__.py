"""Minimal DM TUI entrypoint.

Run as:
python -m dm_tui
"""
import sys
import os
from baator.kernel.event_bus import EventBus
from baator.kernel.systems import CoreLoop
from baator.interface import RNG, SocketRNG, PythonRNG

def choose_rng():
    mode = os.getenv("BAATOR_RNG", "python").lower()
    if mode == "socket":
        host = os.getenv("BAATOR_RNG_HOST", "127.0.0.1")
        port = int(os.getenv("BAATOR_RNG_PORT", "4444"))
        return SocketRNG(host=host, port=port)
    return PythonRNG()

def main(rng: RNG, argv=None):
    argv = argv or sys.argv[1:]
    bus = EventBus()
    loop = CoreLoop(bus)
    # subscribe a simple printer for heartbeat events
    print("RNG PING:", rng.ping())
    print("d20:", rng.roll(20), " 3d6:", [rng.roll(6) for _ in range(3)])
    bus.subscribe("heartbeat", lambda e: print(f"heartbeat: {e.payload}"))
    loop.run_for(ticks=5, interval=0.05)
    print("dm_tui finished")

if __name__ == '__main__':
    rng = choose_rng()
    main(rng)
