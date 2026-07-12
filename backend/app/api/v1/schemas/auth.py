from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True  # permite criar isso a partir de um objeto ORM (User)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
