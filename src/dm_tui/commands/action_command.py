# dm_tui/commands/action_command.py
class ActionCommand:
    name = "action"
    def help(self) -> str: return "/action [--id=<slot>] <rule_id> <actor> -> <target>"

    def parse(self, argv):
        slot = "default"
        rest = []
        for t in argv:
            if t.startswith("--id="):
                slot = t.split("=",1)[1] or "default"
            else:
                rest.append(t)
        if not rest: return ({"help": True}, slot)

        rule_id = rest[0]
        if "->" in rest:
            i = rest.index("->")
            actor  = " ".join(rest[1:i])
            target = " ".join(rest[i+1:])
        else:
            actor, target = rest[1], rest[2]
        return ({"rule": rule_id, "actor": actor, "target": target, "slot": slot}, slot)

    def run(self, ctx, a, _local_state):
        if a.get("help"): return self.help()

        # 🔎 read the *scene* plugin's state
        scene_state = ctx.get_state("scene", a["slot"])
        sc   = scene_state.get("scene")
        idx  = scene_state.get("index", {})
        A, B = idx.get(a["actor"]), idx.get(a["target"])
        if not (sc and A and B):
            return "Need a scene and known actor/target (/scene help)"

        ctx_extra = {
            "actor":  {"stats": {"STR": 2}, "essence": 3},
            "target": {"hp": 10, "AC": 12, "firewall": 2, "integrity": 8, "wards": 1},
        }
        ctx.sim.apply_rule(sc, a["rule"], actor=A, target=B, ctx_extra=ctx_extra)
        return f"Applied {a['rule']} ({A.name} -> {B.name})"

def register(reg): reg.register(ActionCommand())

