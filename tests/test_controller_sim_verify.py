# tests/test_controller_sim_verify.py
import sys, os
from pathlib import Path
from shutil import copytree

# make src importable for tests
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "dm_tui"))

from dm_tui.app.baator_bridge import BaatorController

def test_simulate_matches_engine(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    # mirror the real repo layout under tmp_path
    copytree(project_root / "content", tmp_path / "content", dirs_exist_ok=True)

    ctrl = BaatorController(str(tmp_path), world_name="sim")
    ctrl.load_pack("baator_base")  # use controller to get normalization + env plumbing
    ctrl.set_env_mana(0.8)
    ctrl._actor_by_name("Valkyr").power = 3
    ctrl.start_scene("duel", ["Valkyr", "Drone"])

    pred = ctrl.simulate_rule("attack_basic", "Valkyr", "Drone")
    assert pred["predicted_damage"] == 4

    rows = ctrl.verify_ticks("attack_basic", 2)
    assert rows[0]["ok"] and rows[1]["ok"]

