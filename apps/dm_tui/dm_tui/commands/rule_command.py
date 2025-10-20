from .base_command import BaseCommand

class RuleCommand(BaseCommand):
    key = "rule"
    help = "/rule <rule_id> key=value ... – apply rule by id with simple bindings"

    def execute(self) -> None:
        if not self.args:
            self.app.ui_log("Usage: /rule <rule_id> key=value ...")
            return
        rid, *kv = self.args
        bindings = {}
        for pair in kv:
            if "=" in pair:
                k, v = pair.split("=", 1)
                # crude int casting
                try:
                    v = int(v)
                except ValueError:
                    pass
                bindings[k] = v
        try:
            res = self.app.controller.apply_rule(rid, **bindings)
            self.app.ui_log(str(res))
        except Exception as e:
            self.app.ui_log(f"rule error: {e}")
