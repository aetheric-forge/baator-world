from __future__ import annotations
from typing import List, Dict, Any

def rule_to_markdown(rule: Dict[str, Any]) -> str:
    """
    Accepts a dict like:
    {
      id: "attack_basic",
      name: "Basic Attack Resolution",
      description: "How attacks resolve in low-aether conditions",
      inputs: ["attacker.power", "defender.armor", "env.mana"],
      steps: [
        "base = attacker.power",
        "if env.mana > 0.7: base += 1",
        "damage = max(0, base - defender.armor)",
      ],
      examples: [
        {"attacker.power": 3, "defender.armor": 1, "env.mana": 0.6, "out.damage": 2}
      ]
    }
    """
    name = rule.get("name", rule.get("id", "Unnamed Rule"))
    out = [f"# {name}"]
    if "id" in rule:
        out.append(f"_Rule ID_: `{rule['id']}`")
    if "description" in rule:
        out.append("**Description**")
        out.append(rule['description'])
    if rule.get("inputs"):
        out.append("**Inputs**")
        for i in rule["inputs"]:
            out.append(f"- `{i}`")
    if rule.get("steps"):
        out.append("**Resolution Steps**")
        for s in rule["steps"]:
            out.append(f"1. {s}")
    if rule.get("examples"):
        out.append("**Examples**")
        for ex in rule["examples"]:
            kv = ", ".join(f"`{k}` = `{v}`" for k, v in ex.items())
            out.append(f"- {kv}")
    return "\n".join(out)

def ruleset_to_markdown(rules: List[Dict[str, Any]], title: str = "Baator Ruleset") -> str:
    sections = [f"# {title}", ""]
    for r in rules:
        sections.append(rule_to_markdown(r))
        sections.append("")
    return "\n".join(sections)
