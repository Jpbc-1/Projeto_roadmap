from app.core.security import create_email_verification_token, verify_email_token
from app.infrastructure.services.email import send_verification_email
from app.domain.repositories.user_repository import UserRepository

class InvalidTokenError(Exception):
    """Exceção lançada quando o token de verificação de e-mail é inválido ou expirou."""
    pass

class SendVerificationEmailUseCase:
    async def execute(self, email: str):
        token = create_email_verification_token(email)
        await send_verification_email(email, token)
        return token  # Adicione esta linha!

class ConfirmEmailUseCase:
    def __init__(self, user_repository: UserRepository, db_session):
        self.user_repository = user_repository
        self.db_session = db_session

    async def execute(self, token: str):
        # 1. Tenta abrir o token e pegar o e-mail
        email = verify_email_token(token)
        if not email:
            raise InvalidTokenError("Token de verificação inválido ou expirado.")
        
        # 2. Busca o usuário no banco
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise InvalidTokenError("Usuário não encontrado.")
        
        # 3. Atualiza a coluna que você criou no Passo 1!
        user.email_verified = True
        await self.db_session.commit()
        
        return user