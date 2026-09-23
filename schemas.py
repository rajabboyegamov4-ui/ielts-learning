from pydantic import BaseModel, EmailStr
from models import GenderEnum

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    gender: GenderEnum

class UserResponse(BaseModel):
    id: int
    username: str
    balance: int
    current_level: str

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str
