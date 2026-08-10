"""
Rate limiter em memória, por processo -- suficiente pro MVP rodando numa
instância só (mesma filosofia do worker de jobs: sem infra nova antes de
precisar de verdade, ver app/core/jobs/worker.py).

LIMITAÇÃO IMPORTANTE: se escalar horizontalmente (mais de um processo ou
container atrás de um load balancer), isso PRECISA virar Redis (INCR +
EXPIRE) -- memória de processo não é compartilhada entre réplicas, então
cada uma teria seu próprio contador e o limite real vira (limite x número
de réplicas) sem ninguém perceber. Ver ADR correspondente.
"""
import asyncio
import time
from typing import Dict, Tuple


class InMemoryRateLimiter:
    def __init__(self):
        self._buckets: Dict[str, Tuple[int, float]] = {}
        self._lock = asyncio.Lock()

    async def check(self, key: str, max_attempts: int, window_seconds: int) -> Tuple[bool, int]:
        """Cada chamada conta como uma tentativa. Devolve (permitido,
        segundos_até_resetar) -- quem chama decide se reseta em caso de
        sucesso (ver reset())."""
        async with self._lock:
            now = time.monotonic()
            count, window_start = self._buckets.get(key, (0, now))

            if now - window_start >= window_seconds:
                count, window_start = 0, now

            if count >= max_attempts:
                retry_after = max(int(window_seconds - (now - window_start)), 1)
                return False, retry_after

            self._buckets[key] = (count + 1, window_start)
            return True, 0

    async def reset(self, key: str) -> None:
        async with self._lock:
            self._buckets.pop(key, None)


login_rate_limiter = InMemoryRateLimiter()
