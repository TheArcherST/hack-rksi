## Запуск

1. Установить `docker` и `make`.
2. Скопировать все `.env.example` → `.env` и заполнить.
3. Запустить:
   ```bash
   make up
    ```
4. По умолчанию (.env.example), REST API будет доступен по адресу http://127.0.0.1:8080

## Интеграционные тесты

1. Запустить:
    ```bash
    make test 
    ```


## Предметная область

Событие
1. name (NOT NULL)
2. short_description (NULL, для всплывающей подсказки)
3. description (NOT NULL, для карточки события)
4. starts_at (NOT NULL, больше даты создания)
5. ends_at (NOT NULL, должна быть позже даты начала)
6. image_url (NOT NULL)
7. payment_info (текстовое поле для описания процесса оплаты, например: 
  "Сегодня у Синельникова Станислава день рождения, собираем ему на подарок. 
  Можно перевести на ВТБ (200р) по номеру 89185123076. В переводе прошу указать
  свое ФИО и подтвердить участие.", необязательное)
8. max_participants_count (NULL)
9. location (NULL, примечание: нестандартное поле, может потом удалим)
10. created_at (NOT NULL, внутреннее поле)
11. rejected_at (NULL)
12. status (Вычисляемое поле. ACTIVE/PAST/REJECTED)

Участник события
1. event_id
2. user_id
3. Дата создания

Пользователь
1. Email
2. Username (= email)
3. Password hash
4. Role (user/administrator)
5. Дата создания (регистрации)
6. Дата удаления
