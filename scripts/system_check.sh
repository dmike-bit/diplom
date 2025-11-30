#!/bin/bash

# Комплексная проверка системы Matrix Blog для продакшена
# Использование: ./scripts/system_check.sh [check_type]

set -e

# Конфигурация
DOMAIN="82.202.141.206"
SITE_URL="https://$DOMAIN"
ADMIN_URL="$SITE_URL/admin/"
API_URL="$SITE_URL/api/"
HEALTH_URL="$SITE_URL/health/"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Счетчики
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_TOTAL=0

# Функции логирования
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((CHECKS_PASSED++))
    ((CHECKS_TOTAL++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((CHECKS_TOTAL++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((CHECKS_FAILED++))
    ((CHECKS_TOTAL++))
}

log_header() {
    echo ""
    echo -e "${BLUE}══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════${NC}"
}

# Функция проверки HTTP ответа
check_http() {
    local url="$1"
    local description="$2"
    local expected_status="${3:-200}"
    
    log_info "Проверка: $description"
    log_info "URL: $url"
    
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 10 --insecure)
    
    if [ "$status_code" = "$expected_status" ]; then
        log_success "HTTP $status_code - $description"
    else
        log_error "HTTP $status_code (ожидался $expected_status) - $description"
    fi
}

# Функция проверки контейнеров Docker
check_docker_containers() {
    log_header "ПРОВЕРКА DOCKER КОНТЕЙНЕРОВ"
    
    local containers=("myblog_web" "myblog_nginx" "myblog_db" "myblog_redis" "myblog_celery")
    
    for container in "${containers[@]}"; do
        if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
            log_success "Контейнер $container запущен и работает"
        else
            log_error "Контейнер $container не запущен или не работает"
        fi
    done
}

# Функция проверки портов
check_ports() {
    log_header "ПРОВЕРКА ПОРТОВ"
    
    local ports=("80" "443" "8000" "5432" "6379")
    
    for port in "${ports[@]}"; do
        if netstat -tuln | grep -q ":$port "; then
            log_success "Порт $port открыт и слушается"
        else
            log_error "Порт $port не открыт или не слушается"
        fi
    done
}

# Функция проверки SSL сертификата
check_ssl() {
    log_header "ПРОВЕРКА SSL СЕРТИФИКАТОВ"
    
    log_info "Проверка SSL сертификата для $DOMAIN"
    
    # Проверка истечения сертификата
    local cert_end=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN":443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
    local cert_end_timestamp=$(date -d "$cert_end" +%s)
    local current_timestamp=$(date +%s)
    local days_left=$(( (cert_end_timestamp - current_timestamp) / 86400 ))
    
    if [ $days_left -gt 30 ]; then
        log_success "SSL сертификат действителен еще $days_left дней"
    elif [ $days_left -gt 7 ]; then
        log_warning "SSL сертификат истекает через $days_left дней"
    else
        log_error "SSL сертификат истекает через $days_left дней - требуется срочное обновление!"
    fi
    
    # Проверка качества SSL
    log_info "Проверка качества SSL конфигурации"
    local ssl_grade=$(curl -s "https://api.ssllabs.com/api/v3/analyze?host=$DOMAIN&publish=off" | jq -r '.endpoints[0].grade' 2>/dev/null || echo "Unknown")
    
    if [ "$ssl_grade" = "A" ] || [ "$ssl_grade" = "A+" ]; then
        log_success "SSL рейтинг: $ssl_grade"
    else
        log_warning "SSL рейтинг: $ssl_grade (рекомендуется A или выше)"
    fi
}

# Функция проверки HTTP endpoints
check_endpoints() {
    log_header "ПРОВЕРКА HTTP ENDPOINTS"
    
    check_http "$SITE_URL" "Главная страница"
    check_http "$ADMIN_URL" "Админ-панель"
    check_http "$API_URL" "API"
    check_http "$HEALTH_URL" "Health check"
    check_http "$SITE_URL/blog/" "Страница блога"
}

# Функция проверки производительности
check_performance() {
    log_header "ПРОВЕРКА ПРОИЗВОДИТЕЛЬНОСТИ"
    
    log_info "Измерение времени отклика главной страницы"
    local response_time=$(curl -o /dev/null -s -w "%{time_total}" "$SITE_URL" --max-time 10 --insecure)
    
    # Конвертация в секунды
    if (( $(echo "$response_time < 1.0" | bc -l) )); then
        log_success "Время отклика: ${response_time}s (отличное)"
    elif (( $(echo "$response_time < 2.0" | bc -l) )); then
        log_success "Время отклика: ${response_time}s (хорошее)"
    elif (( $(echo "$response_time < 5.0" | bc -l) )); then
        log_warning "Время отклика: ${response_time}s (приемлемое)"
    else
        log_error "Время отклика: ${response_time}s (медленно)"
    fi
    
    # Проверка размера страницы
    local page_size=$(curl -s "$SITE_URL" --max-time 10 --insecure | wc -c)
    if [ $page_size -lt 100000 ]; then
        log_success "Размер страницы: $page_size байт (оптимальный)"
    elif [ $page_size -lt 500000 ]; then
        log_warning "Размер страницы: $page_size байт (большой)"
    else
        log_error "Размер страницы: $page_size байт (слишком большой)"
    fi
}

# Функция проверки базы данных
check_database() {
    log_header "ПРОВЕРКА БАЗЫ ДАННЫХ"
    
    log_info "Проверка подключения к PostgreSQL"
    if docker-compose exec -T db psql -U postgres -d myblog -c "SELECT 1;" | grep -q "1"; then
        log_success "Подключение к PostgreSQL успешно"
    else
        log_error "Ошибка подключения к PostgreSQL"
    fi
    
    # Проверка таблиц
    local tables_count=$(docker-compose exec -T db psql -U postgres -d myblog -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" | xargs)
    if [ "$tables_count" -gt 0 ]; then
        log_success "Найдено таблиц в БД: $tables_count"
    else
        log_error "В базе данных нет таблиц"
    fi
    
    # Проверка размера БД
    local db_size=$(docker-compose exec -T db psql -U postgres -d myblog -t -c "SELECT pg_size_pretty(pg_database_size('myblog'));" | xargs)
    log_info "Размер базы данных: $db_size"
}

# Функция проверки Redis
check_redis() {
    log_header "ПРОВЕРКА REDIS"
    
    log_info "Проверка подключения к Redis"
    if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
        log_success "Подключение к Redis успешно"
    else
        log_error "Ошибка подключения к Redis"
    fi
    
    # Проверка информации о Redis
    local redis_info=$(docker-compose exec -T redis redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
    log_info "Использование памяти Redis: $redis_info"
}

# Функция проверки логов
check_logs() {
    log_header "ПРОВЕРКА ЛОГОВ"
    
    # Проверка наличия лог файлов
    local log_dirs=("logs" "logs/nginx" "logs/django")
    
    for dir in "${log_dirs[@]}"; do
        if [ -d "$dir" ] && [ "$(ls -A $dir 2>/dev/null)" ]; then
            log_success "Директория логов $dir содержит файлы"
        else
            log_warning "Директория логов $dir пуста или не существует"
        fi
    done
    
    # Проверка последних ошибок в логах
    if [ -f "logs/django.log" ]; then
        local error_count=$(tail -n 100 logs/django.log | grep -i error | wc -l)
        if [ $error_count -eq 0 ]; then
            log_success "В логах Django нет ошибок"
        else
            log_warning "В логах Django найдено $error_count ошибок"
        fi
    fi
}

# Функция проверки безопасности
check_security() {
    log_header "ПРОВЕРКА БЕЗОПАСНОСТИ"
    
    # Проверка заголовков безопасности
    local headers=$(curl -s -I "$SITE_URL" --insecure | head -20)
    
    if echo "$headers" | grep -qi "strict-transport-security"; then
        log_success "HSTS заголовок присутствует"
    else
        log_error "HSTS заголовок отсутствует"
    fi
    
    if echo "$headers" | grep -qi "x-frame-options"; then
        log_success "X-Frame-Options заголовок присутствует"
    else
        log_warning "X-Frame-Options заголовок отсутствует"
    fi
    
    if echo "$headers" | grep -qi "x-content-type-options"; then
        log_success "X-Content-Type-Options заголовок присутствует"
    else
        log_warning "X-Content-Type-Options заголовок отсутствует"
    fi
    
    if echo "$headers" | grep -qi "x-xss-protection"; then
        log_success "X-XSS-Protection заголовок присутствует"
    else
        log_warning "X-XSS-Protection заголовок отсутствует"
    fi
}

# Функция проверки мониторинга
check_monitoring() {
    log_header "ПРОВЕРКА МОНИТОРИНГА"
    
    # Проверка Prometheus
    if curl -s http://localhost:9090/api/v1/query?query=up | jq -e '.status == "success"' >/dev/null 2>&1; then
        log_success "Prometheus доступен и отвечает"
    else
        log_error "Prometheus недоступен или не отвечает"
    fi
    
    # Проверка Grafana
    if curl -s http://localhost:3000/api/health | jq -e '.database == "ok"' >/dev/null 2>&1; then
        log_success "Grafana доступен и работает"
    else
        log_warning "Grafana недоступен или не работает"
    fi
}

# Функция проверки резервного копирования
check_backup() {
    log_header "ПРОВЕРКА РЕЗЕРВНОГО КОПИРОВАНИЯ"
    
    # Проверка наличия скрипта бэкапа
    if [ -f "scripts/backup_database.sh" ] && [ -x "scripts/backup_database.sh" ]; then
        log_success "Скрипт резервного копирования найден и исполним"
    else
        log_error "Скрипт резервного копирования не найден или не исполним"
    fi
    
    # Проверка директории бэкапов
    if [ -d "backups" ]; then
        local backup_count=$(ls -1 backups/*.sql* 2>/dev/null | wc -l)
        log_info "Найдено файлов резервного копирования: $backup_count"
        if [ $backup_count -gt 0 ]; then
            log_success "Обнаружены файлы резервного копирования"
        else
            log_warning "Файлы резервного копирования не найдены"
        fi
    else
        log_error "Директория резервного копирования не существует"
    fi
}

# Функция генерации отчета
generate_report() {
    log_header "ОТЧЕТ О ПРОВЕРКЕ СИСТЕМЫ"
    
    local pass_rate=0
    if [ $CHECKS_TOTAL -gt 0 ]; then
        pass_rate=$((CHECKS_PASSED * 100 / CHECKS_TOTAL))
    fi
    
    echo -e "Общее количество проверок: ${BLUE}$CHECKS_TOTAL${NC}"
    echo -e "Пройдено успешно: ${GREEN}$CHECKS_PASSED${NC}"
    echo -e "Не пройдено: ${RED}$CHECKS_FAILED${NC}"
    echo -e "Процент успешных проверок: ${BLUE}$pass_rate%${NC}"
    
    # Статус системы
    echo ""
    if [ $CHECKS_FAILED -eq 0 ]; then
        echo -e "${GREEN}🎉 СИСТЕМА РАБОТАЕТ КОРРЕКТНО! 🎉${NC}"
    elif [ $CHECKS_FAILED -le 3 ]; then
        echo -e "${YELLOW}⚠️ СИСТЕМА РАБОТАЕТ С НЕБОЛЬШИМИ ПРОБЛЕМАМИ ⚠️${NC}"
    else
        echo -e "${RED}🚨 СИСТЕМА ИМЕЕТ СЕРЬЕЗНЫЕ ПРОБЛЕМЫ! 🚨${NC}"
    fi
    
    # Сохранение отчета
    local report_file="reports/system_check_$(date +%Y%m%d_%H%M%S).txt"
    mkdir -p reports
    {
        echo "Отчет о проверке системы Matrix Blog"
        echo "Дата: $(date)"
        echo "Домен: $DOMAIN"
        echo ""
        echo "Результаты:"
        echo "Общее количество проверок: $CHECKS_TOTAL"
        echo "Пройдено успешно: $CHECKS_PASSED"
        echo "Не пройдено: $CHECKS_FAILED"
        echo "Процент успешных проверок: $pass_rate%"
    } > "$report_file"
    
    log_info "Отчет сохранен в файл: $report_file"
}

# Основная логика
main() {
    local check_type="${1:-all}"
    
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════╗"
    echo "║     MATRIX BLOG - ПРОВЕРКА СИСТЕМЫ              ║"
    echo "║              ПРОДАКШН ЭНВИРОНМЕНТ               ║"
    echo "╚══════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    log_info "Начало проверки системы для домена: $DOMAIN"
    log_info "URL: $SITE_URL"
    log_info "Время начала: $(date)"
    
    case "$check_type" in
        "containers")
            check_docker_containers
            ;;
        "endpoints")
            check_endpoints
            ;;
        "security")
            check_security
            ;;
        "performance")
            check_performance
            ;;
        "database")
            check_database
            ;;
        "redis")
            check_redis
            ;;
        "logs")
            check_logs
            ;;
        "backup")
            check_backup
            ;;
        "monitoring")
            check_monitoring
            ;;
        "ssl")
            check_ssl
            ;;
        "ports")
            check_ports
            ;;
        "all")
            check_docker_containers
            check_ports
            check_ssl
            check_endpoints
            check_performance
            check_database
            check_redis
            check_logs
            check_security
            check_monitoring
            check_backup
            ;;
        *)
            echo "Использование: $0 [containers|endpoints|security|performance|database|redis|logs|backup|monitoring|ssl|ports|all]"
            exit 1
            ;;
    esac
    
    generate_report
}

# Запуск основной функции
main "$@"