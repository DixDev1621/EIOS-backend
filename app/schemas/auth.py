from pydantic import BaseModel, EmailStr, Field


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    requested_role: str = "citizen"  # citizen | researcher; officer/admin roles are granted manually


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
