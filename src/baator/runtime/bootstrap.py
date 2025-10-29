import os
from baator.kernel import EventBus, CommandBus
from baator.runtime import DiceService
from baator.interface import PythonRNG
from baator.interface import SocketRNG

def choose_rng():
    mode = os.getenv("BAATOR_RNG", "python").lower()
    if mode == "socket":
        host = os.getenv("BAATOR_RNG_HOST", "127.0.0.1")
        port = int(os.getenv("BAATOR_RNG_PORT", "4444"))
        return SocketRNG(host=host, port=port)
    return PythonRNG()

def bootstrap():
    event_bus = EventBus()
    cmd_bus = CommandBus()

    rng = choose_rng()
    dice = DiceService(rng, event_bus)

    # register commands
    cmd_bus.register("dice.roll_expr", dice.handle)
    cmd_bus.register("dice.roll_adv", dice.handle)
    cmd_bus.register("dice.roll_dis", dice.handle)

    return event_bus, cmd_bus, dice

