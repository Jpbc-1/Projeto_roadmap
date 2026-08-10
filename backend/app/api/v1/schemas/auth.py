from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = Field(None, min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")


class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: Optional[str]

    class Config:
        from_attributes = True 


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GoogleLoginRequest(BaseModel):
    # ID token que o app recebe do SDK nativo do Google Sign-In -- NÃO é
    # um código de autorização, é o JWT já pronto pra ser verificado.
    id_token: str


class FacebookLoginRequest(BaseModel):
    # Access token que o app recebe do SDK nativo do Facebook Login.
    access_token: str