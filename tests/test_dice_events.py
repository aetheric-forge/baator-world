from baator.kernel import expr_adv
from baator.kernel.event_bus import EventBus
from baator.kernel.command_bus import CommandBus
from baator.kernel.commands import Command
from baator.runtime.context_provider import ActorRepo, SimpleContextProvider
from baator.runtime.dice_service import DiceService

class FakeRNG:
    def __init__(self, seq): self.seq=list(seq)
    def random_int(self, low, high): return self.roll(high-low+1) + (low-1)
    def roll(self, sides): return self.seq.pop(0) if self.seq else 1
    def ping(self): return True

class FixedRNG:
    def roll(self, sides: int): return 4  # d20 → 4
    def random_int(self, low, high): return low
    def ping(self) -> bool: return True

ctx_provider = SimpleContextProvider(ActorRepo())

def test_dice_service_emits_requested_and_fulfilled_for_expr():
    bus = EventBus(sync=True); bus.start()
    events = []
    bus.subscribe("rng.requested",  lambda e: events.append(("req", e.payload)))
    bus.subscribe("rng.fulfilled",  lambda e: events.append(("ok", e.payload)))

    svc = DiceService(FakeRNG([3,3,4]), bus, ctx_provider)  # 3d6+2 => 12
    res = svc.roll_expression("3d6+2", meta={"test": True})

    bus.stop()
    assert res == 12
    kinds = [k for k,_ in events]
    assert kinds == ["req", "ok"]
    assert events[0][1]["expr"] == "3d6+2"
    assert events[1][1]["result"] == 12

def test_command_bus_routes_dice_commands():
    bus = EventBus(sync=True); bus.start()
    seen = {"ok":0}
    bus.subscribe("rng.fulfilled", lambda e: seen.__setitem__("ok", seen["ok"]+1))

    cbus = CommandBus()
    svc = DiceService(FakeRNG([6]), bus, ctx_provider)  # d20 adv/dis will use provided seq minimally
    cbus.register("dice.roll_expr", svc.handle)

    cbus.dispatch(Command(name="dice.roll_expr", payload={"expr":"1d6"}))
    bus.stop()
    assert seen["ok"] == 1

def test_meta_is_flattened():
    bus = EventBus(sync=True)
    seen = {}
    bus.subscribe("rng.fulfilled", lambda e: seen.update(e.payload))

    svc = DiceService(FixedRNG(), bus, ctx_provider)
    svc.roll_expression(expr_adv(20), meta={"actor_id": "A1", "layer": "physical", "source": "tui", "debug": True})

    # Flattened provenance
    assert seen["actor_id"] == "A1"
    assert seen["layer"] == "physical"
    assert seen["source"] == "tui"

    # No 'meta' blob
    assert "meta" not in seen
