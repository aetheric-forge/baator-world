from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional
from baator_core.entities import Faction, Plane, Relic, Actor, Scene
from baator_core.ids import Id
from .repository import Repository

@dataclass
class WorldState:
    factions: Dict[str, Faction] = field(default_factory=dict)
    planes: Dict[str, Plane] = field(default_factory=dict)
    relics: Dict[str, Relic] = field(default_factory=dict)
    actors: Dict[str, Actor] = field(default_factory=dict)
    scenes: Dict[str, Scene] = field(default_factory=dict)

    def to_dict(self) -> dict:
        def m(obj): 
            return asdict(obj)
        return {
            "factions": {k: m(v) for k, v in self.factions.items()},
            "planes": {k: m(v) for k, v in self.planes.items()},
            "relics": {k: m(v) for k, v in self.relics.items()},
            "actors": {k: m(v) for k, v in self.actors.items()},
            "scenes": {k: m(v) for k, v in self.scenes.items()},
        }

    @staticmethod
    def from_dict(data: dict) -> "WorldState":
        def mk(cls, d): return cls(**d)
        ws = WorldState()
        ws.factions = {k: mk(Faction, v) for k, v in data.get("factions", {}).items()}
        ws.planes   = {k: mk(Plane,   v) for k, v in data.get("planes", {}).items()}
        ws.relics   = {k: mk(Relic,   v) for k, v in data.get("relics", {}).items()}
        ws.actors   = {k: mk(Actor,   v) for k, v in data.get("actors", {}).items()}
        ws.scenes   = {k: mk(Scene,   v) for k, v in data.get("scenes", {}).items()}
        return ws

class WorldService:
    def __init__(self, repo: Repository, world_name: str = "sandbox"):
        self.repo = repo
        self.world_name = world_name
        data = repo.load_world(world_name) or {}
        self.state = WorldState.from_dict(data) if data else WorldState()

    # CRUD-ish helpers
    def create_faction(self, name: str, *, sigil: str | None = None, tags: list[str] | None = None) -> str:
        fid = Id.new().value
        self.state.factions[fid] = Faction(Id(fid), name=name, sigil=sigil, tags=tags or [])
        return fid

    def create_plane(self, name: str, entropy: float = 0.2, mana: float = 0.5) -> str:
        pid = Id.new().value
        self.state.planes[pid] = Plane(Id(pid), name=name, entropy=entropy, mana=mana)
        return pid

    def create_actor(self, name: str, *, faction_id: str | None = None, hp: int = 10, power: int = 1, agility: int = 1) -> str:
        aid = Id.new().value
        self.state.actors[aid] = Actor(Id(aid), name=name, faction_id=Id(faction_id) if faction_id else None, hp=hp, power=power, agility=agility)
        return aid

    def create_scene(self, name: str, plane_id: str | None = None) -> str:
        sid = Id.new().value
        self.state.scenes[sid] = Scene(Id(sid), name=name, plane_id=Id(plane_id) if plane_id else None, turn=0, actors=[])
        return sid

    def add_actor_to_scene(self, actor_id: str, scene_id: str) -> None:
        self.state.scenes[scene_id].actors.append(Id(actor_id))

    def advance_time(self, scene_id: str, ticks: int = 1) -> int:
        self.state.scenes[scene_id].turn += ticks
        return self.state.scenes[scene_id].turn

    def save(self) -> None:
        self.repo.save_world(self.world_name, self.state.to_dict())