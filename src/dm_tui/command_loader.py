import importlib, pkgutil
from .command_api import CommandRegistry

def load_commands(reg: CommandRegistry) -> None:
    # import all modules under dm_tui.commands.* that expose register(reg)
    from . import commands as pkg
    for m in pkgutil.iter_modules(pkg.__path__):
        mod = importlib.import_module(f"{pkg.__name__}.{m.name}")
        if hasattr(mod, "register"):
            mod.register(reg)
