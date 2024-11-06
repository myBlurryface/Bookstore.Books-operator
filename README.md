**Books-operator API app**
```markdown
## Один из двух микросервисов Bookstore API
Втрой микросервис - https://github.com/myBlurryface/Bookstore.Bookstore-Statistics/tree/master

Bookstore это REST API для управления онлайн магазином книг с помощью Django, PostgreSQL, KAFKA. 
Проект поддерживает аутентификацию с использованием JWT и использует Docker для контейнеризации приложения.


## Основные возможности Bookstore-operator

- Регистрация и аутентификация пользователей
- Создание, обновление и удаление книг
- Отбор книг по жанру/автору
- Сбор корзины из книг
- Покупка книг из корзины 
- Поддержка аутентификации JWT
- Трансфер данных о пользователях и заказах в Bookstore-Statistics

## Стек технологий

- Python 3.12
- Django Rest Framework
- PostgreSQL
- Docker и Docker Compose
- JWT для аутентификации
- Kafka

## Требования

Для запуска проекта вам потребуется:

- Docker и Docker Compose
- Python 3.12 (если не использовать Docker)
- Установленная и настроенная база данных PostgreSQL
- Kafka при запуске не из контейнера
```

## Установка

### Шаг 1: Установка и настройка PostgreSQL

#### 1. Установка PostgreSQL

##### macOS (с Homebrew):
```bash
brew install postgresql
brew services start postgresql
```

##### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

##### Linux (Fedora/RHEL):
```bash
sudo dnf install postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
sudo systemctl start postgresql
```

