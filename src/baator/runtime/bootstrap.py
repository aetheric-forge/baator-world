import os
from baator.kernel.context import ContextProvider
from baator.kernel import EventBus, CommandBus
from baator.runtime import DiceService
from baator.interface import PythonRNG
from baator.interface import SocketRNG
from baator.runtime.context_provider import ActorRepo, SimpleContextProvider

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
    ctx_provider = SimpleContextProvider(ActorRepo())

    dice = DiceService(rng, event_bus, ctx_provider)

    # register commands
    cmd_bus.register("dice.roll_expr", dice.handle)
    cmd_bus.register("dice.roll_adv", dice.handle)
    cmd_bus.register("dice.roll_dis", dice.handle)

    return event_bus, cmd_bus, dice

