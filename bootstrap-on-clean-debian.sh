#!/usr/bin/env bash
set -euo pipefail

#######################################
#  НАСТРОЙКИ — РЕДАКТИРУЙ ЗДЕСЬ
#######################################

# Если пусто — возьмём первый кластер из pg_lsclusters
PG_VERSION=""

PG_DB_NAME="mydb"
PG_USER="myuser"
PG_PASSWORD="my_pg_password"        # без одинарных кавычек внутри

REDIS_PASSWORD="my_redis_password"  # без одинарных кавычек внутри

#######################################
#  ДАЛЬШЕ ЛУЧШЕ НЕ ТРОГАТЬ :)
#######################################

if [[ "$EUID" -ne 0 ]]; then
  echo "Этот скрипт нужно запускать от root (или через: sudo $0)"
  exit 1
fi

echo ">>> Обновление пакетов..."
apt-get update -y

echo ">>> Установка PostgreSQL и Redis..."
if [[ -n "$PG_VERSION" ]]; then
  apt-get install -y "postgresql-$PG_VERSION" "postgresql-client-$PG_VERSION" redis-server
else
  apt-get install -y postgresql postgresql-client redis-server
fi

if ! command -v pg_lsclusters >/dev/null 2>&1; then
  echo "Не найден pg_lsclusters — похоже, это не Debian/Ubuntu-пакет postgresql. Такой сценарий скрипт не поддерживает."
  exit 1
fi

echo ">>> Определение кластера PostgreSQL через pg_lsclusters..."

# Формат строки: Версия  Кластер  Порт  Статус  Владелец  DataDir  Logfile
if [[ -n "$PG_VERSION" ]]; then
  # Ищем строку нужной версии
  CLUSTER_LINE="$(pg_lsclusters --no-header | awk -v ver="$PG_VERSION" '$1 == ver {print; exit}')"
else
  # Берём первый кластер
  CLUSTER_LINE="$(pg_lsclusters --no-header | head -n1)"
fi

if [[ -z "$CLUSTER_LINE" ]]; then
  echo "Не удалось найти кластер PostgreSQL (pg_lsclusters ничего не вернул)."
  exit 1
fi

read -r PG_VERSION PG_CLUSTER PG_PORT PG_STATUS PG_OWNER PG_DATA_DIR PG_LOGFILE <<<"$CLUSTER_LINE"

echo "    Версия:   $PG_VERSION"
echo "    Кластер:  $PG_CLUSTER"
echo "    Порт:     $PG_PORT"
echo "    Владелец: $PG_OWNER"
echo "    DataDir:  $PG_DATA_DIR"
echo "    Logfile:  $PG_LOGFILE"

PG_CONF="/etc/postgresql/${PG_VERSION}/${PG_CLUSTER}/postgresql.conf"
PG_HBA="/etc/postgresql/${PG_VERSION}/${PG_CLUSTER}/pg_hba.conf"

if [[ ! -f "$PG_CONF" || ! -f "$PG_HBA" ]]; then
  echo "Не найдены конфиги $PG_CONF или $PG_HBA. Проверь установку PostgreSQL."
  exit 1
fi

#######################################
# Хелпер для запуска команд от postgres
#######################################
as_postgres() {
  if [[ "$(id -un)" == "postgres" ]]; then
    "$@"
    return
  fi

  if [[ "$(id -u)" -eq 0 ]]; then
    local cmd=""
    printf -v cmd '%q ' "$@"
    su - postgres -s /bin/bash -c "$cmd"
    return
  fi

  echo "Нужно запустить эту команду от root или postgres" >&2
  return 1
}

#######################################
# Настройка доступа к PostgreSQL
#######################################

echo ">>> Настройка PostgreSQL-конфигов..."

# Разрешаем TCP-доступ с паролем
if ! grep -q "0.0.0.0/0" "$PG_HBA"; then
  echo "host    all             all             0.0.0.0/0               md5" >> "$PG_HBA"
fi

# Слушать на всех интерфейсах (можно заменить на 'localhost')
sed -ri "s/^(#?\s*listen_addresses\s*=\s*).*/\1'*'/" "$PG_CONF"

