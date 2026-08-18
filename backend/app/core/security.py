from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DUMMY_HASH = pwd_context.hash("vascomaiorqueflamengo")


def hash_password(password: str) -> str:
    """Transforma a senha em texto puro em um hash bcrypt (nunca guardamos senha crua)."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara a senha digitada no login com o hash salvo no banco."""
    return pwd_context.verify(plain_password, hashed_password)

def verify_dummy_hash():
    """Verifica se o hash dummy é válido (para evitar ataques de timing)."""
    return pwd_context.verify("vascomaiorqueflamengo", DUMMY_HASH)

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Gera um JWT contendo o e-mail do usuário (subject) e uma data de expiração."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """Valida o JWT e retorna o e-mail (subject) contido nele, ou None se inválido/expirado."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

def create_email_verification_token(email: str) -> str:
    """Gera um token JWT válido por 24 horas para verificação de e-mail."""
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode = {"exp": expire, "sub": email, "type": "email_verification"}
    
    # Usa a mesma SECRET_KEY e algoritmo do sistema de login
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_email_token(token: str) -> Optional[str]:
    """Decodifica o token e retorna o e-mail se for válido."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "email_verification":
            return None
        return payload.get("sub")
    except JWTError:
        return None    
