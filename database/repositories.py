from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from .models import User, Cookie
from .base import Base


class UserRepository:
    """Репозиторий для работы с пользователями"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user_id: int) -> User:
        """Создать нового пользователя"""
        user = User(id=user_id)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по user_id"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_with_cookies(self, user_id: int) -> Optional[User]:
        """Получить пользователя с куками"""
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.cookies))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_all_users(self) -> List[User]:
        """Получить всех пользователей"""
        result = await self.session.execute(select(User))
        return list(result.scalars().all())

    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Обновить пользователя"""
        user = await self.get_user_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            await self.session.commit()
            await self.session.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> bool:
        """Удалить пользователя"""
        user = await self.get_user_by_id(user_id)
        if user:
            await self.session.delete(user)
            await self.session.commit()
            return True
        return False


class CookieRepository:
    """Репозиторий для работы с куками"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_cookie(self, user_id: int, name: str, value: str, expire_date: Optional[datetime] = None) -> Cookie:
        """Создать новую куку"""
        cookie = Cookie(
            user_id=user_id,
            name=name,
            value=value,
            expire_date=expire_date
        )
        self.session.add(cookie)
        await self.session.commit()
        await self.session.refresh(cookie)
        return cookie

    async def get_cookies_by_user_id(self, user_id: int) -> List[Cookie]:
        """Получить все куки пользователя"""
        result = await self.session.execute(
            select(Cookie).where(Cookie.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_cookie_by_name_and_user(self, user_id: int, name: str) -> Optional[Cookie]:
        """Получить куку по имени и пользователю"""
        result = await self.session.execute(
            select(Cookie).where(
                Cookie.user_id == user_id,
                Cookie.name == name
            )
        )
        return result.scalar_one_or_none()

    async def update_cookie(self, cookie_id: int, **kwargs) -> Optional[Cookie]:
        """Обновить куку"""
        result = await self.session.execute(
            select(Cookie).where(Cookie.id == cookie_id)
        )
        cookie = result.scalar_one_or_none()
        if cookie:
            for key, value in kwargs.items():
                if hasattr(cookie, key):
                    setattr(cookie, key, value)
            await self.session.commit()
            await self.session.refresh(cookie)
        return cookie

    async def delete_cookie(self, cookie_id: int) -> bool:
        """Удалить куку"""
        result = await self.session.execute(
            select(Cookie).where(Cookie.id == cookie_id)
        )
        cookie = result.scalar_one_or_none()
        if cookie:
            await self.session.delete(cookie)
            await self.session.commit()
            return True
        return False

    async def delete_all_cookies_by_user(self, user_id: int) -> bool:
        """Удалить все куки пользователя"""
        await self.session.execute(
            delete(Cookie).where(Cookie.user_id == user_id)
        )
        await self.session.commit()
        return True

    async def get_expired_cookies(self) -> List[Cookie]:
        """Получить все истекшие куки"""
        result = await self.session.execute(
            select(Cookie).where(
                Cookie.expire_date < datetime.utcnow()
            )
        )
        return list(result.scalars().all())


class DatabaseManager:
    """Менеджер для работы с базой данных"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.cookies = CookieRepository(session)

    async def create_tables(self):
        """Создать все таблицы"""
        async with self.session.begin():
            await self.session.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """Удалить все таблицы"""
        async with self.session.begin():
            await self.session.run_sync(Base.metadata.drop_all)
