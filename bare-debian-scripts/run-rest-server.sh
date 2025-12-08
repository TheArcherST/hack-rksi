#!/usr/bin/env bash
set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
PY_DIR="$ROOT_DIR/python"
ENV_FILE="$PY_DIR/.env"
PID_FILE="$PY_DIR/.rest-server.pid"
LOG_FILE="$ROOT_DIR/rest-server.log"

GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
RESET="\033[0m"

log_ok()   { echo -e "${GREEN}OK${RESET}   $1"; }
log_err()  { echo -e "${RED}ERR${RESET}  $1"; }
log_info() { echo -e "${YELLOW}INFO${RESET} $1"; }

# sudo-обёртка
if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
else
  SUDO=""
fi

env_get() {
  local key="$1"
  if [[ -f "$ENV_FILE" ]]; then
    awk -F'=' -v k="$key" '
      $1 == k {
        sub(/^[ \t]+/, "", $2);
        sub(/[ \t\r\n]+$/, "", $2);
        print $2;
        exit
      }' "$ENV_FILE"
  fi
}

#############################################
# HOSTNAME CHECK / FIX
#############################################
fix_hosts() {
  local HOSTS_FILE="/etc/hosts"
  local REQUIRED="127.0.0.1 postgres redis rest-server"

  echo ">>> Проверяю алиасы в /etc/hosts..."

  # уже есть rest-server? — ок
  if grep -qE "\brest-server\b" "$HOSTS_FILE" 2>/dev/null; then
    log_ok "/etc/hosts: alias rest-server уже присутствует"
    return 0
  fi

  # можем ли писать в hosts?
  if $SUDO test -w "$HOSTS_FILE" 2>/dev/null; then
    log_info "Добавляю alias'ы postgres / redis / rest-server в /etc/hosts"
    $SUDO cp "$HOSTS_FILE" "$HOSTS_FILE.bak" || true
    echo "$REQUIRED" | $SUDO tee -a "$HOSTS_FILE" >/dev/null
    log_ok "Добавлено: $REQUIRED"
  else
    log_err "/etc/hosts недоступен для записи (read-only)."
    echo "    Пропускаю добавление алиасов."
    echo "    Возможно, это запуск внутри Docker build — это нормально."
    echo "    Во время реального запуска контейнера / VM запись обычно доступна."
  fi
}

#############################################
# WAKE: POSTGRES
#############################################
wake_postgres() {
  if ! command -v pg_isready >/dev/null 2>&1; then
    log_err "pg_isready не найден — нет клиентских утилит PostgreSQL"
    return 1
  fi

  local pg_host pg_port pg_user pg_db pg_pass
  pg_host="$(env_get HACK__POSTGRES__HOST)"
  pg_port="$(env_get HACK__POSTGRES__PORT)"
  pg_user="$(env_get HACK__POSTGRES__USER)"
  pg_db="$(env_get HACK__POSTGRES__DATABASE)"
  pg_pass="$(env_get HACK__POSTGRES__PASSWORD)"

  pg_host="${pg_host:-127.0.0.1}"
  pg_port="${pg_port:-5432}"

  log_info "Проверяю PostgreSQL на ${pg_host}:${pg_port}..."

  if pg_isready -h "$pg_host" -p "$pg_port" >/dev/null 2>&1; then
    if PGPASSWORD="$pg_pass" psql -h "$pg_host" -p "$pg_port" -U "$pg_user" -d "$pg_db" -c "SELECT 1;" >/dev/null 2>&1; then
      log_ok "PostgreSQL уже запущен и отвечает"
      return 0
    else
      log_info "PostgreSQL отвечает на порт, но запросы не проходят — пробую перезапустить кластер"
    fi
  else
    log_info "PostgreSQL не отвечает — пробую запустить/перезапустить кластер"
  fi

  if ! command -v pg_lsclusters >/dev/null 2>&1 || ! command -v pg_ctlcluster >/dev/null 2>&1; then
    log_err "pg_lsclusters/pg_ctlcluster не найдены — не могу управлять PostgreSQL"
    return 1
  fi

  local line ver name port status owner data_dir logfile
  line="$(pg_lsclusters --no-header | awk -v p="$pg_port" '$3==p {print; exit}')"
  if [[ -z "$line" ]]; then
    line="$(pg_lsclusters --no-header | head -n1)"
  fi

  if [[ -z "$line" ]]; then
    log_err "pg_lsclusters не вернул ни одного кластера — PostgreSQL установлен криво"
    return 1
  fi

  read -r ver name port status owner data_dir logfile <<<"$line"
  log_info "Работаю с кластером PostgreSQL: версия=${ver}, кластер=${name}, порт=${port}"

  if ! $SUDO pg_ctlcluster "$ver" "$name" restart >/dev/null 2>&1; then
    log_info "pg_ctlcluster restart не удался, пробую start..."
    $SUDO pg_ctlcluster "$ver" "$name" start >/dev/null 2>&1 || true
  fi

  sleep 2

  if pg_isready -h "$pg_host" -p "$pg_port" >/dev/null 2>&1 && \
     PGPASSWORD="$pg_pass" psql -h "$pg_host" -p "$pg_port" -U "$pg_user" -d "$pg_db" -c "SELECT 1;" >/dev/null 2>&1; then
    log_ok "PostgreSQL успешно поднят и отвечает"
    return 0
  else
    log_err "Не удалось поднять PostgreSQL — проверь лог кластера: $logfile"
    return 1
  fi
}

