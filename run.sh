#!/bin/bash

# Скрипт для запуска Wildberries Auth Service

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка наличия .env файла
check_env() {
    if [ ! -f .env ]; then
        print_warning "Файл .env не найден. Создаю из примера..."
        if [ -f config_example.env ]; then
            cp config_example.env .env
            print_success "Файл .env создан из config_example.env"
            print_warning "Пожалуйста, отредактируйте .env с вашими настройками базы данных"
        else
            print_error "Файл config_example.env не найден"
            exit 1
        fi
    fi
}

# Проверка зависимостей
check_dependencies() {
    print_message "Проверка зависимостей..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 не найден"
        exit 1
    fi
    
    if ! python3 -c "import fastapi" &> /dev/null; then
        print_warning "Зависимости не установлены. Устанавливаю..."
        pip install -r requirements.txt
    fi
    
    print_success "Зависимости проверены"
}

# Проверка базы данных
check_database() {
    print_message "Проверка базы данных..."
    
    # Проверяем, есть ли миграции
    if [ -d "alembic/versions" ] && [ "$(ls -A alembic/versions)" ]; then
        print_message "Найдены миграции. Применяю..."
        ./migrate.sh apply
    else
        print_warning "Миграции не найдены. Создаю начальную миграцию..."
        ./migrate.sh init
    fi
    
    print_success "База данных готова"
}

# Запуск сервиса
start_service() {
    print_message "Запуск Wildberries Auth Service..."
    
    # Получаем порт из переменных окружения
    PORT=${PORT:-8000}
    
    print_success "Сервис запущен на http://localhost:$PORT"
    print_message "API документация: http://localhost:$PORT/docs"
    print_message "Для остановки нажмите Ctrl+C"
    
    # Запускаем сервис
    python3 main.py
}

# Основная функция
main() {
    print_message "Запуск Wildberries Auth Service..."
    echo ""
    
    check_env
    check_dependencies
    check_database
    echo ""
    start_service
}

# Обработка сигналов
trap 'print_message "Сервис остановлен"; exit 0' INT TERM

# Запуск основной функции
main "$@" 
