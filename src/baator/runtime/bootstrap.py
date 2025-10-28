import os
from baator.interface import PythonRNG, SocketRNG

def choose_rng():
    mode = os.getenv("BAATOR_RNG", "python").lower()
    if mode == "socket":
        host = os.getenv("BAATOR_RNG_HOST", "127.0.0.1")
        port = int(os.getenv("BAATOR_RNG_PORT", "4444"))
        return SocketRNG(host=host, port=port)
    return PythonRNG()