#############################################
# WAKE: REDIS
#############################################
wake_redis() {
  if ! command -v redis-cli >/dev/null 2>&1; then
    log_err "redis-cli не найден — Redis клиентские утилиты не установлены"
    return 1
  fi

  local rhost rport
  rhost="$(env_get HACK__REDIS__HOST)"
  rport="$(env_get HACK__REDIS__PORT)"
  rhost="${rhost:-127.0.0.1}"
  rport="${rport:-6379}"

  log_info "Проверяю Redis на ${rhost}:${rport}..."

  if redis-cli -h "$rhost" -p "$rport" ping >/dev/null 2>&1; then
    log_ok "Redis уже запущен и отвечает"
    return 0
  fi

  log_info "Redis не отвечает — пробую запустить..."

  if [[ -f /etc/redis/redis.conf ]]; then
    redis-server /etc/redis/redis.conf --daemonize yes || true
  else
    redis-server --daemonize yes || true
  fi

  sleep 1

  if redis-cli -h "$rhost" -p "$rport" ping >/dev/null 2>&1; then
    log_ok "Redis успешно поднят и отвечает"
    return 0
  else
    log_err "Не удалось поднять Redis"
    return 1
  fi
}

#############################################
# REST-SERVER: START / STOP / STATUS
#############################################

start_rest_server() {
  cd "$PY_DIR"

  if [[ -f "$PID_FILE" ]]; then
    local old_pid
    old_pid="$(cat "$PID_FILE" || true)"
    if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
      log_ok "rest-server уже запущен (PID=$old_pid)"
      return 0
    else
      echo "Старый PID-файл найден, но процесс не жив — удаляю"
      rm -f "$PID_FILE"
    fi
  fi

  if [[ -f .env ]]; then
    set -a
    . .env
    set +a
  fi

  log_info "Запускаю rest-server в фоне, лог: $LOG_FILE"
  nohup run-rest-server >"$LOG_FILE" 2>&1 &

  local new_pid=$!
  echo "$new_pid" > "$PID_FILE"
  log_ok "rest-server запущен (PID=$new_pid)"
}

stop_rest_server() {
  if [[ ! -f "$PID_FILE" ]]; then
    log_err "PID-файл не найден, возможно, rest-server не запущен"
    return 1
  fi

  local pid
  pid="$(cat "$PID_FILE" || true)"

  if [[ -z "$pid" ]]; then
    log_err "PID-файл пустой"
    rm -f "$PID_FILE"
    return 1
  fi

  if kill -0 "$pid" 2>/dev/null; then
    log_info "Останавливаю rest-server (PID=$pid)..."
    kill "$pid" || true
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
      log_info "Процесс ещё жив, посылаю SIGKILL..."
      kill -9 "$pid" || true
    fi
    log_ok "rest-server остановлен"
  else
    log_info "Процесс с PID=$pid не найден — очищаю PID-файл"
  fi

  rm -f "$PID_FILE"
}

status_rest_server() {
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid="$(cat "$PID_FILE" || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      log_ok "rest-server запущен (PID=$pid)"
      return 0
    fi
  fi
  log_err "rest-server не запущен"
  return 1
}

#############################################
# MAIN
#############################################

cmd="${1:-start}"

case "$cmd" in
  start)
    if [[ ! -f "$ENV_FILE" ]]; then
      log_err "Не найден python/.env ($ENV_FILE). Сначала запусти bootstrap.sh"
      exit 1
    fi
    fix_hosts
    wake_postgres || true
    wake_redis || true
    start_rest_server
    ;;
  stop)
    stop_rest_server
    ;;
  restart)
    stop_rest_server || true
    wake_postgres || true
    wake_redis || true
    start_rest_server
    ;;
  status)
    status_rest_server
    ;;
  *)
    echo "Использование: $0 [start|stop|restart|status]"
    exit 1
    ;;
esac
