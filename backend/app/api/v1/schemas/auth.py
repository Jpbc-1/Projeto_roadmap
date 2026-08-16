from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    username: Optional[str] = Field(None, min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")

    @field_validator("password")
    @classmethod
    def password_must_fit_bcrypt(cls, v: str) -> str:
        """bcrypt (ver app/core/security.py, usado via passlib) só enxerga
        os primeiros 72 BYTES da senha -- qualquer coisa depois disso é
        IGNORADA silenciosamente, tanto no hash quanto na verificação.
        Confirmei isso na prática com as versões exatas deste projeto
        (passlib==1.7.4 + bcrypt==4.0.1): gerei o hash de uma senha de 100
        bytes e ele bateu certinho contra uma segunda senha que só repetia
        os primeiros 72 bytes da primeira e mudava tudo depois -- ou seja,
        sem essa validação, alguém pode digitar uma senha de 200 caracteres
        achando que está mais segura, sem saber que só uma fração dela é
        levada em conta de verdade.

        É em BYTES, não caracteres: com acento/emoji, 72 caracteres já pode
        passar de 72 bytes bem antes (cada caractere acentuado ocupa 2
        bytes em UTF-8, e é exatamente o alfabeto mais comum pra quem
        escreve em português). Por isso o limite é aplicado aqui, em cima
        do valor codificado em utf-8, e não como max_length no Field acima
        (que contaria caracteres).

        Rejeitar (em vez de simplesmente truncar em silêncio, que é o que
        o bcrypt já faz sozinho) segue o mesmo princípio já usado em outros
        campos do projeto (ver GoalAnswersRequest em schemas/goals.py):
        avisar a pessoa que o valor não coube, não fingir que coube."""
        if len(v.encode("utf-8")) > 72:
            raise ValueError(
                "A senha não pode passar de 72 bytes (aproximadamente 72 caracteres "
                "sem acento/emoji, menos que isso se usar acentos/emoji)."
            )
        return v


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