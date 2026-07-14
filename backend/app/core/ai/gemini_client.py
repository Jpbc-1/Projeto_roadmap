import json
from typing import Any, Dict, Optional

import httpx


class GeminiAPIError(Exception):
    """Levantado quando a API do Gemini responde com erro ou formato inesperado."""


class GeminiClient:
    """Wrapper fino sobre a API REST do Gemini. Não conhece regra de negócio —
    só sabe enviar um prompt e devolver JSON estruturado."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    async def generate_json(
        self,
        prompt: str,
        system_instruction: str,
        response_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Envia o prompt e força a resposta a vir em JSON, validando contra
        um schema opcional (recurso nativo do Gemini, evita texto solto)."""

        url = f"{self.BASE_URL}/{self.model}:generateContent"
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

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise GeminiAPIError(f"Gemini retornou {response.status_code}: {response.text[:300]}")

        data = response.json()

        try:
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise GeminiAPIError(f"Resposta do Gemini em formato inesperado: {exc}") from exc