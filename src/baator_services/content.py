from __future__ import annotations
from collections import OrderedDict
from curses import raw
from dataclasses import dataclass, field
from typing import Dict, Any, List, Literal
from typing_extensions import TypeGuard
from baator_services.world import Faction, WorldService
from baator_core.ids import Id

@dataclass
class LoadReport:
    factions: int = 0
    planes: int = 0
    relics: int = 0
    actors: int = 0
    scenes: int = 0
    rules: int = 0
    notes: List[str] = field(default_factory=list)

class ContentLoader:
    """
    Loads YAML content packs (factions.yml, planes.yml, rules.yml, etc.)
    and writes them into a WorldService state. Unknown files are ignored gracefully.
    Minimal schema checks are performed; invalid items are skipped with notes.
    """
    def __init__(self, world: WorldService):
        self.world = world

    @staticmethod
    def _coerce_id(value: Any) -> str:
        # "auto" -> new uuid
        if value in (None, "auto", "AUTO"):
            return Id.new().value
        if isinstance(value, dict) and "value" in value:
            return value["value"]
        return str(value)

    def _is_dict_meta(self, x: Any) -> TypeGuard[Dict[Any, Any]]:
        return isinstance(x, dict)

    def _merge_rules_unique(
        self,
        existing: List[Dict[str, Any]],
        added: List[Dict[str, Any]],
        *,
        policy: Literal["prefer_new", "prefer_old"] = "prefer_new",
    ) -> List[Dict[str, Any]]:
        """
        Merge two rule lists, de-duplicating by 'id'.
        - prefer_new: later (added) rules override earlier ones of the same id
        - prefer_old: earlier (existing) rules are kept, added dups are ignored
        """
        if policy == "prefer_new":
            # existing first, then added; added overwrites on same id
            seq = existing + added
        else:  # prefer_old
            # added first, then existing; existing overwrites on same id
            seq = added + existing

        by_id: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        for r in seq:
            rid = r.get("id")
            if not isinstance(rid, str):
                continue
            by_id[rid] = r  # later assignment wins
        return list(by_id.values())

    def _normalize_ruleset(self, ruleset: Any) -> List[Dict[str, Any]]:
        """
        Coerce ruleset into a canonical: list[dict{id:str, steps:list[str], ...}]
        - Accept dict-of-rules (values), list of rules, or a single rule dict
        - Coerce steps to list[str]
        - Support {"py": "..."} inside steps; ignore comment-only dicts
        - Coerce scalars (e.g., 3) to "3"
        """
        if ruleset is None:
            return []
        if isinstance(ruleset, dict):
            # treat as map of id->rule OR a single rule with keys (id, steps, ...)
            values = list(ruleset.values()) if any(isinstance(v, dict) for v in ruleset.values()) else [ruleset]
        elif isinstance(ruleset, list):
            values = ruleset
        else:
            values = [ruleset]

        out: List[Dict[str, Any]] = []
        for r in values:
            if not isinstance(r, dict):
                # wrap non-dict into a rule-like dict
                r = {"id": str(r), "steps": []}
            rid = r.get("id")
            # keep other fields (name, tags...) as-is
            steps = r.get("steps", [])
            if isinstance(steps, str):
                steps = [steps]

            fixed_steps: List[str] = []
            if isinstance(steps, list):
                for s in steps:
                    if isinstance(s, str):
                        fixed_steps.append(s)
                    elif isinstance(s, dict):
                        # allow {"py": "..."}; ignore pure comments/unknowns
                        py = s.get("py")
                        if isinstance(py, str):
                            fixed_steps.append(py)
                    elif isinstance(s, (int, float)):
                        fixed_steps.append(str(s))
                    # else: drop silently
            else:
                fixed_steps = [str(steps)]

            rule = dict(r)
            rule["id"] = str(rid) if rid is not None else "<no-id>"
            rule["steps"] = fixed_steps
            out.append(rule)
        return out

    def load_pack(self, pack_name: str) -> LoadReport:
        repo = self.world.repo
        bundle = repo.load_pack(pack_name)
        report = LoadReport()

        # Factions
        for rec in bundle.get("factions", []):
            name = rec.get("name")
            if not isinstance(name, str) or not name.strip():
                report.notes.append(f"skip faction with invalid name: {rec!r}")
                continue
            fid = self._coerce_id(rec.get("id", "auto"))
            sigil = rec.get("sigil")
            tags = rec.get("tags") or []
            self.world.state.factions[fid] = Faction(Id(fid), name=name, sigil=sigil, tags=list(tags))
            report.factions += 1

        # Planes
        for rec in bundle.get("planes", []):
            name = rec.get("name")
            if not isinstance(name, str) or not name.strip():
                report.notes.append(f"skip plane with invalid name: {rec!r}")
                continue
            pid = self._coerce_id(rec.get("id", "auto"))
            entropy = float(rec.get("entropy", 0.0) or 0.0)
            mana = float(rec.get("mana", 0.0) or 0.0)
            from baator_core.entities import Plane
            self.world.state.planes[pid] = Plane(Id(pid), name=name, entropy=entropy, mana=mana)
            report.planes += 1

        # Rules (optional, stored as opaque dicts attached to world metadata)
        ruleset = bundle.get("rules", [])
        norm_rules = self._normalize_ruleset(ruleset)
        if norm_rules:
            raw_meta = getattr(self.world, "meta", {})
            existing = raw_meta.get("rules", [])
            existing = self._normalize_ruleset(existing)
            merged = self._merge_rules_unique(
                existing,
                norm_rules,
                policy="prefer_new",
            )
            raw_meta["rules"] = merged
            if self._is_dict_meta(raw_meta):
                meta: Dict[Any, Any] = raw_meta
            else:
                meta = {}
            self.world.meta = meta
            report.rules = len(ruleset)

        return report
