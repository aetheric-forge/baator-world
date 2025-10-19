from __future__ import annotations
import json, os, yaml
from typing import Dict, Any
from pathlib import Path

class FileSystemRepository:
    def __init__(self, root: str):
        self.root = Path(root)
        self.worlds = self.root / "worlds"
        self.packs = self.root / "content" / "packs"
        self.worlds.mkdir(parents=True, exist_ok=True)

    def _world_path(self, name: str) -> Path:
        return self.worlds / f"{name}.json"

    # Repository interface
    def list_worlds(self):
        for p in self.worlds.glob("*.json"):
            yield p.stem

    def load_world(self, name: str):
        p = self._world_path(name)
        if not p.exists():
            return None
        return json.loads(p.read_text())

    def save_world(self, name: str, data: Dict[str, Any]) -> None:
        p = self._world_path(name)
        p.write_text(json.dumps(data, indent=2))

    def load_pack(self, pack_name: str):
        # expects directory under packs
        base = self.packs / pack_name
        result = {}
        if not base.exists(): 
            return result
        for y in base.glob("*.yml"):
            with open(y, "r") as f:
                result[y.stem] = yaml.safe_load(f) or {}
        return result