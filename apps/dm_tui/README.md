# apps/dm_tui

Place your existing DM TUI here (or symlink). Update imports to use `baator_*` services instead of internal core code.

Recommended entry path in the TUI: obtain a `WorldService` and call into it for world operations.