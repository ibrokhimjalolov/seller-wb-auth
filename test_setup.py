#!/usr/bin/env python3
"""
Тестовый скрипт для проверки настройки микросервиса
"""

import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


async def test_database_connection():
    """Тест подключения к базе данных"""
    try:
        from database.base import async_engine, Base
        
        # Проверяем подключение
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Подключение к базе данных успешно")
            
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False
    
    return True

async def test_models():
    """Тест моделей"""
    try:
        from database.models import User, Cookie
        from database.base import Base
        
        # Проверяем, что модели определены
        assert User.__tablename__ == "users"
        assert Cookie.__tablename__ == "cookies"
        print("✅ Модели определены корректно")
        
    except Exception as e:
        print(f"❌ Ошибка в моделях: {e}")
        return False
    
    return True

async def test_repositories():
    """Тест репозиториев"""
    try:
        from database.repositories import UserRepository, CookieRepository, DatabaseManager
        from database.base import async_session_maker
        
        async with async_session_maker() as session:
            db_manager = DatabaseManager(session)
            
            # Проверяем создание пользователя
            user = await db_manager.users.create_user("test_user_123")
            assert user.user_id == "test_user_123"
            print("✅ Репозитории работают корректно")
            
            # Удаляем тестового пользователя
            await db_manager.users.delete_user("test_user_123")
            
    except Exception as e:
        print(f"❌ Ошибка в репозиториях: {e}")
        return False
    
    return True

async def test_auth_service():
    """Тест сервиса авторизации"""
    try:
        from domain.auth.auth_service import WildberriesAuthService
        from database.base import async_session_maker
        
        async with async_session_maker() as session:
            auth_service = WildberriesAuthService(session)
            
            # Проверяем создание пользователя
            user = await auth_service.create_user("test_auth_user")
            assert user.user_id == "test_auth_user"
            print("✅ Сервис авторизации работает корректно")
            
            # Удаляем тестового пользователя
            await auth_service.delete_user("test_auth_user")
            
    except Exception as e:
        print(f"❌ Ошибка в сервисе авторизации: {e}")
        return False
    
    return True

async def test_schemas():
    """Тест схем"""
    try:
        from domain.auth.schemas import UserCreate, AuthRequest, AuthResponse
        
        # Проверяем создание схем
        user_create = UserCreate(user_id="test_schema_user")
        assert user_create.user_id == "test_schema_user"
        
        auth_request = AuthRequest(
            user_id="test_user",
            phone="9991231212",
            verification_code="123456"
        )
        assert auth_request.user_id == "test_user"
        
        auth_response = AuthResponse(
            success=True,
            message="Test message",
            user_id="test_user"
        )
        assert auth_response.success is True
        
        print("✅ Схемы работают корректно")
        
    except Exception as e:
        print(f"❌ Ошибка в схемах: {e}")
        return False
    
    return True

async def main():
    """Главная функция тестирования"""
    print("🧪 Запуск тестов настройки микросервиса...")
    print("=" * 50)
    
    tests = [
        ("Подключение к БД", test_database_connection),
        ("Модели", test_models),
        ("Репозитории", test_repositories),
        ("Сервис авторизации", test_auth_service),
        ("Схемы", test_schemas),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Тестирование: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Результаты тестирования:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Итого: {passed}/{len(results)} тестов пройдено")
    
    if passed == len(results):
        print("🎉 Все тесты пройдены! Микросервис готов к работе.")
        print("\n📝 Следующие шаги:")
        print("1. Создайте файл .env с настройками базы данных")
        print("2. Запустите сервис: python main.py")
        print("3. Откройте API документацию: http://localhost:8000/docs")
    else:
        print("⚠️  Некоторые тесты не пройдены. Проверьте настройки.")

if __name__ == "__main__":
    asyncio.run(main()) 
