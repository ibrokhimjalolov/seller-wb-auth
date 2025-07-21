from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.base import get_async_session
from domain.auth.auth_service import WildberriesAuthService
from domain.auth.schemas import (
    UserWithCookiesResponse,
    RequestAuthRequest, RequestAuthResponse, ConfirmAuthRequest,
    ConfirmAuthResponse,
    CookiesResponse
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
            user_id=auth_data.user_id,
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
            user_id=auth_data.user_id,
            phone=auth_data.phone,
            verification_code=auth_data.verification_code,
            session_id=auth_data.session_id
        )

        return ConfirmAuthResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=UserWithCookiesResponse)
async def get_user_with_cookies(
    user_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Получить пользователя с куками"""
    try:
        auth_service = WildberriesAuthService(session)
        user = await auth_service.get_user_with_cookies(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )

        return UserWithCookiesResponse.from_orm(user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/users/{user_id}/cookies", response_model=CookiesResponse)
async def get_user_cookies(
    user_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Получить куки пользователя"""
    try:
        auth_service = WildberriesAuthService(session)
        cookies = await auth_service.get_user_cookies(user_id)

        return CookiesResponse(
            user_id=user_id,
            cookies=cookies
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.delete("/users/{user_id}", response_model=ConfirmAuthResponse)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Удалить пользователя"""
    try:
        auth_service = WildberriesAuthService(session)
        success = await auth_service.delete_user(user_id)

        if success:
            return ConfirmAuthResponse(
                success=True,
                message="Пользователь успешно удален",
                user_id=user_id
            )
        else:
            return ConfirmAuthResponse(
                success=False,
                message="Пользователь не найден",
                user_id=user_id
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )
