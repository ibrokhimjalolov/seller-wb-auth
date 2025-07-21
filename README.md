# Wildberries Auth Service

Микросервис для авторизации в Wildberries с сохранением куки в базе данных.

## Структура проекта

```
services/wildberries/
├── api/
│   └── routes/
│       └── auth.py          # API роуты для авторизации
├── database/
│   ├── base.py              # Конфигурация базы данных
│   ├── models.py            # Модели User и Cookie
│   └── repositories.py      # Репозитории для работы с БД
├── domain/
│   └── auth/
│       ├── auth.py          # Логика авторизации через Selenium
│       ├── auth_service.py  # Бизнес-логика сервиса
│       └── schemas.py       # Pydantic схемы
├── alembic/
│   ├── versions/            # Миграции базы данных
│   └── env.py              # Конфигурация Alembic
├── main.py                  # Главный файл приложения
├── migrate.sh               # Скрипт управления миграциями
├── run.sh                   # Скрипт запуска сервиса
├── requirements.txt         # Зависимости
└── alembic.ini            # Конфигурация миграций
```

## Установка и настройка

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка базы данных

Создайте файл `.env` в корне проекта:

```env
# Database configuration
DB_URL=postgresql+asyncpg://user:password@localhost/wb_auth_db

# Server configuration
PORT=8000

# Logging
LOG_LEVEL=INFO
```

### 3. Создание базы данных

```bash
# Создайте базу данных PostgreSQL
createdb wb_auth_db

# Или используйте Docker
docker run --name wb-postgres -e POSTGRES_PASSWORD=password -e POSTGRES_DB=wb_auth_db -p 5432:5432 -d postgres:13
```

### 4. Управление миграциями через bash

Используйте скрипт `migrate.sh` для управления миграциями:

```bash
# Показать справку
./migrate.sh help

# Инициализировать базу данных (применить все миграции)
./migrate.sh init

# Применить миграции
./migrate.sh apply

# Создать новую миграцию
./migrate.sh create-migration "Add new field to users table"

# Показать историю миграций
./migrate.sh history

# Показать текущее состояние
./migrate.sh current

# Откатить миграции
./migrate.sh rollback 001

# Сбросить базу данных
./migrate.sh reset
```

### 5. Запуск сервиса

#### Быстрый запуск (рекомендуется)

```bash
./run.sh
```

Этот скрипт автоматически:
- Проверит и создаст файл .env если нужно
- Установит зависимости если нужно
- Применит миграции базы данных
- Запустит сервис

#### Ручной запуск

```bash
python main.py
```

Сервис будет доступен по адресу: http://localhost:8000

## API Endpoints

### Авторизация

- `POST /api/v1/auth/request` - Запрос кода авторизации (первый этап)
- `POST /api/v1/auth/confirm` - Подтверждение авторизации (второй этап)
- `POST /api/v1/auth/users` - Создание нового пользователя
- `GET /api/v1/auth/users/{user_id}` - Получение пользователя с куками
- `GET /api/v1/auth/users/{user_id}/cookies` - Получение куки пользователя
- `POST /api/v1/auth/users/{user_id}/refresh` - Обновление куки
- `DELETE /api/v1/auth/users/{user_id}` - Удаление пользователя

### Примеры запросов

#### Создание пользователя

```bash
curl -X POST "http://localhost:8000/api/v1/auth/users" \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test_user_123"}'
```

#### Запрос кода авторизации (первый этап)

```bash
curl -X POST "http://localhost:8000/api/v1/auth/request" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test_user_123",
       "phone": "9991231212"
     }'
```

#### Подтверждение авторизации (второй этап)

```bash
curl -X POST "http://localhost:8000/api/v1/auth/confirm" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test_user_123",
       "phone": "9991231212",
       "verification_code": "123456",
       "session_id": "uuid-from-request-response"
     }'
```

#### Получение куки

```bash
curl -X GET "http://localhost:8000/api/v1/auth/users/test_user_123/cookies"
```

## Модели базы данных

### User

- `id` - Первичный ключ
- `user_id` - ID пользователя в Wildberries (уникальный)
- `created_at` - Дата создания
- `updated_at` - Дата обновления

### Cookie

- `id` - Первичный ключ
- `user_id` - Внешний ключ на User
- `name` - Название куки
- `value` - Значение куки
- `expire_date` - Дата истечения
- `created_at` - Дата создания
- `updated_at` - Дата обновления

## Управление миграциями

### Создание миграции

```bash
# Автоматическое создание миграции на основе изменений в моделях
./migrate.sh create-migration "Описание изменений"

# Пример
./migrate.sh create-migration "Add email field to users table"
```

### Применение миграций

```bash
# Применить все миграции
./migrate.sh apply

# Или инициализировать базу данных (то же самое)
./migrate.sh init
```

### Откат миграций

```bash
# Откатить до конкретной ревизии
./migrate.sh rollback 001

# Откатить все миграции
./migrate.sh rollback base
```

### Просмотр информации

```bash
# История миграций
./migrate.sh history

# Текущее состояние
./migrate.sh current

# Статус миграций
./migrate.sh status
```

## Особенности

1. **Асинхронная работа** - Все операции с базой данных асинхронные
2. **Миграции через Alembic** - Управление схемой базы данных через миграции
3. **Cascade удаление** - При удалении пользователя удаляются все его куки
4. **Валидация данных** - Используются Pydantic схемы для валидации
5. **Обработка ошибок** - Централизованная обработка ошибок
6. **Bash скрипт** - Удобное управление миграциями через командную строку

## Разработка

### Добавление новых эндпоинтов

1. Создайте новые схемы в `domain/auth/schemas.py`
2. Добавьте методы в `domain/auth/auth_service.py`
3. Создайте роуты в `api/routes/auth.py`

### Изменение моделей базы данных

1. Измените модели в `database/models.py`
2. Создайте миграцию: `./migrate.sh create-migration "Описание изменений"`
3. Примените миграцию: `./migrate.sh apply`

### Тестирование

```bash
# Запуск тестов (если есть)
python -m pytest tests/

# Проверка API документации
# Откройте http://localhost:8000/docs
```

## Docker

Для запуска в Docker создайте `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

И `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_URL=postgresql+asyncpg://user:password@db/wb_auth_db
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=wb_auth_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
``` 
