# Baator World (Scaffold)

Port-and-adapters scaffold for expanding the DM TUI into a full Baator Engine.

## Packages

- **baator_core** — canonical domain entities and value objects. Pure Python.
- **baator_rules** — rules/resolvers that operate on domain objects.
- **baator_services** — orchestration layer (WorldService) + ports (Repository).
- **baator_data** — adapters (FileSystemRepository) to persist worlds and load packs.
- **baator_sim** — simulation config + engine for action scenes.

Apps live under `apps/` and consume `baator_*` packages (e.g., the existing DM TUI).

## Quickstart

```bash
pip install -e .
python -m baator_sim.demo
```

This runs a tiny seeded simulation and prints an event log.