#!/usr/bin/env bash
set -euo pipefail

#######################################
#  НАСТРОЙКИ ДЛЯ POSTGRES
#######################################

PG_VERSION=""          # если пусто — возьмём первую версию из pg_lsclusters

PG_DB_NAME="hack"
PG_USER="hack"
PG_PASSWORD="changeme"

#######################################
#  ПУТИ
#######################################

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"

PY_DIR="${ROOT_DIR}/python"
MAKEFILE_PATH="${ROOT_DIR}/Makefile"
ENV_PATH="${PY_DIR}/.env"

# sudo-обёртка
if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
else
  SUDO=""
fi

#######################################
# ХЕЛПЕР: выполнение от postgres
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
  echo "Нужно быть root или postgres" >&2
  return 1
}

#######################################
# 1. СИСТЕМНЫЕ ПАКЕТЫ
#######################################

echo ">>> Установка зависимостей через apt-get..."
$SUDO apt-get update -y
# python3 python3-venv python3-pip \
$SUDO apt-get install -y \
  make \
  build-essential libpq-dev \
  postgresql postgresql-client \
  redis-server \
  netcat-traditional dnsutils

#######################################
# 2. POSTGRESQL
#######################################

echo ">>> Определяем кластер PostgreSQL..."

if [[ -n "$PG_VERSION" ]]; then
  CLUSTER_LINE="$(pg_lsclusters --no-header | awk -v ver="$PG_VERSION" '$1==ver {print; exit}')"
else
  CLUSTER_LINE="$(pg_lsclusters --no-header | head -n1)"
fi

if [[ -z "$CLUSTER_LINE" ]]; then
  echo "pg_lsclusters не вернул ни одного кластера."
  exit 1
fi

read -r PG_VERSION_REAL PG_CLUSTER PG_PORT_REAL PG_STATUS PG_OWNER PG_DATA_DIR PG_LOGFILE <<<"$CLUSTER_LINE"

PG_VERSION="${PG_VERSION:-$PG_VERSION_REAL}"
PG_PORT="${PG_PORT_REAL}"

PG_CONF="/etc/postgresql/${PG_VERSION}/${PG_CLUSTER}/postgresql.conf"
PG_HBA="/etc/postgresql/${PG_VERSION}/${PG_CLUSTER}/pg_hba.conf"

echo "    Версия:   $PG_VERSION"
echo "    Кластер:  $PG_CLUSTER"
echo "    Порт:     $PG_PORT"
echo "    DataDir:  $PG_DATA_DIR"

echo ">>> Настраиваем postgresql.conf и pg_hba.conf..."

if ! grep -q "0.0.0.0/0" "$PG_HBA"; then
  echo "host    all             all             0.0.0.0/0               md5" >> "$PG_HBA"
fi

# Слушаем на всех интерфейсах (внутри контейнера это ок)
sed -ri "s/^(#?\s*listen_addresses\s*=\s*).*/\1'*'/" "$PG_CONF"

echo ">>> Перезапуск PostgreSQL..."
$SUDO pg_ctlcluster "$PG_VERSION" "$PG_CLUSTER" restart

echo ">>> Проверка подключения..."
as_postgres psql -tAc "SELECT version();" >/dev/null

echo ">>> Создаём пользователя и БД..."

if ! as_postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${PG_USER}'" | grep -q 1; then
  as_postgres psql -c "CREATE ROLE ${PG_USER} LOGIN PASSWORD '${PG_PASSWORD}';"
fi

if ! as_postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${PG_DB_NAME}'" | grep -q 1; then
  as_postgres createdb -O "${PG_USER}" "${PG_DB_NAME}"
fi

#######################################
# 3. REDIS
#######################################

echo ">>> Запуск Redis..."
redis-cli shutdown >/dev/null 2>&1 || true
redis-server --daemonize yes

#######################################
# 4. PYTHON venv + POETRY
#######################################

if [[ ! -d "$PY_DIR" ]]; then
  echo "Каталог python/ не найден в корне ($ROOT_DIR)!"
  exit 1
fi

echo ">>> Настраиваем виртуальное окружение Python..."

cd "$PY_DIR"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

pip install --upgrade pip
pip install poetry

echo ">>> poetry install..."
poetry install --no-root --compile
poetry install --only-root --compile

deactivate
cd "$ROOT_DIR"

#######################################
# 6. СОЗДАЁМ python/.env
#######################################

echo ">>> Создаём python/.env ..."

cat > "$ENV_PATH" <<EOF
HACK__POSTGRES__HOST=postgres
HACK__POSTGRES__PORT=${PG_PORT}
HACK__POSTGRES__USER=${PG_USER}
HACK__POSTGRES__PASSWORD=${PG_PASSWORD}
HACK__POSTGRES__DATABASE=${PG_DB_NAME}

HACK__REDIS__HOST=redis
HACK__REDIS__PORT=6379
HACK__REDIS__DB=0
HACK__REDIS__USERNAME=default
HACK__REDIS__SSL=false
HACK__REDIS__DECODE_RESPONSES=true
EOF

echo ">>> Создан python/.env:"
cat "$ENV_PATH"

#######################################
# 7. ПЕРЕЗАПИСЫВАЕМ Makefile ТОЛЬКО ЛОКАЛЬНЫМИ ТАРГЕТАМИ
#######################################

echo ">>> Перезаписываю Makefile только локальными целями..."

cat > "$MAKEFILE_PATH" <<'EOF'
# Локальные цели (без docker), с теми же именами, что и докерные

alembic:
	cd python && . .venv/bin/activate && alembic $(command)

run-migrations:
	make alembic command="upgrade head"

generate-migrations:
	make alembic command="revision -m '$(m) $(msg) $(message)' --autogenerate"

up:
	./bare-debian-scripts/run-rest-server.sh start
	make run-migrations

test:
	cd python && . .venv/bin/activate && pytest $(args)

update:
	git pull && make up && make test

logs:
	tail -f rest-server.log || echo "rest-server.log ещё не создан"

down:
	./bare-debian-scripts/run-rest-server.sh stop || true
EOF

#######################################
# 8. ИТОГ
#######################################

echo
echo "====================================="
echo "  bootstrap.sh завершён"
echo "-------------------------------------"
echo "PostgreSQL:"
echo "  База:         ${PG_DB_NAME}"
echo "  Пользователь: ${PG_USER}"
echo "  Пароль:       ${PG_PASSWORD}"
echo "  Порт:         ${PG_PORT}"
echo
echo "Redis:"
echo "  Host:         redis (127.0.0.1)"
echo "  Порт:         6379"
echo
echo "Python:"
echo "  Venv:         python/.venv"
echo "  Env:          python/.env"
echo
echo "Makefile:"
echo "  Цели: alembic, run-migrations, generate-migrations, up, test, update, logs, down"
echo "====================================="
