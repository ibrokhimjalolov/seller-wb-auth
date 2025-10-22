from typing import List, Dict, Optional
from datetime import datetime, date
import undetected_chromedriver as uc
from sqlalchemy.ext.asyncio import AsyncSession
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from database.repositories import DatabaseManager
from database.models import User
from domain.auth.schemas import BookRequest
from .auth import request_code, verify_code
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import os

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

    def create_new_driver(self, phone: str):
        """Создаем новый драйвер для пользователя"""
        profile_dir = os.path.abspath(f"chrome_profile/{phone}")

        options = Options()
        options.add_argument(f"--user-data-dir={profile_dir}")  # ✅ persistent browser profile
        options.add_argument("--profile-directory=Default")

        return uc.Chrome(headless=False, options=options)

    async def request_auth(self, phone: str) -> Dict:
        """Запрос кода авторизации (первый этап)"""
        try:
            # Создаем драйвер

            driver = self.create_new_driver(phone)

            # Запрашиваем код
            request_code(driver, phone)

            time.sleep(5)

            # Генерируем уникальный session_id
            session_id = phone

            # Сохраняем сессию
            self._active_sessions[session_id] = {
                'phone': phone,
                'driver': driver,
                'created_at': datetime.utcnow(),
                'verified': False,
            }

            if "Запрос кода возможен через" in driver.page_source:
                # Закрываем драйвер
                driver.quit()

                # Удаляем сессию
                del self._active_sessions[session_id]
                return {
                    'success': False,
                    'message': 'Запрос кода возможен через некоторое время. Попробуйте позже.',
                }
            return {
                'success': True,
                'message': 'Код подтверждения отправлен на указанный номер',
                'session_id': session_id
            }

        except Exception as e:
            print(f"Ошибка запроса авторизации: {e}")
            return {
                'success': False,
                'message': f'Ошибка запроса кода: {str(e)}',
                'session_id': None
            }

    async def confirm_auth(self, phone: str, verification_code: str) -> Dict:
        """Подтверждение авторизации (второй этап)"""
        try:
            # Проверяем сессию
            if phone not in self._active_sessions:
                return {
                    'success': False,
                    'message': 'Сессия не найдена или истекла. Запросите код заново.',
                }

            session_data = self._active_sessions[phone]

            driver = session_data['driver']

            # Вводим код и получаем куки
            result = verify_code(driver, verification_code)

            if not result["success"]:
                # Закрываем драйвер
                driver.quit()

                # Удаляем сессию
                del self._active_sessions[phone]
                return {
                    'success': False,
                    'message': 'Неверный код подтверждения',
                }

            return {
                'success': True,
                'message': 'Пользователь успешно аутентифицирован',
            }

        except Exception as e:
            print(f"Ошибка подтверждения авторизации: {e}")
            return {
                'success': False,
                'message': f'Ошибка подтверждения: {str(e)}',
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

    def close_popups(self, driver):
        """
        Принятие условий использования, если появляется соответствующий попап, чтобы не мешал дальнейшей работе.
        """

        try:
            buttons = driver.find_elements(By.XPATH, "//button[.//span[text()='Принимаю']]")
            if buttons:
                buttons[0].click()
        except Exception as ex:
            print(ex)

        try:
            buttons = driver.find_elements(By.XPATH, "div[class*='Button-tooltip'][role='button'][tabindex='0']")
            if buttons:
                buttons[0].click()
        except Exception as ex:
            print(ex)

        try:
            buttons = driver.find_elements(By.XPATH, "div[class*='Tooltip-hint-view__close-button'][aria-label='Close'][data-action='close']")
            if buttons:
                buttons[0].click()
        except Exception as ex:
            print(ex)

    async def book(self, book_data: BookRequest) -> Dict:
        """Бронирование товара"""

        driver = self.create_new_driver(book_data.phone)

        url = f"https://seller.wildberries.ru/supplies-management/all-supplies/supply-detail?preorderId&supplyId={book_data.supply_id}"

        driver.get(url)

        wait = WebDriverWait(driver, 30)

        self.close_popups(driver)

        if url != driver.current_url:
            driver.quit()
            print("⚠️ Redirected to another page, possibly not logged in.")
            return {
                'success': False,
                'message': 'Пользователь не авторизован',
                'code': 'NOT_AUTHENTICATED'
            }

        # Wait for any buttons to appear
        buttons = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "Supply-detail-options__plan-desktop-button__-N407e2FDC")))
        if len(buttons) >= 1:
            buttons[0].click()
        else:
            driver.quit()
            print("⚠️ Not enough buttons found on page.")
            return {
                'success': False,
                'message': 'Не удалось найти кнопку бронирования'
            }

        time.sleep(3)  # Let popup render
        self.close_popups(driver)
        confirm_pop_up = driver.find_elements(By.XPATH, """//*[@id="Portal-modal"]/div[5]/div/div/div[4]/div[1]/button""")
        if confirm_pop_up:
            confirm_pop_up[0].click()
            time.sleep(3)

        self.close_popups(driver)

        rows = driver.find_elements(By.TAG_NAME, "tr")
        target_date = get_formated_date(book_data.dt)

        for row in rows:
            items = row.find_elements(By.TAG_NAME, "td")
            for item in items:
                spans = item.find_elements(By.TAG_NAME, "span")
                if spans and target_date in spans[0].text:
                    driver.execute_script("arguments[0].scrollIntoView(true);", item)
                    popup_divs = item.find_elements(By.CSS_SELECTOR, "div.Custom-popup")

                    if popup_divs:

                        ActionChains(driver).scroll_to_element(item).move_to_element(item).perform()
                        button = item.find_elements(By.TAG_NAME, "button")[-1]
                        ActionChains(driver).move_to_element(button).perform()
                        button.click()
                        time.sleep(2)

                        driver.save_screenshot("screenshot.png")

                        confirm_buttons = driver.find_elements(By.TAG_NAME, "button")
                        for confirm_button in confirm_buttons:
                            if "Перенести" == confirm_button.text.strip():
                                driver.save_screenshot("screenshot1.png")
                                confirm_button.click()
                                wait.until(EC.invisibility_of_element(confirm_button))
                                driver.save_screenshot("screenshot2.png")
                                print("✅ Supply successfully booked.")

                                driver.quit()
                                return {
                                    'success': True,
                                    'message': 'Товар успешно забронирован'
                                }
        driver.quit()
        print("⚠️ Target date not found or booking failed.")
        return {
            'success': False,
            'message': 'Не удалось забронировать товар на указанную дату'
        }


def get_formated_date(d: date) -> str:
    month_names = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    return f"{d.day} {month_names[d.month - 1]}"
