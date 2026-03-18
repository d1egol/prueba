"""
Rate limiting por sesión — ventana deslizante en memoria.

Fix #4: Evita que un solo usuario sature el agente con requests paralelos.
"""

import time
from collections import deque


class RateLimiter:
    def __init__(self, max_messages: int = 10, window_seconds: int = 60):
        self.max_messages = max_messages
        self.window = window_seconds
        self._timestamps: dict[str, deque] = {}

    def is_allowed(self, session_id: str) -> bool:
        """True si el session puede enviar un mensaje ahora."""
        now = time.monotonic()
        if session_id not in self._timestamps:
            self._timestamps[session_id] = deque()

        dq = self._timestamps[session_id]

        # Purgar timestamps fuera de la ventana
        while dq and dq[0] < now - self.window:
            dq.popleft()

        if len(dq) >= self.max_messages:
            return False

        dq.append(now)
        return True

    def seconds_until_reset(self, session_id: str) -> int:
        """Segundos hasta que el más antiguo mensaje salga de la ventana."""
        dq = self._timestamps.get(session_id)
        if not dq:
            return 0
        now = time.monotonic()
        return max(0, int(self.window - (now - dq[0])) + 1)
