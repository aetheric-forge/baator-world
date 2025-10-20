import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
# tests/test_rules_exec.py
from baator_rules.resolver import apply_yaml_rule
from baator_core.entities import Actor
from baator_core.ids import Id

def test_rule_with_env_dict_access():
    rule = {"id":"attack_basic","steps":[
        "base = attacker.power",
        "if env['mana'] > 0.7: base += 1",
        "defender.hp = max(0, defender.hp - base)",
    ]}
    atk = Actor(Id.new(), "Valkyr", hp=10, power=3)
    dfd = Actor(Id.new(), "Drone", hp=10, power=1)
    res = apply_yaml_rule(rule, {"attacker": atk, "defender": dfd, "env": {"mana":0.8}})
    assert dfd.hp == 6
    assert res["rule_id"] == "attack_basic"
