from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import PORT
from api.routes import auth


# Создаем приложение FastAPI
app = FastAPI(
    title="Wildberries Auth Service",
    description="Микросервис для авторизации в Wildberries",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(auth.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {"message": "Wildberries Auth Service API"}


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy"}


if __name__ == "__main__":
    port = PORT
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
    )
