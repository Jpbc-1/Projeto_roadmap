from dataclasses import dataclass
from typing import Optional


@dataclass
class OAuthProfile:
    """O que qualquer verificador de provider devolve, depois de confirmar
    que o token é de verdade -- formato único que o resto do código
    (LoginWithOAuthUseCase) consome sem saber qual provider foi."""

    provider: str  
    provider_user_id: str
    email: str
    name: Optional[str] = None
