from typing import Any, Dict, List, Optional

import httpx

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


EXPO_MAX_MESSAGES_PER_REQUEST = 100


class ExpoPushAPIError(Exception):
    """Levantado quando a requisição INTEIRA pro Expo falha (HTTP não-2xx —
    ex: payload malformado, credenciais erradas, muitas mensagens no lote).

    Não confundir com um erro de UM token específico dentro de um lote que
    respondeu 200: isso não é uma exceção, é um item com status="error"
    dentro de "data" (ver send_push_batch) -- tratado individualmente por
    quem chama, não aqui.

    Carrega status_code pelo mesmo motivo do GeminiAPIError (ver
    app/core/ai/gemini_client.py): quem pegar essa exceção decide o que
    fazer sem precisar fazer parsing de mensagem de erro."""

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


async def send_push_batch(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Manda até EXPO_MAX_MESSAGES_PER_REQUEST mensagens numa única
    requisição pro Expo Push API.

    messages: [{"to": token, "title": ..., "body": ..., "data": {...}}, ...]
    Não faz chunking sozinho -- quem chama (_send_push, em
    app/core/jobs/handlers.py) decide o tamanho de cada lote antes de
    chamar esta função; ela levanta ValueError se receber mais que o
    limite, em vez de silenciosamente deixar o Expo rejeitar o lote
    inteiro com um erro mais difícil de rastrear.

    Devolve o corpo cru da resposta: um "push ticket" por mensagem
    enviada, na mesma ordem em que foram mandadas (ver
    https://docs.expo.dev/push-notifications/sending-notifications/#push-tickets).
    Cada ticket tem status "ok" (com "id") ou "error" (com "message" e
    "details.error", ex: "DeviceNotRegistered").

    Nota sobre o "id" do ticket: a Expo o chama de receipt ID e ele serve
    pra consultar, depois, um endpoint separado (/push/getReceipts) que
    confirma se a entrega chegou de fato no FCM/APNs -- é o mecanismo
    "oficial" deles pra pegar DeviceNotRegistered com mais certeza (entre
    outros erros, tipo MessageTooBig, que segundo a doc da Expo só
    aparecem nesse segundo passo, não no ticket imediato). Não
    implementamos esse segundo passo aqui de propósito -- exigiria
    guardar os ticket ids em algum lugar e um novo job periódico só pra
    consultá-los -- e o ticket imediato já É suficiente pro caso que
    importa aqui (DeviceNotRegistered pode aparecer nele também, ver
    _send_push). Fica registrado como uma melhoria futura possível, não
    como algo quebrado.

    Levanta ExpoPushAPIError só se a requisição INTEIRA falhar (HTTP
    não-2xx). Erro de um token específico dentro de um lote que
    respondeu 200 não levanta exceção — vem como "status": "error"
    dentro de "data", tratado por quem chama."""
    if not messages:
        return {"data": []}
    if len(messages) > EXPO_MAX_MESSAGES_PER_REQUEST:
        raise ValueError(
            f"send_push_batch recebeu {len(messages)} mensagens; o Expo aceita no "
            f"máximo {EXPO_MAX_MESSAGES_PER_REQUEST} por requisição — quem chama "
            f"precisa dividir em chunks antes (ver _send_push em core/jobs/handlers.py)."
        )

    client = _get_http_client()
    response = await client.post(
        EXPO_PUSH_URL,
        json=messages,
        headers={"accept": "application/json", "content-type": "application/json"},
        timeout=10.0,
    )

    if response.status_code != 200:
        raise ExpoPushAPIError(
            f"Expo Push API retornou {response.status_code}: {response.text[:300]}",
            status_code=response.status_code,
        )

    return response.json()
