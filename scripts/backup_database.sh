#!/bin/bash

# Автоматическое резервное копирование PostgreSQL для Matrix Blog
# Использование: ./backup_database.sh [backup_type]

set -e

# Конфигурация
BACKUP_DIR="/backups"
DB_HOST="db"
DB_NAME="${DB_NAME:-myblog}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD}"
RETENTION_DAYS=30
S3_BUCKET="${S3_BACKUP_BUCKET:-}"
S3_PREFIX="${S3_BACKUP_PREFIX:-}"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Проверка переменных окружения
if [ -z "$DB_PASSWORD" ]; then
    echo -e "${RED}❌ Переменная DB_PASSWORD не установлена${NC}"
    exit 1
fi

# Создание директории для бэкапов
mkdir -p "$BACKUP_DIR"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Функция проверки доступности БД
check_db() {
    log "Проверка доступности базы данных..."
    if ! pg_isready -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t 10; then
        log "ERROR: База данных недоступна"
        return 1
    fi
    log "✓ База данных доступна"
    return 0
}

# Функция создания бэкапа
create_backup() {
    local backup_type=${1:-"daily"}
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$BACKUP_DIR/${DB_NAME}_${backup_type}_${timestamp}.sql.gz"
    
    log "Начинаю создание $backup_type бэкапа..."
    
    # Создание бэкапа с сжатием
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --clean \
        --if-exists \
        --create \
        --format=custom \
        --compress=6 \
        --file="$backup_file.custom"
    
    # Создание дополнительного SQL файла
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --clean \
        --if-exists \
        --create \
        --format=plain \
        --compress=6 \
        --file="$backup_file"
    
    # Проверка размера файла
    if [ -f "$backup_file" ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        log "✓ Бэкап создан: $backup_file ($size)"
        
        # Создание MD5 хеша
        md5sum "$backup_file" > "${backup_file}.md5"
        log "✓ MD5 хеш создан"
        
        return 0
    else
        log "ERROR: Файл бэкапа не создан"
        return 1
    fi
}

# Функция загрузки в S3 (если настроено)
upload_to_s3() {
    if [ -n "$S3_BUCKET" ] && command -v aws >/dev/null 2>&1; then
        log "Загружаю бэкап в S3..."
        
        local backup_file="$1"
        local s3_key="$S3_PREFIX$(basename "$backup_file")"
        
        if aws s3 cp "$backup_file" "s3://$S3_BUCKET/$s3_key" \
            --storage-class STANDARD_IA \
            --metadata "backup_type=database,created=$(date -Iseconds),database=$DB_NAME"; then
            log "✓ Бэкап загружен в S3: s3://$S3_BUCKET/$s3_key"
        else
            log "ERROR: Ошибка загрузки в S3"
        fi
    fi
}

# Функция очистки старых бэкапов
cleanup_old_backups() {
    log "Очистка старых бэкапов (старше $RETENTION_DAYS дней)..."
    
    # Удаление локальных файлов
    find "$BACKUP_DIR" -name "${DB_NAME}_*.sql*" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "${DB_NAME}_*.custom" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "${DB_NAME}_*.md5" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    log "✓ Локальные старые бэкапы очищены"
    
    # Очистка S3 (если настроено)
    if [ -n "$S3_BUCKET" ] && command -v aws >/dev/null 2>&1; then
        log "Очистка старых бэкапов в S3..."
        aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX" --recursive | \
            awk '{print $4}' | \
            xargs -I {} aws s3api head-object --bucket "$S3_BUCKET" --key {} --query 'Metadata.backup_type' --output text 2>/dev/null | \
            grep database || true
        
        # Удаление старых файлов в S3
        cutoff_date=$(date -d "$RETENTION_DAYS days ago" -I)
        aws s3api list-objects-v2 \
            --bucket "$S3_BUCKET" \
            --prefix "$S3_PREFIX" \
            --query "Contents[?LastModified<='$cutoff_date'].Key" \
            --output text | \
            tr '\t' '\n' | \
            grep "${DB_NAME}_" | \
            xargs -I {} aws s3 rm "s3://$S3_BUCKET/{}" 2>/dev/null || true
    fi
}

# Функция восстановления из бэкапа
restore_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        log "ERROR: Файл бэкапа не найден: $backup_file"
        exit 1
    fi
    
    log "Начинаю восстановление из бэкапа: $backup_file"
    
    # Проверка MD5
    if [ -f "${backup_file}.md5" ]; then
        if md5sum -c "${backup_file}.md5" >/dev/null 2>&1; then
            log "✓ MD5 хеш проверен"
        else
            log "ERROR: MD5 хеш не совпадает"
            exit 1
        fi
    fi
    
    # Остановка приложений
    log "Остановка приложений..."
    docker-compose exec web python manage.py shell -c "from django.core.management import call_command; call_command('celery_control', 'stop')" 2>/dev/null || true
    
    # Восстановление из custom формата
    if [[ "$backup_file" == *.custom ]]; then
        log "Восстановление из custom формата..."
        PGPASSWORD="$DB_PASSWORD" pg_restore \
            -h "$DB_HOST" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --clean \
            --if-exists \
            --verbose \
            "$backup_file"
    else
        log "Восстановление из SQL формата..."
        gunzip -c "$backup_file" | \
            PGPASSWORD="$DB_PASSWORD" psql \
            -h "$DB_HOST" \
            -U "$DB_USER" \
            -d postgres
    fi
    
    log "✓ Восстановление завершено"
}

# Функция проверки целостности бэкапа
verify_backup() {
    local backup_file="$1"
    
    if [[ "$backup_file" == *.custom ]]; then
        log "Проверка целостности custom бэкапа..."
        PGPASSWORD="$DB_PASSWORD" pg_restore \
            -l "$backup_file" > /dev/null
    else
        log "Проверка целостности SQL бэкапа..."
        gunzip -t "$backup_file" > /dev/null
    fi
    
    if [ $? -eq 0 ]; then
        log "✓ Бэкап целостный"
        return 0
    else
        log "ERROR: Бэкап поврежден"
        return 1
    fi
}

# Функция создания статистики
create_stats() {
    local db_size=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" | xargs)
    local tables_count=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" | xargs)
    
    log "📊 Статистика базы данных:"
    log "   Размер: $db_size"
    log "   Таблиц: $tables_count"
    log "   Подключений: $(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM pg_stat_activity;" | xargs)"
    
    # Сохранение статистики
    echo "$(date '+%Y-%m-%d %H:%M:%S') | Size: $db_size | Tables: $tables_count" >> "$BACKUP_DIR/stats.log"
}

# Основная логика
main() {
    local action="${1:-"backup"}"
    local backup_type="${2:-"manual"}"
    
    log "🚀 Начало операции: $action"
    
    case "$action" in
        "backup")
            if check_db; then
                create_backup "$backup_type" && \
                cleanup_old_backups && \
                create_stats
            fi
            ;;
        "restore")
            restore_backup "$2"
            ;;
        "verify")
            verify_backup "$2"
            ;;
        "stats")
            create_stats
            ;;
        *)
            echo "Использование: $0 [backup|restore|verify|stats] [параметр]"
            echo "  backup [daily|weekly|monthly] - создать бэкап"
            echo "  restore <файл>               - восстановить из бэкапа"
            echo "  verify <файл>                - проверить целостность бэкапа"
            echo "  stats                        - показать статистику БД"
            exit 1
            ;;
    esac
    
    log "✅ Операция завершена"
}

# Запуск основной функции
main "$@"