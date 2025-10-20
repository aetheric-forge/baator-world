from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional

from baator_data.fs_repo import FileSystemRepository
from baator_services.world import WorldService
from baator_services.content import ContentLoader
from baator_rules.resolver import apply_yaml_rule
from baator_core.entities import Actor
from baator_core.ids import Id
from baator_sim.engine import run_scene

class BaatorController:
    def __init__(self, root: str, world_name: str = "dm_sandbox"):
        self.root = Path(root)
        self.repo = FileSystemRepository(str(self.root))
        self.world = WorldService(self.repo, world_name=world_name)
        self._last_scene_id: Optional[str] = None

    def _debug_rules_meta(self) -> str:
        meta = getattr(self.world, "meta", {})
        rules = meta.get("rules")
        if rules is None:
            return "meta has no 'rules' key"
        info = [f"rules type={type(rules).__name__}, len={getattr(rules,'__len__',lambda: '?')()}"]
        if isinstance(rules, list) and rules:
            r0 = rules[0]
            info.append(f"rule[0] keys={list(r0.keys())}")
            steps = r0.get("steps")
            info.append(f"steps type={type(steps).__name__}")
            if isinstance(steps, list):
                info.append("step element types: " + ", ".join(type(s).__name__ for s in steps[:5]))
        return " | ".join(info)

    # ---------- Content / Packs ----------
    def load_pack(self, pack_name: str) -> Dict[str, int]:
        loader = ContentLoader(self.world)           # takes WorldService
        report = loader.load_pack(pack_name)         # correct method
        return dict(factions=report.factions, planes=report.planes, rules=report.rules)

    # ---------- World building (return IDs) ----------
    def create_faction(self, name: str) -> str:
        fid = self.world.create_faction(name)        # returns id
        return fid

    def create_actor(self, name: str, hp: int = 10, faction_id: Optional[str] = None) -> str:
        aid = self.world.create_actor(name, hp=hp, faction_id=faction_id)  # returns id
        return aid

    def create_plane(self, name: str, entropy: float = 0.5, mana: float = 0.5) -> str:
        pid = self.world.create_plane(name, entropy=entropy, mana=mana)  # returns id
        return pid

    # ---------- Scene control ----------
    def start_scene(self, name: str, actors: List[str]) -> str:
        """
        Create a scene and attach the given actor *names*.
        If an actor name doesn't exist, create it; always wire by ID.
        """
        sid = self.world.create_scene(name)          # returns scene id
        for nm in actors:
            aid = self._ensure_actor_id_by_name(nm)
            self.world.add_actor_to_scene(aid, sid)
        self._last_scene_id = sid
        return sid

    def tick(self, ticks: int = 1) -> List[Dict[str, Any]]:
        sid = self._active_scene_id()
        out: List[Dict[str, Any]] = []
        for _ in range(max(1, ticks)):
            out.extend(run_scene(self.world, sid, max_ticks=1))
        return out

    def run_auto(self, max_ticks: int = 20) -> List[Dict[str, Any]]:
        sid = self._active_scene_id()
        return run_scene(self.world, sid, max_ticks=max_ticks)

    # ---------- Rules ----------
    def apply_rule(self, rule_id: str, **bindings) -> Dict[str, Any]:
        """
        Resolve common bindings (attacker/defender) by *name* into Actor objects,
        keep scalars as-is, and run the YAML rule.
        """
        rules = getattr(self.world, "meta", {}).get("rules", [])
        rule = next((r for r in rules if r.get("id") == rule_id), None)
        if not rule:
            raise KeyError(f"rule not found: {rule_id}")

        ctx: Dict[str, Any] = {}
        for k, v in bindings.items():
            if isinstance(v, str) and k in ("attacker", "defender"):
                ctx[k] = self._actor_by_name(v)      # -> Actor object
            else:
                ctx[k] = v
        ctx.setdefault("env", {"mana": 0.5})

        return apply_yaml_rule(rule, ctx)

    # ---------- Persistence ----------
    def save(self) -> None:
        self.world.save()

    def load_world(self) -> Dict[str, Any]:
        data = self.repo.load_world(self.world.world_name)
        return data or {}

    # ---------- Helpers: name/ID/object resolution ----------
    def _active_scene_id(self) -> str:
        sid = self._last_scene_id or getattr(self.world.state, "active_scene_id", None)
        if not sid:
            raise RuntimeError("No active scene. Use start_scene() first.")
        return sid

    def _ensure_actor_id_by_name(self, name: str) -> str:
        # look for existing
        for aid, a in self.world.state.actors.items():
            if a.name == name:
                return aid
        # create new if missing
        return self.world.create_actor(name, hp=10)

    def _actor_by_name(self, name: str) -> Actor:
        aid = self._ensure_actor_id_by_name(name)
        return self.world.state.actors[aid]

    # --- Diagnostics surfaced as a return value, not prints ---
    def rules_summary(self) -> str:
        """Human-friendly snapshot of rules currently attached to world meta."""
        meta = getattr(self.world, "meta", {})
        rules = meta.get("rules")
        if rules is None:
            return "rules: <none>"
        if not isinstance(rules, list):
            return f"rules: unexpected type {type(rules).__name__}"
        if not rules:
            return "rules: []"
        parts = [f"rules: {len(rules)}"]
        # show the first few
        for r in rules[:3]:
            rid = r.get("id", "<no-id>") if isinstance(r, dict) else str(r)
            steps = r.get("steps", []) if isinstance(r, dict) else []
            kind = type(steps).__name__
            head = []
            if isinstance(steps, list):
                for s in steps[:3]:
                    head.append(repr(s) if isinstance(s, str) else f"<{type(s).__name__}>")
            parts.append(f"  - {rid}  steps={kind} {head}")
        return "\n".join(parts)

    # --- Internal: coerce steps to strings so the resolver can compile() them ---
    def _normalize_rules(self) -> None:
        meta = getattr(self.world, "meta", {})
        rules = meta.get("rules")
        if not isinstance(rules, list):
            return
        for r in rules:
            if not isinstance(r, dict):
                continue
            steps = r.get("steps", [])
            # allow single string -> list[str]
            if isinstance(steps, str):
                steps = [steps]
            # force everything to strings
            if isinstance(steps, list):
                r["steps"] = [s if isinstance(s, str) else str(s) for s in steps]
            else:
                r["steps"] = [str(steps)]

