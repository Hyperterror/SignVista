"""
Simple in-process sliding-window rate limiter.

Good enough for a single-process deployment. For multiple workers/instances,
swap the storage for Redis.
"""

import ipaddress
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import HTTPException, Request

from app.config import settings


class RateLimiter:
    def __init__(self):
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, q: Deque[float], window: float, now: float) -> None:
        while q and q[0] <= now - window:
            q.popleft()

    def hit(self, key: str, limit: int, window_seconds: float) -> bool:
        """Record a hit. Returns False if the limit is exceeded."""
        if not settings.RATE_LIMIT_ENABLED:
            return True
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            self._prune(q, window_seconds, now)
            if len(q) >= limit:
                return False
            q.append(now)
            # Opportunistic cleanup so idle keys don't accumulate forever
            if len(self._hits) > 10_000:
                for k in [k for k, v in self._hits.items() if not v]:
                    del self._hits[k]
            return True

    def count(self, key: str, window_seconds: float) -> int:
        now = time.monotonic()
        with self._lock:
            q = self._hits.get(key)
            if not q:
                return 0
            self._prune(q, window_seconds, now)
            return len(q)

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def _parse_networks(entries):
    nets = []
    for entry in entries:
        try:
            nets.append(ipaddress.ip_network(entry, strict=False))
        except ValueError:
            pass
    return nets


_TRUSTED_NETWORKS = _parse_networks(settings.TRUSTED_PROXIES)


def _is_trusted(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr in net for net in _TRUSTED_NETWORKS)


def client_ip(request: Request) -> str:
    """
    Client IP for rate limiting. X-Forwarded-For is honoured only when the
    direct peer is a trusted proxy (IPs or CIDR ranges in TRUSTED_PROXIES);
    the right-most untrusted hop is used so a client can't spoof its address.
    """
    peer = request.client.host if request.client else "unknown"
    if not _is_trusted(peer):
        return peer
    forwarded = request.headers.get("x-forwarded-for", "")
    hops = [h.strip() for h in forwarded.split(",") if h.strip()]
    for hop in reversed(hops):
        if not _is_trusted(hop):
            return hop
    return peer


def enforce(key: str, limit: int, window_seconds: float, detail: str = "Too many requests. Please try again later.") -> None:
    if not limiter.hit(key, limit, window_seconds):
        raise HTTPException(status_code=429, detail=detail, headers={"Retry-After": str(int(window_seconds))})
