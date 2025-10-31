"""Minimal DM TUI entrypoint.

Run as:
python -m dm_tui
"""
import sys
from typing import Optional, List
from uuid import uuid4
from baator.kernel import RNG, CoreLoop, Command
from baator.runtime.bootstrap import choose_rng, bootstrap
from baator.runtime.diagnostics import TraceRecorder
from baator.domain import Scene, Participant
from baator.runtime import RulesEngine, RulesRegistry, Simulator, load_rule_pack

def main(rng: RNG, argv: Optional[List[str]] = None):
    argv = argv or sys.argv[1:]
    bus, cbus, _ = bootstrap()
    engine = RulesEngine(cbus, bus, rng)
    registry = RulesRegistry()
    for pack in ["packs/physical_core.yaml", "packs/cyber_core.yaml", "packs/mythic_core.yaml"]:
        registry.register_pack(load_rule_pack(pack))

    rec = TraceRecorder(); rec.attach(bus)

    # log RNG events
    bus.subscribe("rng.requested",  lambda e: print(f"RNG REQUEST: {e.payload}"))
    bus.subscribe("rng.fulfilled",  lambda e: print(f"RNG RESULT : {e.payload}"))
    bus.subscribe("rng.failed",     lambda e: print(f"RNG FAILED : {e.payload}"))
    bus.subscribe("rules.trace", lambda e: print("RULE:", e.payload))
    bus.subscribe("sim.trace.end", lambda e: print("END :", e.payload))

    # subscribe for visibility
    sim = Simulator(registry, engine, cbus, bus)

    # still show heartbeats
    bus.subscribe("heartbeat", lambda e: print(f"heartbeat: {e.payload}"))

    # prove command flow
    cbus.dispatch(Command(name="dice.roll_expr", payload={"expr": "3d6+2", "meta": {"source": "tui"}}))
    cbus.dispatch(Command(name="dice.roll_adv",  payload={"sides": 20, "meta": {"source": "tui"}}))
    cbus.dispatch(Command(name="dice.roll_dis",  payload={"sides": 20, "meta": {"source": "tui"}}))

    loop = CoreLoop(bus)
    loop.run_for(ticks=3, interval=0.05)

    # fake participants (extend with real stats via ctx_extra later)
    scene = Scene("demo")
    p1 = Participant(actor_id=uuid4(), name="Valkyr", initiative=15)
    p2 = Participant(actor_id=uuid4(), name="Goblin", initiative=10)
    scene.participants = [p1, p2]

    # example context providing the stats referenced by rules
    ctx_extra = {
    "actor": {"stats": {"STR": 2, "HACK": 0, "WILL": 1}, "essence": 3},
    "target": {"AC": 12, "hp": 10, "firewall": 2, "integrity": 8, "wards": 1},
    }

    # apply one physical attack
    sim.apply_rule(scene, "physical.attack.basic", actor=p1, target=p2, ctx_extra=ctx_extra)
    # ... set up scene, ctx_extra ...
    loop.run_for(ticks=3, interval=0.05)

    print("dm_tui finished")

if __name__ == '__main__':
    rng = choose_rng()
    main(rng)
