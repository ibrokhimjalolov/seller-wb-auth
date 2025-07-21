from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData

from config import DB_URL

# Создаем базовый класс для моделей
Base = declarative_base()

# Метаданные для управления миграциями
metadata = MetaData()

# Создаем асинхронный движок
async_engine = create_async_engine(
    DB_URL,
    echo=True,  # Логирование SQL запросов
    pool_pre_ping=True,
    pool_recycle=300,
)

# Создаем фабрику сессий
async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Функция для получения сессии
async def get_async_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
