from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import Token, UserCreate, UserOut
from app.application.auth.authenticate_user import (
    AuthenticateUserUseCase,
    InvalidCredentialsError,
)
from app.application.auth.register_user import (
    EmailAlreadyRegisteredError,
    RegisterUserUseCase,
    UsernameAlreadyTakenError,
)
from app.core.security import create_access_token
from app.infrastructure.database.session import get_db_session
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
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyUserRepository(db)
    use_case = AuthenticateUserUseCase(repository)

    try:
        user = await use_case.execute(email=form_data.username, password=form_data.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    access_token = create_access_token(subject=user.email)
    return Token(access_token=access_token)