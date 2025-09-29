# 🤖 Telegram-бот для продажи онлайн-курсов

Многофункциональный Telegram-бот для автоматизированной продажи онлайн-курсов с админ-панелью, статистикой и интеграцией с платежной системой ЮKassa.

---

## 🚀 Основные возможности

### Для пользователей

- 🎓 **Каталог курсов** — просмотр списка доступных курсов с описанием и ценами.
- 💳 **Покупка** — интеграция с ЮKassa (через Telegram Payments).
- ⏱ **Автоотмена неоплаченных заказов** — если пользователь не завершил оплату за 10 минут, заказ автоматически отменяется.
- 🤖 **Автоматическая выдача доступа** — после оплаты бот мгновенно предоставляет доступ к материалам курса.
- 📚 **Личный кабинет** — разделы "Мои курсы" и "История покупок".

### Для администраторов

- 🔐 **Защищённая админ-панель** — доступ только для ID из списка администраторов.
- ➕ **Управление курсами (CRUD)**
- 👥 **Управление пользователями** — просмотр зарегистрированных пользователей с пагинацией.
- 📊 **Статистика** — пользователи, покупки, доход.
- 🛡️ **Троттлинг** — защита от флуда.

---

## 🛠️ Стек технологий

- **Python 3.10+**
- **Aiogram 3** — асинхронный фреймворк для Telegram Bot API
- **AIOHTTP** — вебхуки
- **asyncpg** — PostgreSQL
- **ЮKassa через Telegram Payment API**
- **Nginx, Gunicorn, systemd** — деплой на VPS

---

## 📁 Структура проекта

```
coursesbot/
│── bot.py
│── config.py
│── database.py
│── requirements.txt
│── .env
│── .gitignore
│── README.md
│
├── handlers/
│   ├── user.py
│   └── admin.py
│
├── keyboards/
│   ├── user_kb.py
│   └── admin_kb.py
│
├── models/
│   ├── users.py
│   ├── courses.py
│   ├── payments.py
│   ├── user_courses.py
│   └── stats.py
│
├── migrations/
│   ├── 001_init.sql
│   └── 002_add_indexes.sql
│
├── states/
│   └── admin_states.py
│
├── middlewares/
│   └── throttling.py
│
└── filters/
    └── admin.py
```

---

## ⚙️ Установка и запуск

### 1️⃣ Клонируйте репозиторий

```bash
git clone <URL-вашего-репозитория>
cd <название-папки-проекта>
```

### 2️⃣ Создайте и активируйте виртуальное окружение

**Windows**:

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Установите зависимости

```bash
pip install -r requirements.txt
```

### 4️⃣ Настройте переменные окружения

Создайте файл `.env` и заполните его:

```ini
BOT_TOKEN="..."
ADMIN_IDS="..."
PAYMENT_PROVIDER_TOKEN="..."
DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
```

### 5️⃣ Production на Render.com

1. Загрузите код на GitHub.
2. Создайте Web Service, подключив репозиторий.
3. Добавьте переменные окружения.

---

## ☁️ Production на VPS (Ubuntu 22.04)

Инструкция предполагает наличие домена, указывающего на IP вашего VPS.

---

### 🔹 1. Первоначальная настройка сервера

```bash
ssh root@ВАШ_IP_АДРЕС
adduser your_user
usermod -aG sudo your_user
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
ssh your_user@ВАШ_IP_АДРЕС
```

---

### 🔹 2. Установка PostgreSQL

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
```

Создаём пользователя и базу:

```bash
sudo -u postgres psql
```

Внутри PostgreSQL:

```sql
CREATE DATABASE coursesbot;
CREATE USER botuser WITH PASSWORD 'strongpassword';
ALTER ROLE botuser SET client_encoding TO 'utf8';
ALTER ROLE botuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE botuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE coursesbot TO botuser;
\q
```

Проверьте подключение:

```bash
psql -U botuser -d coursesbot -h 127.0.0.1 -W
```

---

### 🔹 3. Загрузка и настройка бота

```bash
sudo apt install python3-pip python3-venv git -y
git clone https://github.com/ваш_логин/ваш_репозиторий.git
cd ваш_репозиторий
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nano .env
```

---

### 🔹 4. Настройка Nginx

```bash
sudo nano /etc/nginx/sites-available/your_bot
```

Конфигурация:

```
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Активируем:

```bash
sudo ln -s /etc/nginx/sites-available/your_bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### 🔹 5. Настройка systemd

```bash
sudo nano /etc/systemd/system/your_bot.service
```

**Вариант без Gunicorn:**

```
[Unit]
Description=Telegram Course Bot
After=network.target

[Service]
User=your_user
WorkingDirectory=/home/your_user/ваш_репозиторий
ExecStart=/home/your_user/ваш_репозиторий/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**Вариант с Gunicorn (рекомендация):**

```
ExecStart=/home/your_user/ваш_репозиторий/venv/bin/gunicorn --workers 4 --worker-class aiohttp.GunicornWebWorker bot:app
```

Активируем:

```bash
sudo systemctl daemon-reload
sudo systemctl enable your_bot.service
sudo systemctl start your_bot.service
sudo systemctl status your_bot.service
```

---

### 🔹 6. Настройка HTTPS (Certbot)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx
sudo systemctl restart nginx
sudo systemctl restart your_bot.service
```

---

## 🕹️ Использование

### Пользовательский интерфейс

- `/start` — регистрация
- Меню — навигация по курсам, покупки, история

### Админ-панель

- `/admin` — управление курсами, пользователями, статистикой

---

## 💖 Донаты

Если вам понравился проект:

- **BTC:** `bc1qa3c5xdc6a3n2l3w0sq3vysustczpmlvhdwr8vc`

Спасибо за вашу поддержку! 🙏
