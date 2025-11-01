# dm_tui/commands/scene_command.py
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4
from baator.domain import Scene, Participant
from baator.kernel.events import Event
from ..command_api import CommandRegistry, CommandHandler, CommandContext

@dataclass
class SceneArgs:
    op: str
    name: Optional[str] = None
    mode: Optional[str] = None
    actor: Optional[str] = None
    target: Optional[str] = None

class SceneCommand:
    name = "scene"

    def help(self) -> str:
        return (
            "/scene [--id=<slot>] new <name>\n"
            "/scene [--id=<slot>] start <mode> <actor> <target>\n"
            "/scene [--id=<slot>] add <name>\n"
            "/scene [--id=<slot>] rm <name>\n"
            "/scene [--id=<slot>] next"
        )

    def parse(self, argv: list[str]) -> tuple[dict, str]:
        # global option: --id=slot
        state_id = "default"
        rest: list[str] = []
        for t in argv:
            if t.startswith("--id="):
                state_id = t.split("=", 1)[1] or "default"
            else:
                rest.append(t)
        if not rest:
            return ({"op": "help"}, state_id)
        op = rest[0]
        if op == "new" and len(rest) >= 2:
            return ({"op": "new", "name": " ".join(rest[1:])}, state_id)
        if op == "start" and len(rest) >= 4:
            return ({"op": "start", "mode": rest[1], "actor": rest[2], "target": rest[3]}, state_id)
        if op == "add" and len(rest) >= 2:
            return ({"op": "add", "name": rest[1]}, state_id)
        if op == "rm" and len(rest) >= 2:
            return ({"op": "rm", "name": rest[1]}, state_id)
        if op == "next":
            return ({"op": "next"}, state_id)
        return ({"op": "help"}, state_id)

    def run(self, ctx: CommandContext, args: dict, state: dict) -> str | None:
        # state is namespaced for this handler+state_id
        # shape: {"scene": Scene, "index": {name: Participant}}
        bus = ctx.bus
        op = args.get("op")

        if op == "help":
            return self.help()

        if op == "new":
            sc = Scene(args["name"])
            state["scene"] = sc
            state["index"] = {}
            bus.publish(Event("sim.trace.begin", {"scene_id": sc.scene_id, "rule": "scene.new"}))
            return f"Scene created: {sc.scene_id}"

        if op == "start":
            sc = state.get("scene") or Scene(args["mode"])
            state["scene"] = sc
            p1 = Participant(actor_id=uuid4(), name=args["actor"], initiative=0)
            p2 = Participant(actor_id=uuid4(), name=args["target"], initiative=0)
            sc.participants = [p1, p2]
            state["index"] = {p1.name: p1, p2.name: p2}
            bus.publish(Event("sim.trace.step", {"scene_id": sc.scene_id, "round": sc.round}))
            return f"Scene started ({args['mode']}): {p1.name} vs {p2.name}"

        if op == "add":
            sc = state.get("scene")
            if not sc: return "No active scene: use /scene new <name>"
            p = Participant(actor_id=uuid4(), name=args["name"], initiative=0)
            sc.participants.append(p)
            state.setdefault("index", {})[p.name] = p
            return f"Added {p.name}"

        if op == "rm":
            sc = state.get("scene")
            if not sc: return "No active scene"
            idx = state.get("index", {})
            p = idx.pop(args["name"], None)
            if not p: return f"Unknown participant: {args['name']}"
            sc.participants = [x for x in sc.participants if x.name != args["name"]]
            return f"Removed {args['name']}"

        if op == "next":
            sc = state.get("scene")
            if not sc: return "No active scene"
            sc.round += 1
            bus.publish(Event("sim.trace.step", {"scene_id": sc.scene_id, "round": sc.round}))
            return f"Round {sc.round}"

        return self.help()

def register(reg: CommandRegistry) -> None:
    reg.register(SceneCommand())
