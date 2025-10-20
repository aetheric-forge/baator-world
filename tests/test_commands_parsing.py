# tests/test_commands_parsing.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "dm_tui"))
sys.path.insert(0, str(ROOT / "src"))
from dm_tui.commands.base import REGISTRY, CommandContext
from dm_tui.commands import plugins  # side-effect register
class FakeApp:
    def __init__(self, controller):
        self.controller = controller
        self.logs=[]
    def ui_log(self, msg): self.logs.append(msg)

def test_rules_listing(tmp_path):
    # minimal controller
    from dm_tui.app.baator_bridge import BaatorController
    ctrl = BaatorController(str(tmp_path), world_name="sim")
    ctrl.world.meta = {"rules":[{"id":"r1","name":"Rule One","steps":["pass"]}]}
    app = FakeApp(ctrl)
    ctx = CommandContext(app=app, ui_log=app.ui_log, controller=ctrl)
    REGISTRY.resolve("rules").fn(ctx, [])
    assert "Loaded 1 rule" in "\n".join(app.logs)
