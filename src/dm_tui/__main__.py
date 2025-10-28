"""Minimal DM TUI entrypoint.

Run as:
python -m dm_tui
"""
import sys
from baator.kernel import CoreLoop, Command
from baator.runtime.bootstrap import choose_rng, bootstrap

def main(argv=None):
    argv = argv or sys.argv[1:]
    bus, cbus, dice = bootstrap()

    # log RNG events
    bus.subscribe("rng.requested",  lambda e: print(f"RNG REQUEST: {e.payload}"))
    bus.subscribe("rng.fulfilled",  lambda e: print(f"RNG RESULT : {e.payload}"))
    bus.subscribe("rng.failed",     lambda e: print(f"RNG FAILED : {e.payload}"))

    # still show heartbeats
    bus.subscribe("heartbeat", lambda e: print(f"heartbeat: {e.payload}"))

    # prove command flow
    cbus.dispatch(Command(name="dice.roll_expr", payload={"expr": "3d6+2", "meta": {"source": "tui"}}))
    cbus.dispatch(Command(name="dice.roll_adv",  payload={"sides": 20, "meta": {"source": "tui"}}))
    cbus.dispatch(Command(name="dice.roll_dis",  payload={"sides": 20, "meta": {"source": "tui"}}))

    loop = CoreLoop(bus)
    loop.run_for(ticks=3, interval=0.05)
    print("dm_tui finished")

if __name__ == '__main__':
    rng = choose_rng()
    main(rng)
