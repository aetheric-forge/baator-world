import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from baator_data.fs_repo import FileSystemRepository
from baator_services.world import WorldService
from baator_sim.engine import run_scene

def test_fallback_damage_without_rules(tmp_path):
    repo = FileSystemRepository(str(tmp_path))
    w = WorldService(repo, world_name="sim")
    a = w.create_actor("A", hp=10); w.state.actors[a].power = 5
    b = w.create_actor("B", hp=10)
    s = w.create_scene("duel"); w.add_actor_to_scene(a, s); w.add_actor_to_scene(b, s)
    log = run_scene(w, s, max_ticks=1)
    assert any(e.get("event")=="attack" and e["damage"]==5 for e in log)
