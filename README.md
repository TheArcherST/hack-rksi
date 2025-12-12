# Backend TTK Афиши

Это бекенд решения команды asyncore кейса от ТТК на хакатоне IT-Tech 2025. 
Решение победило в номинации «Лучшее WEB-приложение» (приз 50 т.р.)

Фронтенд: https://github.com/addavriance/rksi-hack-app

Задеплоенный проект: https://ttk-afisha.lvalue.dev/


## Запуск

1. Установить `docker` и `make`.
2. Скопировать все `.env.example` → `.env` и заполнить.
3. Запустить:
   ```bash
   make up
    ```
4. По умолчанию (.env.example), REST API будет доступен по адресу http://127.0.0.1:8080

## Интеграционные тесты

Интеграционными тестами покрыты все happy-path сценарии за исключением требующих
сложных проверок отправленной почты и планирования доставки уведомлений: это 
тестировалось вручную. По unhappy path есть проверки связанные с важными 
аспектами безопасности, в т.ч. неуспешная аутентификация и авторизация, работа 
рейт лимитера на подтверждение почты.

Как прогнать в рамках запущенного compose стека:
```bash
make test 
```

Примечание: знаю, что дизайн тестов не идеальный (например используются debug 
эндпоинты), но он в полной мере выполнял свою задачу в рамках хакатона: 
дать уверенность в том, что во время защиты всё точно работает.

## Архитектура в первом приближении

```mermaid
flowchart LR
    Client -->|HTTP| API[FastAPI + Dishka]

    subgraph Storage[Хранилища]
        PG[Postgres]
        S3[S3-совместимое хранилище]
    end

    subgraph RedisBlock[Redis]
        RL[Счётчик с TTL]
        Q[Очередь задач]
    end

    API -->|Постоянное хранение| PG
    API -->|Распределённое хранение| S3
    API -->|Rate limiting| RL
    API -->|Ставит задачи| Q

    Scheduler[TaskIQ Scheduler] -->|Планирует задачи| Q
    Worker[TaskIQ Worker] -->|Берёт задачи| Q
        
    Worker -->|Фиксирует уведомления| PG
    Worker -->|Отправляет почту| Email[Почтовый сервер]
```


## Сущности, жизненный цикл которых поддерживается РСУБД
```mermaid
erDiagram
    USER ||--o{ LOGIN_SESSION : "1 : N"
    USER ||--o{ ISSUED_LOGIN_RECOVERY : "1 : N"
    USER ||--o{ EVENT_PARTICIPANT : "N : M"
    USER ||--o{ INSTANT_NOTIFICATION : "1 : N"
    EVENT ||--o{ EVENT_PARTICIPANT : "1 : N"

    USER {
      int id PK
      string email UK
      string username UK
      string full_name
      string password_hash
      string role "USER | ADMINISTRATOR"
      bool is_system
      datetime created_at
      datetime deleted_at "nullable"
    }

    LOGIN_SESSION {
      uuid uid PK
      int user_id FK "FK to USER.id"
      string token
      string user_agent "nullable"
      datetime created_at
    }

    ISSUED_REGISTRATION {
      int id PK
      string email
      string full_name
      string password_hash
      int verification_code
      uuid token
      datetime created_at
    }

    ISSUED_LOGIN_RECOVERY {
      int id PK
      int user_id FK "FK to USER.id"
      uuid token UK
      datetime created_at
      datetime used_at "nullable"
    }

    EVENT {
      int id PK
      string name
      string short_description "nullable"
      string description
      datetime starts_at
      datetime ends_at
      string image_url
      string payment_info "nullable"
      int max_participants_count "nullable"
      string location "nullable"
      datetime created_at
      datetime rejected_at "nullable"
    }

    EVENT_PARTICIPANT {
      int id PK
      int event_id FK "FK to EVENT.id"
      int user_id FK "FK to USER.id"
      string status "PARTICIPATING | REJECTED"
      datetime reminder_queued_at "nullable"
      datetime created_at
    }

    INSTANT_NOTIFICATION {
      int id PK
      int recipient_id FK "FK to USER.id"
      string title
      string content
      string cta_url "nullable"
      string cta_label "nullable"
      datetime acked_at "nullable"
      datetime created_at
    }

```

## Про безопасность

- Есть рейт лимит на подтверждение почты (кулдаун min(30с*2**retries_count, 1ч),
  начинает блокировать ввод после второй неудачной попытки)
- Пароль хэшируется алгоритмом argon2 с солью (используется готовое решение 
  полного флоу самого процесса хэширования); подробности того, как именно
  работают процессы связанные с аутентификацией и авторизацией можно найти
  в python/src/hack/core/services/access.py.
