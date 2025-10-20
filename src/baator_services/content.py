from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Iterable, List, Optional
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
        if ruleset:
            raw_meta = getattr(self.world, "meta", {})
            raw_meta.setdefault("rules", []).extend(ruleset)
            if self._is_dict_meta(raw_meta):
                meta: Dict[Any, Any] = raw_meta
            else:
                meta = {}
            self.world.meta = meta
            report.rules = len(ruleset)

        return report
