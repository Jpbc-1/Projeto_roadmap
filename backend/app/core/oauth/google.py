import asyncio

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import settings
from app.core.oauth.profile import OAuthProfile


class GoogleTokenVerificationError(Exception):
    pass


async def verify_google_id_token(token: str) -> OAuthProfile:
    """
    O app mobile usa o SDK nativo do Google (Google Sign-In) e recebe um
    ID token de volta -- é ESSE token que chega aqui, não um código de
    autorização. Diferente do Facebook (ver facebook.py), esse token é um
    JWT assinado pelo Google: dá pra verificar a assinatura + validade +
    "pra quem foi emitido" offline, contra a chave pública do Google, sem
    round-trip nenhum pra API deles em tempo de request (certificados
    ficam em cache pela própria lib).
    """
    if not settings.GOOGLE_OAUTH_CLIENT_ID:
        raise GoogleTokenVerificationError("GOOGLE_OAUTH_CLIENT_ID não configurado no servidor.")

    try:
        claims = await asyncio.to_thread(
            google_id_token.verify_oauth2_token,
            token,
            google_requests.Request(),
            settings.GOOGLE_OAUTH_CLIENT_ID,
        )
    except ValueError as exc:
        raise GoogleTokenVerificationError(f"Token do Google inválido: {exc}") from exc

    if not claims.get("email_verified", False):
        raise GoogleTokenVerificationError("E-mail do Google não verificado.")

    return OAuthProfile(
        provider="google",
        provider_user_id=claims["sub"],
        email=claims["email"],
        name=claims.get("name"),
    )
