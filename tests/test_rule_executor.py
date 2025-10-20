import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from baator_rules.resolver import apply_yaml_rule
from baator_core.entities import Actor
from baator_core.ids import Id

def test_apply_yaml_rule_basic_damage():
    rule = {
        "id": "attack_basic",
        "steps": [
            "base = attacker.power",
            "defender.hp = max(0, defender.hp - base)",
        ]
    }
    atk = Actor(Id.new(), "Attacker", hp=10, power=3, agility=1)
    dfd = Actor(Id.new(), "Defender", hp=10, power=1, agility=1)
    ctx = {"attacker": atk, "defender": dfd, "env": {"mana": 0.5}}
    res = apply_yaml_rule(rule, ctx)
    assert dfd.hp == 7
    assert res["rule_id"] == "attack_basic"