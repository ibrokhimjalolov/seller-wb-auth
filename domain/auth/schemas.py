from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, date


class UserCreate(BaseModel):
    """Схема для создания пользователя"""
    user_id: int = Field(..., description="ID пользователя в Telegram")


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CookieCreate(BaseModel):
    """Схема для создания куки"""
    name: str = Field(..., description="Название куки")
    value: str = Field(..., description="Значение куки")
    expire_date: Optional[datetime] = Field(None, description="Дата истечения куки")


class CookieResponse(BaseModel):
    """Схема ответа с данными куки"""
    id: int
    name: str
    value: str
    expire_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserWithCookiesResponse(BaseModel):
    """Схема ответа с пользователем и куками"""
    success: bool


class RequestAuthRequest(BaseModel):
    """Схема для запроса кода авторизации"""
    phone: str = Field(..., description="Номер телефона в формате 9991231212")


class RequestAuthResponse(BaseModel):
    """Схема ответа запроса авторизации"""
    success: bool
    message: str


class ConfirmAuthRequest(BaseModel):
    """Схема для подтверждения авторизации"""
    phone: str = Field(..., description="Номер телефона в формате 9991231212")
    verification_code: str = Field(..., description="6-значный код из SMS")


class ConfirmAuthResponse(BaseModel):
    """Схема ответа подтверждения авторизации"""
    success: bool
    message: str
    user_id: Optional[int] = None
    context: Optional[dict] = None


class CookiesResponse(BaseModel):
    """Схема ответа с куками"""
    user_id: int
    cookies: List[Dict[str, str]]


class ErrorResponse(BaseModel):
    """Схема ответа с ошибкой"""
    error: str
    message: str


class BookRequest(BaseModel):
    phone: str
    supply_id: int
    dt: date


class BookResponse(BaseModel):
    success: bool
    message: str
