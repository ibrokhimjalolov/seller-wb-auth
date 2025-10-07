from typing import List, Dict, Optional
from datetime import datetime
import undetected_chromedriver as uc
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from database.repositories import DatabaseManager
from database.models import User
from .auth import request_code, verify_code


sessions = {}


class WildberriesAuthService:
    """Сервис для авторизации в Wildberries"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.db_manager = DatabaseManager(session)
        # Хранилище активных сессий (в продакшене лучше использовать Redis)
        self._active_sessions = sessions

    async def create_user(self, user_id: int) -> User:
        """Создать нового пользователя"""
        return await self.db_manager.users.create_user(user_id)

    async def get_user(self, user_id: int) -> Optional[User]:
        """Получить пользователя"""
        return await self.db_manager.users.get_user_by_id(user_id)

    async def get_user_with_cookies(self, user_id: int) -> Optional[User]:
        """Получить пользователя с куками"""
        return await self.db_manager.users.get_user_with_cookies(user_id)

    async def save_cookies(self, user_id: int, cookies: List[Dict]) -> bool:
        """Сохранить куки пользователя"""
        user = await self.get_user(user_id)
        if not user:
            return False

        # Удаляем старые куки
        await self.db_manager.cookies.delete_all_cookies_by_user(user.id)

        # Сохраняем новые куки
        for cookie_data in cookies:
            name = cookie_data.get('name')
            value = cookie_data.get('value')
            expiry = cookie_data.get('expiry')

            if name and value:
                expire_date = None
                if expiry:
                    expire_date = datetime.fromtimestamp(expiry)

                await self.db_manager.cookies.create_cookie(
                    user_id=user.id,
                    name=name,
                    value=value,
                    expire_date=expire_date
                )

        return True

    async def get_user_cookies(self, user_id: int) -> List[Dict]:
        """Получить куки пользователя"""
        user = await self.get_user_with_cookies(user_id)
        if not user:
            return []

        cookies = []
        for cookie in user.cookies:
            cookie_dict = {
                'name': cookie.name,
                'value': cookie.value,
                'expire_date': cookie.expire_date.isoformat() if cookie.expire_date else None
            }
            cookies.append(cookie_dict)

        return cookies

    async def request_auth(self, user_id: int, phone: str) -> Dict:
        """Запрос кода авторизации (первый этап)"""
        try:
            # Создаем драйвер
            driver = uc.Chrome(headless=True)

            # Запрашиваем код
            request_code(driver, phone)

            # Генерируем уникальный session_id
            session_id = str(uuid.uuid4())

            # Сохраняем сессию
            self._active_sessions[session_id] = {
                'user_id': user_id,
                'phone': phone,
                'driver': driver,
                'created_at': datetime.utcnow()
            }

            # Создаем или получаем пользователя
            user = await self.get_user(user_id)
            if not user:
                user = await self.create_user(user_id)

            return {
                'success': True,
                'message': 'Код подтверждения отправлен на указанный номер',
                'user_id': user_id,
                'session_id': session_id
            }

        except Exception as e:
            print(f"Ошибка запроса авторизации: {e}")
            return {
                'success': False,
                'message': f'Ошибка запроса кода: {str(e)}',
                'user_id': user_id,
                'session_id': None
            }

    async def confirm_auth(self, user_id: int, phone: str, verification_code: str, session_id: str) -> Dict:
        """Подтверждение авторизации (второй этап)"""
        try:
            # Проверяем сессию
            if session_id not in self._active_sessions:
                return {
                    'success': False,
                    'message': 'Сессия не найдена или истекла. Запросите код заново.',
                    'user_id': user_id
                }

            session_data = self._active_sessions[session_id]

            # Проверяем соответствие данных
            if session_data['user_id'] != user_id or session_data['phone'] != phone:
                return {
                    'success': False,
                    'message': 'Данные сессии не соответствуют запросу',
                    'user_id': user_id
                }

            driver = session_data['driver']

            # Вводим код и получаем куки
            cookies = verify_code(driver, verification_code)

            # Закрываем драйвер
            driver.quit()

            # Удаляем сессию
            del self._active_sessions[session_id]

            # Сохраняем куки
            await self.save_cookies(user_id, cookies)

            return {
                'success': True,
                'message': 'Пользователь успешно аутентифицирован',
                'user_id': user_id
            }

        except Exception as e:
            print(f"Ошибка подтверждения авторизации: {e}")
            return {
                'success': False,
                'message': f'Ошибка подтверждения: {str(e)}',
                'user_id': user_id
            }

    async def refresh_cookies(self, user_id: int) -> bool:
        """Обновить куки пользователя"""
        # Здесь можно добавить логику для обновления куки
        # Например, проверка срока действия и повторная авторизация
        user = await self.get_user_with_cookies(user_id)
        if not user:
            return False

        # Проверяем истекшие куки
        expired_cookies = await self.db_manager.cookies.get_expired_cookies()
        for cookie in expired_cookies:
            if cookie.user_id == user.id:
                await self.db_manager.cookies.delete_cookie(cookie.id)

        return True

    async def delete_user(self, user_id: int) -> bool:
        """Удалить пользователя и все его куки"""
        return await self.db_manager.users.delete_user(user_id)

    def cleanup_expired_sessions(self):
        """Очистка истекших сессий"""
        current_time = datetime.utcnow()
        expired_sessions = []

        for session_id, session_data in self._active_sessions.items():
            # Сессии истекают через 10 минут
            if (current_time - session_data['created_at']).total_seconds() > 600:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            session_data = self._active_sessions[session_id]
            if 'driver' in session_data:
                try:
                    session_data['driver'].quit()
                except:
                    pass
            del self._active_sessions[session_id] 
