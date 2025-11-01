# dm_tui/app.py
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Input, RichLog
from rich.pretty import pretty_repr
from baator.runtime.bootstrap import bootstrap, choose_rng
from baator.runtime import RulesEngine, RulesRegistry, Simulator, load_rule_pack
from .command_api import CommandRegistry, CommandContext
from .command_loader import load_commands

class DMApp(App):
    CSS_PATH = None
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("g", "scroll_home", "Top"),
        ("G", "scroll_end", "Bottom"),
        ("j", "scroll_up", "Up"),
        ("k", "scroll_down", "Down"),
    ]

    def action_scroll_home(self): self.event_log.scroll_home()
    def action_scroll_end(self): self.event_log.scroll_end()
    def action_scroll_up(self): self.event_log.scroll_up()
    def action_scroll_down(self): self.event_log.scroll_down()

    def compose(self) -> ComposeResult:
        yield Header()
        self.scene = DataTable(zebra_stripes=True)
        self.event_log = RichLog(id="event-log", highlight=True, wrap=True, auto_scroll=True, markup=True, max_lines=5000)
        self.input = Input(placeholder="/help for command help")
        yield self.scene
        yield self.event_log
        yield self.input
        yield Footer()

    def on_mount(self) -> None:
        def log_event(e):
            payload = pretty_repr(e.payload, max_string=120)
            self.event_log.write(f"[cyan]{e.name}[/]: {payload}\n")

        def on_damage(e):
            # expect payload like {'amount': X, 'target': 'Drone'}
            name = e.payload.get("target")
            amt  = e.payload.get("amount", 0)
            p = self.cmdreg.get_state("scene").get(name)
            if p:
                p.initiative = getattr(p, "initiative", 0)  # keep existing fields
                # if you’re storing hp in the scene participant, decrement here
                p.hp = max(0, getattr(p, "hp", 10) - amt)
                self.event_log.write(f"[red]-{amt}[/] to {name}  HP={p.hp}\n")        # Runtime

        self.bus, self.cbus = bootstrap(sync_bus=True)   # ensure sync EB for UI
        rng = choose_rng()
        self.engine = RulesEngine(self.cbus, self.bus, rng)
        self.registry = RulesRegistry()
        for pack in ["packs/physical_core.yaml", "packs/cyber_core.yaml", "packs/mythic_core.yaml"]:
            self.registry.register_pack(load_rule_pack(pack))
        self.sim = Simulator(self.registry, self.engine, self.cbus, self.bus)
        self.cmdreg = CommandRegistry()
        self.cbus.register("physical.take_damage", on_damage)
        self.cmdreg.set_base_context(app=self, bus=self.bus, cbus=self.cbus, engine=self.engine, sim=self.sim)
        load_commands(self.cmdreg)

        # Subscriptions
        for name in ("rules.trace","sim.trace.begin","sim.trace.end", "dice.resolved", "rng.fulfilled"):
            self.bus.subscribe(name, log_event)

    async def on_input_submitted(self, msg: Input.Submitted) -> None:
        text = msg.value.strip()
        self.input.value = ""
        if not text: return
        if text.startswith("/"):
            out = self.cmdreg.dispatch_line(text)
            if out: self.event_log.write(out + "\n")
            return
