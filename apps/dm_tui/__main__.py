# apps/dm_tui/__main__.py
import os, sys

# Make baator-world/src importable for baator_* packages
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# Import the app from the dm_tui package using a relative import
from .dm_tui.ui.dm_app import DMApp

if __name__ == "__main__":
    DMApp().run()
