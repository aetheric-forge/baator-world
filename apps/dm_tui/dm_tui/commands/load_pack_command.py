from .base_command import BaseCommand

class LoadPackCommand(BaseCommand):
    key = "loadpack"
    help = "/loadpack <pack_name> - Load a content pack into the world"

    def execute(self) -> None:
        if not self.args:
            self.app.ui_log("Usage: /loadpack <pack_name>")
            return
        pack = self.args[0]
        try:
            summary = self.app.controller.load_pack(pack)
            self.app.ui_log(f"Loaded pack '{pack}': "
                            f"{summary['factions']} factions, "
                            f"{summary['planes']} planes, "
                            f"{summary['rules']} rules.")
        except Exception as e:
            self.app.ui_log(f"Error loading pack '{pack}': {e}")
