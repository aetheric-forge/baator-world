from __future__ import annotations
import socket
from typing import Final, Protocol

_DEFAULT_TIMEOUT: Final[float] = 1.5

class SocketRNG:
    def __init__(self, host: str = "127.0.0.1", port: int = 4444, timeout: float = _DEFAULT_TIMEOUT):
        self.host, self.port, self.timeout = host, port, timeout

    def _req(self, line: str) -> str:
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as s:
            s.sendall((line + "\n").encode("ascii"))
            data = b""
            while not data.endswith(b"\n"):
                chunk = s.recv(64)
                if not chunk:
                    break
                data += chunk
        if not data:
            raise RuntimeError("RNG: empty response")
        resp = data.decode("ascii", errors="strict").strip()
        if not resp.startswith("OK "):
            raise RuntimeError(f"RNG error: {resp}")
        return resp[3:]

    def random_int(self, low: int, high: int) -> int:
        if low > high:
            low, high = high, low
        return int(self._req(f"RAND {low} {high}"))

    def roll(self, sides: int) -> int:
        if sides < 1:
            raise ValueError("sides must be >= 1")
        return int(self._req(f"DICE d{sides}"))

    def ping(self) -> bool:
        return self._req("PING") == "PONG"