##### Windows:
Загрузите и установите PostgreSQL: [PostgreSQL для Windows](https://www.postgresql.org/download/windows/)

#### 2. Настройка PostgreSQL

1. Войдите в PostgreSQL как суперпользователь:
   ```bash
   sudo -u postgres psql
   ```

2. Создайте пользователя и базу данных:
   ```sql
   CREATE USER books_operator WITH PASSWORD 'operator_password';
   CREATE DATABASE db_bookstore_operator;
   GRANT ALL PRIVILEGES ON DATABASE db_bookstore_operator TO books_operator;
   \q
   ```

#### 3. Установите KAFKA
1. Используйте порт 9092 .
2. Создайте топики: customer_topic, order_topic.

### Шаг 2: Клонирование репозитория

Склонируйте репозиторий на вашу локальную машину:

```bash
git clone https://github.com/myBlurryface/Bookstore.Books-operator/tree/master
cd Bookstore.Books-operator
```

### Шаг 3: Настройка переменных окружения

Создайте файл `.env` в корневой директории проекта. Пример содержимого:

```bash
POSTGRES_DB=db_bookstore # Название ДБ
POSTGRES_USER=books_operator # Пользователь ДБ
POSTGRES_PASSWORD=db_bookstore_operator # Пароль DB 
DB_PORT=5432 # Порт ДБ

# !! Обязательный параметр призапуске из контейнера 
DB_HOST=bookstore-db-1

# При запуске локально  
DB_HOST="localhost"

KAFKA_BROKER=kafka:9092

```

### Шаг 4: Запуск с использованием Docker

1. Перейдите в корневую директорию проекта. Затем постройте и запустите контейнеры:

    ```bash
    docker-compose up --build
    ```

2. Выполните миграции базы данных:

    ```bash
    docker exec web python manage.py migrate
    ```

3. Создайте суперпользователя для доступа к Django admin:

    ```bash
    docker exec web python manage.py createsuperuser
    ```

4. Создайте нужные топики:

    ```bash
    docker exec -it kafka /bin/kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic customer_topic
    docker exec -it kafka /bin/kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic order_topic  
    docker exec -it kafka /bin/kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic order_items_topic 
    ```
Теперь приложение доступно по адресу `http://localhost:8000`.

### Шаг 5: Локальный запуск (без Docker)

Если вы хотите запустить проект без Docker:

1. Установите зависимости:

    ```bash
    pip install -r requirements.txt
    ```

2. Выполните миграции базы данных:

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

3. Запустите сервер разработки:

    ```bash
    python manage.py runserver
    ```

4. Создайте суперпользователя:

    ```bash
    python manage.py createsuperuser
    ```
### **Models Overview**

Модели и их описание
1. Book (Книга)

Описание: Модель, представляющая книги в магазине.

• Поля:
    • title: Название книги (строка, обязательное).
    • author: Автор книги (строка, обязательное). 
    • description: Описание книги (текст).
    • synopsis: Краткий синопсис (текст).
    • genre: Жанр книги (строка).
    • price: Цена книги (десятичное число).
    • discount: Скидка на книгу (десятичное число, по умолчанию 0.00).
    • stock: Количество книг в наличии (целое положительное число).

• Методы:
    __str__(): Возвращает название книги.

2. Customer (Покупатель)

Описание: Расширенная модель пользователя с дополнительными полями.

• Поля:
    • user: Связь с моделью User.
    • phone_number: Номер телефона (строка, уникальное).
    • address: Адрес (текст, необязательное).
    • total_spent: Сумма, потраченная пользователем (десятичное число).

• Методы:

    __str__(): Возвращает имя пользователя.
    update_total_spent(amount): Обновляет поле total_spent.

3. Review (Отзыв)

Описание: Отзывы пользователей о книгах.

• Поля:
    • book: Связь с моделью Book.
    • user: Связь с моделью User.
    • rating: Оценка (целое число от 1 до 5).
    • comment: Комментарий (текст, необязательное).
    • created_at: Дата и время создания (автоматическое).
    • updated_at: Дата и время обновления (автоматическое).

• Методы:
    __str__(): Возвращает строку вида "Review by [пользователь] for [книга]".

• Особенности:
    Поля user и book имеют ограничение на уникальность (уникальный отзыв для каждой книги от одного пользователя).

4. Cart (Корзина)

Описание: Модель корзины пользователя.

• Поля:
    • customer: Связь с моделью Customer.
    • book: Связь с моделью Book.
    • quantity: Количество книг в корзине.
    • added_at: Дата добавления (автоматическое).

• Методы:
    __str__(): Возвращает строку вида "[количество] of [книга] in cart of [пользователь]".

• Особенности:
    Уникальная запись по customer и book.

5. Order (Заказ)

Описание: Модель заказа с детализацией статуса.

• Поля:
    • customer: Связь с моделью Customer.
    • created_at: Дата создания (автоматическое).
    • updated_at: Дата обновления (автоматическое).
    • status: Статус заказа (выбор из вариантов: pending, processed, shipped, delivered, canceled).
    • total_price: Общая стоимость заказа.
    • discount: Скидка на заказ.

• Методы:
    __str__(): Возвращает строку вида "Order [id] by [пользователь]".
    calculate_total(): Вычисляет общую стоимость заказа с учетом скидок.

6. OrderItem (Элемент заказа)

Описание: Отдельный элемент в заказе.

• Поля:
    • order: Связь с моделью Order.
    • book: Связь с моделью Book.
    • quantity: Количество единиц.
    • price: Цена за единицу.
    • discount: Скидка на единицу.

• Методы:
    __str__(): Возвращает строку вида "[количество] of [книга] in order [id]".
    get_total_price(): Возвращает общую стоимость для элемента заказа с учетом скидки.

### API Документация

## API Маршруты

  # Основные маршруты:

  • /books/: Список всех книг.
  • /books/{id}/: Подробная информация о книге.
  • /cart/: Просмотр и управление корзиной пользователя.
  • /orders/: Просмотр и создание заказов.
  • /reviews/: Просмотр и создание отзывов о книгах.

  # Дополнительные маршруты:

  • /books/by_author/: Поиск книг по автору.
  • /books/by_genre/: Поиск книг по жанру.
  • /cart/clear-cart/: Очистка корзины пользователя.
  • /orders/create_order/: Создание нового заказа.

  # Аутентификация и безопасность
  • JWT: Аутентификация через JSON Web Token с помощью /api/token/ для получения токена и /api/token/refresh/ для его обновления.
  • Django Admin: Управление сущностями доступно через стандартные URL-адреса административной панели.
  • Пример использования API
      ```bash
    echo "Регистрация пользователя если он не аутентифицирован""
    curl -X POST http://localhost:8000/customer/ \
    -H "Content-Type: application/json" \
    -d '{
      "username": "username",
      "email": "username@example.com",
      "password": "password",
      "phone_number": "123457890",
      "address": "Adress Street"
    }'      

    echo "Создание книги администратором (может управлять только администратор) "
    ADMIN_TOKEN=
    curl -X POST "$BASE_URL/books/" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "title": "Book",
      "author": "Author",
      "description": "Description",
      "synopsis": "Synopsis",
      "genre": "Genre",
      "price": "20.00",
      "discount": "10.00",
      "stock": 4
    }'
    ```

  # Дополнительно с API маршрутами можно ознакомиться с помощью команды 
      ```bash
      python manage.py show_urls
      ```
### Аутентификация

- Получение JWT токенов:
  - URL: `/api/token/`
  - Метод: `POST`
  - Параметры:
    ```json
    {
      "username": "ваш_username",
      "password": "ваш_пароль"
    }
    ```

- Обновление JWT токена:
  - URL: `/api/token/refresh/`
  - Метод: `POST`
  - Параметры:
    ```json
    {
      "refresh": "ваш_refresh_token"
    }
    ```

## Автоматическое тестирование
!! Перед запуском тестов замокать kafka_producer.py
Запуск тестов:

```bash
# Используя Docker
docker exec web python manage.py test
# Не используя Docker
python manage.py test
```

## Автор

- Лозицкий Константин — ralf_201@hotmail.com
- GitHub: [ваш GitHub профиль](https://github.com/myBlurryface)
