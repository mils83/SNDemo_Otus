# Социальная сеть: Базовый скелет (ДЗ)

Проект представляет собой монолитное приложение на FastAPI с базой данных PostgreSQL.
В качестве доступа к БД используется чистый драйвер `psycopg2` (без ORM).

## Требования

- Docker и Docker Compose
- Python 3.10+

## Запуск приложения

1. **Запуск базы данных PostgreSQL:**
   Выполните команду в корне проекта:

    ```bash
    docker-compose up -d
    ```

База данных поднимется на `localhost:5432`, скрипт `init.sql` выполнится автоматически.

2. **Установка зависимостей Python:**\
   Рекомендуется использовать виртуальное окружение:

   ```bash
   python -m venv venv
   source venv/bin/activate  # для Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Запуск приложения:**

   ```bash
   python main.py
   ```

   Приложение будет доступно по адресу: `http://localhost:8000`\
   Документация Swagger UI: `http://localhost:8000/docs`

## Тестирование через Postman

1. Импортируйте файл `postman_collection.json` в Postman.
2. Выполните запрос **"1. Register User"** для создания анкеты.
3. Выполните запрос **"2. Login"**. Скрипт в Postman автоматически сохранит полученный токен в переменные коллекции.
4. Выполните запрос **"3. Get User by ID"** для просмотра анкеты (в заголовках уже подставится Bearer токен).
