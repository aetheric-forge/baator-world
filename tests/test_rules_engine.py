from baator.kernel import CommandBus, EventBus
from baator.runtime import DiceService, RulesEngine, load_rule_pack, RulesRegistry
from baator.runtime.context_provider import ActorRepo, SimpleContextProvider

class FixedRNG:
    def roll(self, sides:int)->int: return 6
    def random_int(self,low:int,high:int)->int: return low
    def ping(self) -> bool: return True

def test_load_and_apply_attack_rule(tmp_path):
    yml = tmp_path/"physical.yaml"
    yml.write_text("""
pack_id: aether.physical_core
version: 1
engine_min: 0.4
namespace: physical
rules:
  - id: attack.basic
    layer: physical
    when: [ "target.hp > 0" ]
    roll: "1d20"
    dc: 5
    on_success:
      - type: command
        name: "physical.take_damage"
        payload: { layer: "physical", amount: "1d8" }
    on_failure:
      - type: event
        name: "physical.attack_missed"
        payload: {}
""")
    pack = load_rule_pack(yml)
    reg = RulesRegistry(); reg.register_pack(pack)
    bus = EventBus(sync=True)
    cmd = CommandBus()
    seen = {"cmds": [], "evts": []}

    svc = DiceService(FixedRNG(), bus, cmd, SimpleContextProvider(ActorRepo()))
    cmd.register("dice.resolve_number", svc.handle)
    cmd.register("physical.take_damage", lambda c: seen["cmds"].append(c.payload))
    bus.subscribe("physical.attack_missed", lambda e: seen["evts"].append(e.payload))

    eng = RulesEngine(cmd, bus)
    rule = reg.get("physical.attack.basic")
    ctx = {"target": {"hp": 10}}
    result = eng.apply(rule, ctx=ctx, provenance={"actor_id":"A1","layer":"physical","source":"test"})
    assert result["applied"] and result["success"]
    assert seen["cmds"][0]["layer"] == "physical"
    # with FixedRNG 1d20=6 >= dc 5 → success path taken
    assert seen["evts"] == []
