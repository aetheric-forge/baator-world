from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import pathlib
import yaml  # add PyYAML to requirements.txt
from baator.kernel.layers import Layer

@dataclass
class Effect:
    type: str            # "command" | "event"
    name: str
    payload: Dict[str, Any]

@dataclass
class Rule:
    id: str
    layer: Layer
    when: List[str] = field(default_factory=list)   # simple boolean conditions
    cost: Optional[str] = None                      # arithmetic expr (no names)
    roll: Optional[str] = None                      # dice expr
    dc: Optional[int] = None
    on_success: List[Effect] = field(default_factory=list)
    on_failure: List[Effect] = field(default_factory=list)

@dataclass
class RulePack:
    pack_id: str
    version: int
    engine_min: str
    namespace: str
    description: str = ""
    rules: List[Rule] = field(default_factory=list)

class RulesRegistry:
    def __init__(self):
        self._rules: Dict[str, Rule] = {}   # key: f"{namespace}.{id}"

    def register_pack(self, pack: RulePack) -> None:
        for r in pack.rules:
            key = f"{pack.namespace}.{r.id}"
            if key in self._rules:
                raise ValueError(f"Duplicate rule id: {key}")
            self._rules[key] = r

    def get(self, key: str) -> Rule:
        return self._rules[key]

    def all(self) -> Dict[str, Rule]:
        return dict(self._rules)

def _ensure(cond: bool, msg: str):
    if not cond: raise ValueError(msg)

def load_rule_pack(path: str | pathlib.Path) -> RulePack:
    data = yaml.safe_load(pathlib.Path(path).read_text())
    for k in ("pack_id","version","engine_min","namespace","rules"):
        _ensure(k in data, f"Missing pack field: {k}")

    rules = []
    for raw in data["rules"]:
        for k in ("id","layer"):
            _ensure(k in raw, f"Missing rule field: {k}")
        layer = Layer(raw["layer"])
        when = list(raw.get("when", []))
        cost = raw.get("cost")
        roll = raw.get("roll")
        dc = raw.get("dc")
        def parse_effect(x: Dict[str, Any]) -> Effect:
            for k in ("type","name","payload"):
                _ensure(k in x, f"Missing effect field: {k}")
            _ensure(x["type"] in ("command","event"), "effect.type must be command|event")
            return Effect(type=x["type"], name=x["name"], payload=dict(x["payload"] or {}))
        on_success = [parse_effect(e) for e in raw.get("on_success", [])]
        on_failure = [parse_effect(e) for e in raw.get("on_failure", [])]
        rules.append(Rule(
            id=raw["id"], layer=layer, when=when, cost=cost, roll=roll, dc=dc,
            on_success=on_success, on_failure=on_failure
        ))

    return RulePack(
        pack_id=data["pack_id"], version=int(data["version"]),
        engine_min=str(data["engine_min"]), namespace=data["namespace"],
        description=data.get("description",""), rules=rules
    )
