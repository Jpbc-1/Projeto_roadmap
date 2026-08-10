from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import FacebookLoginRequest, GoogleLoginRequest, Token, UserCreate, UserOut
from app.application.auth.authenticate_user import (
    AuthenticateUserUseCase,
    InvalidCredentialsError,
)
from app.application.auth.login_with_oauth import LoginWithOAuthUseCase
from app.application.auth.register_user import (
    EmailAlreadyRegisteredError,
    RegisterUserUseCase,
    UsernameAlreadyTakenError,
)
from app.core.config import settings
from app.core.oauth.facebook import FacebookTokenVerificationError, verify_facebook_access_token
from app.core.oauth.google import GoogleTokenVerificationError, verify_google_id_token
from app.core.rate_limiter import login_rate_limiter
from app.core.security import create_access_token
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.oauth_account_repository import SQLAlchemyOAuthAccountRepository
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db_session)):
    repository = SQLAlchemyUserRepository(db)
    use_case = RegisterUserUseCase(repository)

    try:
        user = await use_case.execute(email=payload.email, password=payload.password, username=payload.username)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except UsernameAlreadyTakenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
):
    client_ip = request.client.host if request.client else "unknown"
    email_key = f"login:email:{form_data.username.strip().lower()}"
    ip_key = f"login:ip:{client_ip}"

    ip_ok, ip_retry = await login_rate_limiter.check(
        ip_key, settings.LOGIN_RATE_LIMIT_PER_IP, settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    )
    if not ip_ok:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login a partir deste endereço. Tente novamente mais tarde.",
            headers={"Retry-After": str(ip_retry)},
        )

    email_ok, email_retry = await login_rate_limiter.check(
        email_key, settings.LOGIN_RATE_LIMIT_PER_EMAIL, settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    )
    if not email_ok:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login para este e-mail. Tente novamente mais tarde.",
            headers={"Retry-After": str(email_retry)},
        )

    repository = SQLAlchemyUserRepository(db)
    use_case = AuthenticateUserUseCase(repository)

    try:
        user = await use_case.execute(email=form_data.username, password=form_data.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    await login_rate_limiter.reset(email_key)

    access_token = create_access_token(subject=user.email)
    return Token(access_token=access_token)


@router.post("/oauth/google", response_model=Token)
async def login_with_google(payload: GoogleLoginRequest, db: AsyncSession = Depends(get_db_session)):
    try:
        profile = await verify_google_id_token(payload.id_token)
    except GoogleTokenVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    user_repository = SQLAlchemyUserRepository(db)
    oauth_account_repository = SQLAlchemyOAuthAccountRepository(db)
    use_case = LoginWithOAuthUseCase(user_repository, oauth_account_repository)
    user = await use_case.execute(profile)

    access_token = create_access_token(subject=user.email)
    return Token(access_token=access_token)


@router.post("/oauth/facebook", response_model=Token)
async def login_with_facebook(payload: FacebookLoginRequest, db: AsyncSession = Depends(get_db_session)):
    try:
        profile = await verify_facebook_access_token(payload.access_token)
    except FacebookTokenVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    user_repository = SQLAlchemyUserRepository(db)
    oauth_account_repository = SQLAlchemyOAuthAccountRepository(db)
    use_case = LoginWithOAuthUseCase(user_repository, oauth_account_repository)
    user = await use_case.execute(profile)

    access_token = create_access_token(subject=user.email)
    return Token(access_token=access_token)


# Nota pro Apple Sign In (mencionado como "depois"): quando chegar a hora,
# é um 3º verificador em app/core/oauth/apple.py (mais parecido com o do
# Google -- Apple também usa JWT assinado, mas com uma chave que gira e
# precisa ser buscada num JWKS endpoint) + uma rota /oauth/apple igual a
# essas duas. LoginWithOAuthUseCase já está pronto pra receber esse
# terceiro provider sem mudar nada nele.