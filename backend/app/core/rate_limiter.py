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

from fastapi import Request

from app.core.config import settings


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

register_rate_limiter = InMemoryRateLimiter()


def get_client_ip(request: Request) -> str:
    """IP do cliente pra chave de rate limit (por enquanto só usado em
    /register e /login).

    Por padrão usa request.client.host (o socket que abriu a conexão TCP
    com o processo Python) -- correto se a API recebe requisição direto da
    internet, mas ERRADO se houver um proxy reverso/load balancer na
    frente (Nginx, Railway, Render, Cloudflare, ALB etc.): nesse caso,
    TODO mundo apareceria com o IP do proxy, e o rate limit efetivamente
    viraria "todo mundo compartilha o mesmo balde".

    Se a API estiver atrás de um proxy confiável que você SABE que
    sobrescreve (não só repassa) o header X-Forwarded-For a cada
    requisição, ligue settings.TRUST_PROXY_HEADERS=true no ambiente de
    produção -- só então usamos o primeiro IP da lista desse header.
    Atenção: NUNCA ligar essa flag sem ter certeza disso, porque
    X-Forwarded-For é só um header HTTP comum -- qualquer cliente pode
    mandar o valor que quiser nele. Se não há proxy confiável reescrevendo
    esse header antes de chegar aqui, confiar nele permite burlar o rate
    limit trivialmente (manda um X-Forwarded-For diferente a cada
    requisição)."""
    if settings.TRUST_PROXY_HEADERS:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            first_ip = forwarded_for.split(",")[0].strip()
            if first_ip:
                return first_ip

    return request.client.host if request.client else "unknown"
