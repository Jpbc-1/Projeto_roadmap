"""Exceções cruas (str(exc)) podem vazar detalhe técnico interno -- stack
trace, nome de driver de banco, string de conexão parcial, nome de serviço
interno -- pro dono do recurso, que só devia saber QUE algo deu errado, não
COMO por dentro. Usado em qualquer lugar que hoje guarda/expõe
generation_error, last_error, ou uma resposta de erro de endpoint."""

import logging

logger = logging.getLogger("app.errors")


def safe_error_message(exc: Exception, context: str) -> str:
    """Loga a exceção completa (só no log do servidor, nunca na resposta)
    e devolve uma mensagem genérica segura pra guardar no banco ou expor
    via API. Quando a causa raiz for a IA sobrecarregada (503, mesmo após
    esgotar toda a cadeia de fallback -- ver GeminiClient), a mensagem é
    mais específica: ajuda o usuário a saber que vale tentar de novo em
    vez de achar que quebrou de vez."""
    logger.error("%s", context, exc_info=exc)
    if getattr(exc, "status_code", None) == 503:
        return f"{context}: nossa IA está sobrecarregada no momento. Tente novamente em alguns minutos."
    return f"{context}. Tente novamente em alguns instantes; se persistir, contate o suporte."
