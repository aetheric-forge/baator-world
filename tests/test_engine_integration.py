import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from baator_data.fs_repo import FileSystemRepository
from baator_services.world import WorldService
from baator_services.content import ContentLoader
from baator_sim.engine import run_scene

def test_engine_prefers_yaml_rule(tmp_path):
    repo = FileSystemRepository(str(tmp_path))
    world = WorldService(repo, world_name="sim")
    # Create minimal actors & scene
    f = world.create_faction("X")
    a1 = world.create_actor("A", hp=10, power=4)
    a2 = world.create_actor("B", hp=10, power=1)
    s = world.create_scene("Arena")
    world.add_actor_to_scene(a1, s)
    world.add_actor_to_scene(a2, s)
    world.save()

    # Load a pack with custom attack rule (damage equals attacker.power)
    base = Path(tmp_path) / "content" / "packs" / "sim_pack"
    base.mkdir(parents=True, exist_ok=True)
    (base / "rules.yml").write_text("""
- id: attack_basic
  name: Custom Attack
  steps:
    - base = attacker.power
    - defender.hp = defender.hp - base
""".strip())

    loader = ContentLoader(world)
    report = loader.load_pack("sim_pack")
    assert report.rules == 1

    log = run_scene(world, s, seed=123, max_ticks=1)
    # Expect B to take 4 damage (power 4 rule), proving YAML rule applied
    assert any(e.get("event") == "attack" and e.get("damage") == 4 for e in log)
