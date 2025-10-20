from .base_command import BaseCommand

class SceneStartCommand(BaseCommand):
    key = "scene"
    help = "/scene start <name> <actor1> <actor2> ... – start a scene with actors"

    def execute(self) -> None:
        if not self.args or self.args[0] != "start" or len(self.args) < 3:
            self.app.ui_log("Usage: /scene start <name> <actor1> <actor2> ...")
            return
        name = self.args[1]
        actors = self.args[2:]
        try:
            sid = self.app.controller.start_scene(name, actors)
            self.app.ui_log(f"Scene '{name}' started (id={sid}) with actors: {', '.join(actors)}")
        except Exception as e:
            self.app.ui_log(f"scene error: {e}")
