from typing import Any, Mapping
from uuid import UUID

from baator.domain.actor import Actor
from baator.kernel import Layer
from baator.kernel.context import ContextProvider

class ActorRepo:
    def get(self, actor_id: UUID) -> Actor | None: ...

def _as_uuid(v):
    try:
        return UUID(str(v))
    except (ValueError, TypeError):
        return None
class SimpleContextProvider(ContextProvider):
    def __init__(self, repo: ActorRepo):
        self.repo = repo

    def resolve(self, meta: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
        ctx: dict[str, Any] = {}
        aid: UUID | None = None
        tid: UUID | None = None
        if meta is not None:
            aid = _as_uuid(meta.get("actor_id"))
            tid = _as_uuid(meta.get("target_id"))

        if aid:
            ctx["actor"] = self._project(self.repo.get(UUID(str(aid))))
        if tid:
            ctx["target"] = self._project(self.repo.get(UUID(str(tid))))

        return ctx or None

    def _project(self, actor: Actor | None) -> Mapping[str, Any]:
        # Map facets to the fields your rules reference
        # Adjust to your actual facet structure
        if actor is None:
            raise ValueError("Cannot _project null Actor")
        proj: dict[str, Any] = {"name": actor.name}
        phys = actor.facets.get(Layer.PHYSICAL)  # e.g., Layer.PHYSICAL
        cyber = actor.facets.get(Layer.CYBER) # Layer.CYBER
        myth  = actor.facets.get(Layer.MYTHIC) # Layer.MYTHIC

        if phys:
            proj.update({
                "hp": getattr(phys, "hp", 0),
                "AC": getattr(phys, "ac", 10),
                "stats": getattr(phys, "stats", {}),  # e.g., {"STR":2,"DEX":1,...}
            })
        if cyber:
            proj.update({
                "firewall": getattr(cyber, "firewall", 0),
                "integrity": getattr(cyber, "integrity", 0),
            })
        if myth:
            proj.update({
                "wards": getattr(myth, "wards", 0),
                "essence": getattr(myth, "essence", 0),
            })
        return proj
