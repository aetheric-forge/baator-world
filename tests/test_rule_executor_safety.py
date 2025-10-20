
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pytest

from baator_rules.resolver import apply_yaml_rule, UnsafeExpression
from baator_core.entities import Actor
from baator_core.ids import Id

def test_private_attribute_access_forbidden():
    atk = Actor(Id.new(), "A", hp=10, power=2, agility=1)
    dfd = Actor(Id.new(), "B", hp=10, power=1, agility=1)
    rule = {"id": "poke_dunder", "steps": ["x = attacker.__class__"]}
    with pytest.raises(UnsafeExpression):
        apply_yaml_rule(rule, {"attacker": atk, "defender": dfd, "env": {}})

def test_private_attribute_assignment_forbidden():
    atk = Actor(Id.new(), "A", hp=10, power=2, agility=1)
    dfd = Actor(Id.new(), "B", hp=10, power=1, agility=1)
    rule = {"id": "assign_dunder", "steps": ["attacker.__class__ = 1"]}
    with pytest.raises(UnsafeExpression):
        apply_yaml_rule(rule, {"attacker": atk, "defender": dfd, "env": {}})

def test_boolops_and_or_supported():
    atk = Actor(Id.new(), "A", hp=10, power=2, agility=1)
    dfd = Actor(Id.new(), "B", hp=10, power=1, agility=1)
    rule = {"id": "boolops", "steps": ["cond = (attacker.power >= 2) and (defender.hp == 10)", "if cond: defender.hp = defender.hp - 1"]}
    ctx = {"attacker": atk, "defender": dfd, "env": {}}
    apply_yaml_rule(rule, ctx)
    assert dfd.hp == 9
