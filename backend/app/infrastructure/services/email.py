import logging

logger = logging.getLogger(__name__)


async def send_verification_email(email: str, token: str) -> None:
    """STUB -- não manda e-mail nenhum de verdade ainda, só loga. Antes,
    o token gerado aqui voltava direto na resposta HTTP de POST
    /auth/send-verify-email, o que anulava o propósito da verificação
    (qualquer um podia se "auto-verificar" sem nunca ter acesso à caixa
    de entrada). Isso foi corrigido no endpoint (o token não sai mais na
    resposta), mas a integração de envio de verdade ainda está pendente
    aqui -- precisa de credenciais de um provedor (Resend, SendGrid, AWS
    SES, ou SMTP genérico) que não estão disponíveis neste ambiente pra
    configurar. Até lá, o link fica visível SÓ no log do servidor (ver
    api/v1/endpoints/auth.py::send_verify_email), nunca em nenhuma
    resposta de API.

    Pra plugar um provedor de verdade: troque o corpo desta função pela
    chamada HTTP/SDK do provedor escolhido, usando um link no formato
    f"{FRONTEND_OU_API_BASE_URL}/api/v1/auth/verify-email?token={token}"
    -- o resto do fluxo (geração/validação do token, endpoint) já está
    pronto e não muda.
    """
    logger.warning(
        "EMAIL NÃO ENVIADO DE VERDADE (stub sem provedor configurado) -- "
        "destinatário=%s. Ver docstring de send_verification_email.",
        email,
    )
