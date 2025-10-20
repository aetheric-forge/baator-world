# tests/test_rules_normalization.py
import sys, os, yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "apps" / "dm_tui"))

from dm_tui.app.baator_bridge import BaatorController  # controller does normalization

def test_steps_normalized_to_strings(tmp_path):
    # 1) create a pack on disk the way the repo expects
    pack_dir = Path(tmp_path) / "content" / "packs" / "mixed"
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "rules.yml").write_text(yaml.safe_dump([
        {"id": "x", "steps": ["a=1", {"py": "b=2"}, {"comment": "ignore-me"}, 3]}
    ], sort_keys=False))

    # 2) point controller at tmp repo root and load the pack (triggers normalization)
    ctrl = BaatorController(str(tmp_path), world_name="sim")
    report = ctrl.load_pack("mixed")
    assert report["rules"] == 1

    # 3) verify normalized steps are all strings and dict/comments were handled
    rules = ctrl.world.meta["rules"]
    steps = rules[0]["steps"]
    assert steps == ["a=1", "b=2", "3"]

