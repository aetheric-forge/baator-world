"""
Lightweight event bus with adapter/plugin points.

Design notes:
- `EventBus` exposes `publish` and `subscribe`.
- Adapters implement a simple interface (example RabbitMQ adapter).
- Also includes a RNG adapter interface (for a socket-based C++ RNG).
This is intentionally small: the real project should swap adapters via DI/composition.
"""

from typing import Callable, Dict, List, Any, Protocol
import threading
import queue
import time
from .events import Event

class Subscriber(Protocol):
    def __call__(self, event: Event) -> None:
        ...

class TransportAdapter(Protocol):
    def publish(self, event: Event) -> None:
        ...
    def close(self) -> None:
        ...

class EventBus:
    def __init__(self, transport: TransportAdapter = None):
        # in-process fallback queue
        self._subs: Dict[str, List[Subscriber]] = {}
        self._queue: "queue.Queue[Event]" = queue.Queue()
        self._running = False
        self._transport = transport

    def subscribe(self, event_name: str, fn: Subscriber) -> None:
        self._subs.setdefault(event_name, []).append(fn)

    def _dispatch(self, event: Event) -> None:
        for fn in self._subs.get(event.name, []):
            try:
                fn(event)
            except Exception as e:
                # swallow for now, but real impl would log
                print(f"[EventBus] subscriber error: {e}")

    def publish(self, event: Event) -> None:
        # transport-level publish (e.g. RabbitMQ) if provided:
        if self._transport is not None:
            try:
                self._transport.publish(event)
                return
            except Exception as e:
                print(f"[EventBus] transport publish failed, falling back: {e}")
        # otherwise push to local queue for dispatch loop
        self._queue.put(event)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        def loop():
            while self._running:
                try:
                    ev = self._queue.get(timeout=0.5)
                except Exception:
                    continue
                self._dispatch(ev)
        t = threading.Thread(target=loop, daemon=True)
        t.start()

    def stop(self) -> None:
        self._running = False
        if self._transport:
            try:
                self._transport.close()
            except Exception:
                pass

# Example adapter stubs

class RabbitMQAdapter:
    def __init__(self, url: str):
        self.url = url
        # placeholder - real impl would create connection/channel
        self._connected = False

    def connect(self):
        # connect logic (pika or aio-pika)
        self._connected = True

    def publish(self, event: Event) -> None:
        if not self._connected:
            self.connect()
        # serialise and push to RabbitMQ -- placeholder
        print(f"[RabbitMQAdapter] would publish: {event}")

    def close(self) -> None:
        self._connected = False

class SocketRNGAdapter:
    """
    Adapter that queries an external RNG via a socket (e.g., C++ daemon).
    Protocol: send 'RAND
' -> receive ascii integer + '\n'
    """
    def __init__(self, host: str = "localhost", port: int = 4444, timeout: float = 1.0):
        self.host = host
        self.port = port
        self.timeout = timeout

    def random_int(self, low: int = 0, high: int = 2**31 - 1) -> int:
        import socket
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as s:
            s.sendall(b"RAND\n")
            data = s.recv(64)
        try:
            return int(data.strip())
        except Exception:
            raise RuntimeError("Invalid RNG response")

    def close(self) -> None:
        pass
