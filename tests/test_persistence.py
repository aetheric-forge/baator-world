import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from baator_data.fs_repo import FileSystemRepository
from baator_services.world import WorldService

def test_world_save_and_reload(tmp_path):
    repo = FileSystemRepository(str(tmp_path))
    w = WorldService(repo, "sim")
    a = w.create_actor("A", hp=9)
    s = w.create_scene("S"); w.add_actor_to_scene(a, s); w.save()
    w2 = WorldService(repo, "sim")
    assert "A" in [x.name for x in w2.state.actors.values()]
    assert any(sc.name=="S" for sc in w2.state.scenes.values())
