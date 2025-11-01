"""Minimal DM TUI entrypoint.

Run as:
python -m dm_tui
"""
from .app import DMApp

if __name__ == '__main__':
    DMApp().run()
