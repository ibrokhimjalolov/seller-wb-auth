from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.base import get_async_session
from domain.auth.auth_service import WildberriesAuthService
from domain.auth.schemas import (
    UserWithCookiesResponse,
    RequestAuthRequest, RequestAuthResponse, ConfirmAuthRequest,
    ConfirmAuthResponse,
    BookResponse, BookRequest
)

router = APIRouter(prefix="/auth", tags=["Авторизация"])


@router.post("/request", response_model=RequestAuthResponse)
async def request_auth(
    auth_data: RequestAuthRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Запрос кода авторизации (первый этап)"""
    try:
        auth_service = WildberriesAuthService(session)

        result = await auth_service.request_auth(
            phone=auth_data.phone
        )

        return RequestAuthResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.post("/confirm", response_model=ConfirmAuthResponse)
async def confirm_auth(
    auth_data: ConfirmAuthRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Подтверждение авторизации (второй этап)"""
    try:
        auth_service = WildberriesAuthService(session)

        result = await auth_service.confirm_auth(
            phone=auth_data.phone,
            verification_code=auth_data.verification_code,
        )

        return ConfirmAuthResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/users/{phone}", response_model=UserWithCookiesResponse)
async def get_user_with_cookies(
    phone: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Получить пользователя с куками"""
    try:
        auth_service = WildberriesAuthService(session)
        success = phone in auth_service._active_sessions

        return UserWithCookiesResponse(
            success=success
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.post("/book", response_model=BookResponse)
async def book(
    book_data: BookRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Получить куки пользователя"""
    try:

        auth_service = WildberriesAuthService(session)
        result = await auth_service.book(book_data)
        return BookResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )
