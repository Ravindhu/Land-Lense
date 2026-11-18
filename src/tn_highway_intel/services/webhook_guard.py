"""Webhook guards: constant-time secret check and a token-bucket rate limiter (docs/API.md 1.2, 1.6)."""

from __future__ import annotations

import hmac
import math
import time
from typing import Callable, Optional


def secret_matches(presented: Optional[str], expected: str) -> bool:
    if presented is None or not expected:
        return False
    return hmac.compare_digest(presented.encode("utf-8"), expected.encode("utf-8"))


class RateLimiter:
    """Allow `per_minute` requests per minute in total. Returns (allowed, retry_after_seconds)."""

    def __init__(self, per_minute: int, clock: Callable[[], float] = time.monotonic) -> None:
        self.capacity = float(per_minute)
        self.rate_per_s = per_minute / 60.0
        self._clock = clock
        self._tokens = float(per_minute)
        self._last = clock()

    def allow(self) -> tuple[bool, int]:
        now = self._clock()
        self._tokens = min(self.capacity, self._tokens + (now - self._last) * self.rate_per_s)
        self._last = now
        if self._tokens >= 1:
            self._tokens -= 1
            return True, 0
        wait = (1 - self._tokens) / self.rate_per_s
        return False, max(1, math.ceil(wait))
