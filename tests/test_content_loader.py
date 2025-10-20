import sys, os, json
from pathlib import Path

# Ensure src is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from baator_data.fs_repo import FileSystemRepository
from baator_services.world import WorldService
from baator_services.content import ContentLoader

def write_pack(tmpdir: Path):
    base = tmpdir / "content" / "packs" / "spec_pack"
    base.mkdir(parents=True, exist_ok=True)
    (base / "factions.yml").write_text("""
- id: auto
  name: Test Faction
  sigil: tf
  tags: [order]
""".strip())
    (base / "planes.yml").write_text("""
- id: auto
  name: Spec Plane
  entropy: 0.25
  mana: 0.75
""".strip())
    (base / "rules.yml").write_text("""
- id: attack_basic
  name: Attack
  steps:
    - base = attacker.power
    - defender.hp = max(0, defender.hp - base)
""".strip())
    return base

def test_content_loader_loads_pack(tmp_path):
    repo = FileSystemRepository(str(tmp_path))
    world = WorldService(repo, world_name="t")
    loader = ContentLoader(world)
    write_pack(tmp_path)
    report = loader.load_pack("spec_pack")
    world.save()

    # Assert counts
    assert report.factions == 1
    assert report.planes == 1
    assert report.rules == 1

    # Assert world persisted
    data = repo.load_world("t")
    assert data is not None
    assert "factions" in data and len(data["factions"]) == 1
    assert "planes" in data and len(data["planes"]) == 1

    # Rules attached to meta
    rules = getattr(world, "_meta", {}).get("rules", [])
    assert len(rules) == 1
    assert rules[0]["id"] == "attack_basic"