#######################################
# Перезапуск PostgreSQL через pg_ctlcluster
#######################################

if ! command -v pg_ctlcluster >/dev/null 2>&1; then
  echo "Не найден pg_ctlcluster, не могу управлять кластером стандартным способом."
  exit 1
fi

echo ">>> Перезапуск кластера PostgreSQL через pg_ctlcluster..."
pg_ctlcluster "$PG_VERSION" "$PG_CLUSTER" restart

echo ">>> Проверка, что PostgreSQL живой..."
as_postgres psql -tAc "SELECT version();" >/dev/null

#######################################
# Создание пользователя и базы
#######################################

echo ">>> Создание пользователя и базы в PostgreSQL..."

if ! as_postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${PG_USER}'" | grep -q 1; then
  as_postgres psql -c "CREATE ROLE ${PG_USER} LOGIN PASSWORD '${PG_PASSWORD}';"
fi

if ! as_postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${PG_DB_NAME}'" | grep -q 1; then
  as_postgres createdb -O "${PG_USER}" "${PG_DB_DB_NAME:-$PG_DB_NAME}" 2>/dev/null || \
  as_postgres createdb -O "${PG_USER}" "${PG_DB_NAME}"
fi

# (опционально) сменить пароль суперюзера postgres:
# as_postgres psql -c "ALTER USER postgres WITH PASSWORD '${PG_PASSWORD}';"

#######################################
# Настройка Redis
#######################################

echo ">>> Настройка Redis..."

REDIS_CONF="/etc/redis/redis.conf"

if [[ ! -f "$REDIS_CONF" ]]; then
  echo "Не найден $REDIS_CONF. Проверь установку Redis."
  exit 1
fi

# Пароль
if grep -qE '^\s*#?\s*requirepass' "$REDIS_CONF"; then
  sed -ri "s/^\s*#?\s*requirepass.*/requirepass ${REDIS_PASSWORD}/" "$REDIS_CONF"
else
  echo "requirepass ${REDIS_PASSWORD}" >> "$REDIS_CONF"
fi

# Слушать на всех интерфейсах (если нужно только localhost — измени bind)
if grep -qE '^\s*bind ' "$REDIS_CONF"; then
  sed -ri "s/^\s*bind .*/bind 0.0.0.0 ::1/" "$REDIS_CONF"
else
  echo "bind 0.0.0.0 ::1" >> "$REDIS_CONF"
fi

#######################################
# Запуск Redis (без systemd)
#######################################

echo ">>> Запуск Redis напрямую (без systemd)..."

if command -v redis-cli >/dev/null 2>&1; then
  redis-cli -a "$REDIS_PASSWORD" shutdown >/dev/null 2>&1 || true
  redis-cli shutdown >/dev/null 2>&1 || true
fi

redis-server "$REDIS_CONF" --daemonize yes

echo
echo "====================================="
echo " PostgreSQL и Redis установлены и настроены."
echo "-------------------------------------"
echo "PostgreSQL:"
echo "  Версия:       ${PG_VERSION}"
echo "  Кластер:      ${PG_CLUSTER}"
echo "  Порт:         ${PG_PORT}"
echo "  DataDir:      ${PG_DATA_DIR}"
echo "  Logfile:      ${PG_LOGFILE}"
echo "  База:         ${PG_DB_NAME}"
echo "  Пользователь: ${PG_USER}"
echo "  Пароль:       ${PG_PASSWORD}"
echo
echo "Redis:"
echo "  Конфиг:       ${REDIS_CONF}"
echo "  Пароль:       ${REDIS_PASSWORD}"
echo "  Порт:         6379"
echo
echo "Примеры подключения:"
echo "  PostgreSQL: psql -h 127.0.0.1 -p ${PG_PORT} -U ${PG_USER} -d ${PG_DB_NAME}"
echo "  Redis:      redis-cli -h 127.0.0.1 -p 6379 -a ${REDIS_PASSWORD}"
echo "====================================="
echo "Готово."
