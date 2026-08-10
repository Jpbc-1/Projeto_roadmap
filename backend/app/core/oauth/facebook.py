import httpx

from app.core.config import settings
from app.core.oauth.profile import OAuthProfile


class FacebookTokenVerificationError(Exception):
    pass


async def verify_facebook_access_token(access_token: str) -> OAuthProfile:
    """
    Diferente do Google, o access token do Facebook é OPACO -- não dá pra
    verificar sozinho, precisa perguntar pra Meta. Duas chamadas:

    1) /debug_token confirma que o token é válido E foi emitido PRO NOSSO
       app (checando app_id) -- sem isso, um token válido de outro app na
       Meta passaria pela chamada seguinte sem a gente perceber que não
       era destinado a nós.
    2) só DEPOIS disso confirmado, busca o perfil de verdade em /me.
    """
    if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
        raise FacebookTokenVerificationError("Credenciais do Facebook não configuradas no servidor.")

    app_access_token = f"{settings.FACEBOOK_APP_ID}|{settings.FACEBOOK_APP_SECRET}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            debug_response = await client.get(
                "https://graph.facebook.com/debug_token",
                params={"input_token": access_token, "access_token": app_access_token},
            )
            debug_response.raise_for_status()
        except httpx.HTTPError as exc:
            raise FacebookTokenVerificationError(f"Falha ao validar token com o Facebook: {exc}") from exc

        debug_data = debug_response.json().get("data", {})
        if not debug_data.get("is_valid"):
            raise FacebookTokenVerificationError("Token do Facebook inválido ou expirado.")
        if debug_data.get("app_id") != settings.FACEBOOK_APP_ID:
            raise FacebookTokenVerificationError("Token do Facebook não foi emitido para este app.")

        try:
            profile_response = await client.get(
                "https://graph.facebook.com/me",
                params={"fields": "id,name,email", "access_token": access_token},
            )
            profile_response.raise_for_status()
        except httpx.HTTPError as exc:
            raise FacebookTokenVerificationError(f"Falha ao buscar perfil no Facebook: {exc}") from exc

        profile = profile_response.json()

    email = profile.get("email")
    if not email:
        raise FacebookTokenVerificationError("Sua conta do Facebook não tem e-mail verificado associado.")

    return OAuthProfile(
        provider="facebook",
        provider_user_id=profile["id"],
        email=email,
        name=profile.get("name"),
    )
