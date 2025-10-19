from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from .ids import Id

@dataclass(frozen=True)
class Faction:
    id: Id
    name: str
    sigil: Optional[str] = None
    tags: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class Plane:
    id: Id
    name: str
    entropy: float = 0.0  # 0..1
    mana: float = 0.0     # 0..1

@dataclass(frozen=True)
class Relic:
    id: Id
    name: str
    quality: int = 0
    tags: List[str] = field(default_factory=list)

@dataclass
class Actor:
    id: Id
    name: str
    faction_id: Optional[Id] = None
    hp: int = 10
    power: int = 1
    agility: int = 1
    tags: List[str] = field(default_factory=list)

@dataclass
class Scene:
    id: Id
    name: str
    plane_id: Optional[Id] = None
    turn: int = 0
    actors: List[Id] = field(default_factory=list)