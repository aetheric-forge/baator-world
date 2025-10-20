# tests/test_env_and_turns.py
from pathlib import Path
import sys, os

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, ROOT / "src")

from shutil import copytree
from baator_data.fs_repo import FileSystemRepository
from baator_services.world import WorldService
from baator_services.content import ContentLoader
from baator_sim.engine import run_scene

def make_world(tmp_path):
    copytree(ROOT / "content", tmp_path / "content", dirs_exist_ok=True)
    repo = FileSystemRepository(str(tmp_path))
    w = WorldService(repo, world_name="sim")
    ContentLoader(w).load_pack("baator_base")
    # env used by engine
    meta = w.meta; meta["env"] = {"mana": 0.8}; w.meta = meta
    a = w.create_actor("Valkyr", hp=10); w.state.actors[a].power = 3
    b = w.create_actor("Drone", hp=10)
    s = w.create_scene("duel"); w.add_actor_to_scene(a, s); w.add_actor_to_scene(b, s)
    return w, s

def test_alternation_and_env(tmp_path):
    w, s = make_world(tmp_path)
    # tick 1 (Valkyr -> Drone) should include mana bonus
    log = run_scene(w, s, max_ticks=1)
    assert any(e.get("event")=="attack" and e["attacker"]=="Valkyr" and e["damage"]==4 for e in log)
    # tick 2 (Drone -> Valkyr) no bonus
    log = run_scene(w, s, max_ticks=1)
    assert any(e.get("event")=="attack" and e["attacker"]=="Drone" and e["damage"]==2 for e in log)
