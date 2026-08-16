import json
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx


class GeminiAPIError(Exception):
    """Levantado quando a API do Gemini responde com erro ou formato inesperado.

    Carrega o status_code HTTP quando ele existe (None para erros que não
    vieram de uma resposta HTTP, tipo JSON malformado), pra quem pegar essa
    exceção conseguir decidir o que fazer sem precisar fazer parsing da
    mensagem de erro."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


_shared_http_client: Optional[httpx.AsyncClient] = None


def _get_http_client() -> httpx.AsyncClient:
    global _shared_http_client
    if _shared_http_client is None:
        _shared_http_client = httpx.AsyncClient()
    return _shared_http_client


async def close_shared_http_client() -> None:
    """Chamado no shutdown do FastAPI (ver main.py) pra fechar as conexões
    de forma limpa em vez de deixar soltas quando o processo encerra."""
    global _shared_http_client
    if _shared_http_client is not None:
        await _shared_http_client.aclose()
        _shared_http_client = None


UsageCallback = Callable[[str, Dict[str, Any]], Awaitable[None]]


class GeminiClient:
    """Wrapper fino sobre a API REST do Gemini. Não conhece regra de negócio —
    só sabe enviar um prompt e devolver JSON estruturado.

    Suporta uma CADEIA de fallbacks (fallback_models, em ordem). Se a
    chamada com `model` falhar especificamente com 503 (modelo
    sobrecarregado -- o erro mais comum em horário de pico), tenta o
    próximo modelo da lista, e assim por diante, até acertar ou esgotar a
    lista. Erros que não são 503 (ex: API key inválida, prompt bloqueado,
    400) não acionam fallback nenhum -- trocar de modelo não resolve esses
    casos, só custaria uma chamada a mais à toa.

    on_usage, se passado, é chamado depois de CADA chamada bem-sucedida
    (inclusive fallback) com o uso de token real devolvido pelo Gemini --
    pensado pra alimentar app/core/ai/usage_logging.py, que só acumula em
    memória (não escreve no banco na hora), porque este client pode ser
    usado com chamadas concorrentes (ex: asyncio.gather em
    adapt_roadmap.py) e a AsyncSession do SQLAlchemy não é segura pra
    escrita concorrente."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(
        self,
        api_key: str,
        model: str,
        fallback_models: Optional[List[str]] = None,
        on_usage: Optional[UsageCallback] = None,
    ):
        self.api_key = api_key
        self.model = model
        seen = {model}
        self.fallback_models: List[str] = []
        for candidate in fallback_models or []:
            if candidate and candidate not in seen:
                self.fallback_models.append(candidate)
                seen.add(candidate)
        self.on_usage = on_usage

    async def generate_json(
        self,
        prompt: str,
        system_instruction: str,
        response_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Envia o prompt e força a resposta a vir em JSON, validando contra
        um schema opcional (recurso nativo do Gemini, evita texto solto)."""
        models_to_try = [self.model, *self.fallback_models]
        last_error: Optional[GeminiAPIError] = None

        for index, model in enumerate(models_to_try):
            try:
                return await self._request_json(model, prompt, system_instruction, response_schema)
            except GeminiAPIError as exc:
                last_error = exc
                is_last_attempt = index == len(models_to_try) - 1
                if exc.status_code != 503 or is_last_attempt:
                    raise
                

        raise last_error  

    async def _request_json(
        self,
        model: str,
        prompt: str,
        system_instruction: str,
        response_schema: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/{model}:generateContent"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        generation_config: Dict[str, Any] = {"responseMimeType": "application/json"}
        if response_schema is not None:
            generation_config["responseSchema"] = response_schema

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": generation_config,
        }

        client = _get_http_client()
        response = await client.post(url, headers=headers, json=payload, timeout=60.0)

        if response.status_code != 200:
            raise GeminiAPIError(
                f"Gemini ({model}) retornou {response.status_code}: {response.text[:300]}",
                status_code=response.status_code,
            )

        data = response.json()

        if self.on_usage is not None:
            usage = data.get("usageMetadata")
            if usage:
                await self.on_usage(model, usage)

        try:
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise GeminiAPIError(f"Resposta do Gemini ({model}) em formato inesperado: {exc}") from exc

    async def embed_text(self, text: str) -> List[float]:
        """Gera um vetor de embedding para o texto -- usado para comparar
        similaridade semântica (ex: detectar que 'loop' e 'laço de
        repetição' são o mesmo conceito). self.model deve ser um modelo de
        embedding (não um modelo de geração de texto)."""

        url = f"{self.BASE_URL}/{self.model}:embedContent"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {"content": {"parts": [{"text": text}]}}

        client = _get_http_client()
        response = await client.post(url, headers=headers, json=payload, timeout=30.0)

        if response.status_code != 200:
            raise GeminiAPIError(f"Gemini (embedding) retornou {response.status_code}: {response.text[:300]}")

        data = response.json()

        if self.on_usage is not None:
            usage = data.get("usageMetadata")
            if usage:
                await self.on_usage(self.model, usage)

        try:
            return data["embedding"]["values"]
        except KeyError as exc:
            raise GeminiAPIError(f"Resposta de embedding em formato inesperado: {exc}") from exc
