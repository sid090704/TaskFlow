from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    avatar_url: str | None
    is_active: bool

    model_config = {
        "from_attributes": True
    }
    
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str