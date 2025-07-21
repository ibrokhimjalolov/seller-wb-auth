#!/bin/bash

# Скрипт для управления миграциями Alembic

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

# Функция для создания новой миграции
create_migration() {
    local message="$1"
    if [ -z "$message" ]; then
        print_error "Необходимо указать сообщение для миграции"
        echo "Использование: $0 create-migration \"Описание миграции\""
        exit 1
    fi
    
    print_message "Создание новой миграции: $message"
    alembic revision --autogenerate -m "$message"
    print_success "Миграция создана"
}

# Функция для применения миграций
apply_migrations() {
    print_message "Применение миграций..."
    create_migration "new"
    alembic upgrade head
    print_success "Миграции применены"
}

# Функция для отката миграций
rollback_migrations() {
    local revision="$1"
    if [ -z "$revision" ]; then
        print_error "Необходимо указать ревизию для отката"
        echo "Использование: $0 rollback <revision>"
        exit 1
    fi
    
    print_message "Откат миграций до ревизии: $revision"
    alembic downgrade "$revision"
    print_success "Миграции откачены"
}

# Функция для просмотра истории миграций
show_history() {
    print_message "История миграций:"
    alembic history
}

# Функция для просмотра текущего состояния
show_current() {
    print_message "Текущее состояние миграций:"
    alembic current
}

# Функция для просмотра статуса миграций
show_status() {
    print_message "Статус миграций:"
    alembic heads
}

# Функция для инициализации базы данных
init_db() {
    print_message "Инициализация базы данных..."
    
    # Проверяем подключение к базе данных
    print_message "Проверка подключения к базе данных..."
    
    # Применяем миграции
    apply_migrations
    
    print_success "База данных инициализирована"
}

# Функция для сброса базы данных
reset_db() {
    print_warning "Это действие удалит все данные из базы данных!"
    read -p "Вы уверены? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_message "Сброс базы данных..."
        alembic downgrade base
        print_success "База данных сброшена"
    else
        print_message "Операция отменена"
    fi
}

# Основная логика
main() {
    check_env
    
    case "$1" in
        "create-migration")
            create_migration "$2"
            ;;
        "apply"|"upgrade")
            apply_migrations
            ;;
        "rollback"|"downgrade")
            rollback_migrations "$2"
            ;;
        "history")
            show_history
            ;;
        "current")
            show_current
            ;;
        "status"|"heads")
            show_status
            ;;
        "init")
            init_db
            ;;
        "reset")
            reset_db
            ;;
        "help"|"--help"|"-h"|"")
            echo "Использование: $0 <команда> [аргументы]"
            echo ""
            echo "Команды:"
            echo "  create-migration <message>  - Создать новую миграцию"
            echo "  apply|upgrade               - Применить все миграции"
            echo "  rollback|downgrade <rev>   - Откатить миграции до ревизии"
            echo "  history                     - Показать историю миграций"
            echo "  current                     - Показать текущую ревизию"
            echo "  status|heads                - Показать статус миграций"
            echo "  init                        - Инициализировать базу данных"
            echo "  reset                       - Сбросить базу данных"
            echo "  help                        - Показать эту справку"
            echo ""
            echo "Примеры:"
            echo "  $0 create-migration \"Add new field to users table\""
            echo "  $0 apply"
            echo "  $0 rollback 001"
            echo "  $0 init"
            ;;
        *)
            print_error "Неизвестная команда: $1"
            echo "Используйте '$0 help' для получения справки"
            exit 1
            ;;
    esac
}

# Запуск основной функции
main "$@"
