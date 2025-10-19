from time import sleep
from .base_command import BaseCommand

class QuitCommand(BaseCommand):
    def execute(self) -> None:
        self.app.exit("Goodbye!")
