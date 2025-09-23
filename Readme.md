# 🤖 Telegram-бот для продажи онлайн-курсов

Многофункциональный Telegram-бот для автоматизированной продажи онлайн-курсов с админ-панелью, статистикой и интеграцией с платежной системой ЮKassa через Telegram Payments.

---

## 🚀 Основные возможности

### Для пользователей

- 🎓 **Каталог курсов** — просмотр списка доступных курсов с описанием и ценами.
- 💳 **Покупка** — интеграция с ЮKassa через Telegram Payment API.
- ⏱ **Автоотмена неоплаченных заказов** — если пользователь не завершил оплату за 10 минут, заказ автоматически отменяется.
- 🤖 **Автоматическая выдача доступа** — после оплаты бот мгновенно предоставляет доступ к материалам курса.
- 📚 **Личный кабинет** — разделы "Мои курсы" и "История покупок" для удобного доступа к материалам и отслеживания платежей.

### Для администраторов

- 🔐 **Защищённая админ-панель** — доступ только для ID из списка администраторов.
- ➕ **Управление курсами (CRUD)**
  - Добавление новых курсов через пошаговый диалог
  - Просмотр, редактирование и удаление существующих курсов
- 👥 **Управление пользователями** — просмотр зарегистрированных пользователей с пагинацией.
- 📊 **Статистика** — ключевые метрики: количество пользователей, покупок, общая сумма дохода.
- 🛡️ **Надёжность** — встроенный механизм защиты от флуда (троттлинг).

---

## 🛠️ Стек технологий

- **Python 3.10+**
- **Aiogram 3** — асинхронный фреймворк для Telegram Bot API
- **AIOHTTP** — для работы с вебхуками
- **asyncpg** — асинхронный драйвер для PostgreSQL
- **ЮKassa через Telegram Payment API** — приём платежей
- **Nginx, Gunicorn, systemd** — для развертывания на VPS

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
│   ├── admin.py
│   └── payments.py
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
WEBHOOK_HOST="https://your-domain.com"
DATABASE_URL=postgresql://coursesbot_user:your_password@localhost:5432/coursesbot_db
```

---

## 🖥️ Настройка PostgreSQL на VPS

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo -i -u postgres
psql
```

Внутри `psql` создаем базу и пользователя:

```sql
CREATE DATABASE coursesbot_db;
CREATE USER coursesbot_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE coursesbot_db TO coursesbot_user;
\q
exit
```

Перезапуск PostgreSQL:

```bash
sudo systemctl restart postgresql
```

---

## 5️⃣ Production на Render.com

1. Загрузите код на GitHub.
2. Создайте Web Service, подключив репозиторий.
3. Добавьте переменные окружения.

---

## 6️⃣ Production на VPS (Ubuntu 22.04)

### 6.1 Первоначальная настройка сервера

```bash
ssh root@ВАШ_IP_АДРЕС
adduser your_user
usermod -aG sudo your_user
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
ssh your_user@ВАШ_IP_АДРЕС
```

### 6.2 Установка окружения и проекта

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx git -y

git clone https://github.com/ваш_логин/ваш_репозиторий.git
cd ваш_репозиторий
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nano .env
```

### 6.3 Настройка Nginx

```bash
sudo nano /etc/nginx/sites-available/your_bot
sudo ln -s /etc/nginx/sites-available/your_bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Пример конфигурации `your_bot`:

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

### 6.4 Настройка systemd

```bash
sudo nano /etc/systemd/system/your_bot.service
sudo systemctl daemon-reload
sudo systemctl enable your_bot.service
sudo systemctl start your_bot.service
sudo systemctl status your_bot.service
sudo journalctl -u your_bot.service -f
```

Пример сервиса:

```
[Unit]
Description=Telegram Course Bot
After=network.target

[Service]
User=your_user
Group=www-data
WorkingDirectory=/home/your_user/ваш_репозиторий
ExecStart=/home/your_user/ваш_репозиторий/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 6.5 Настройка HTTPS (Certbot)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx
sudo systemctl restart nginx
sudo systemctl restart your_bot.service
```

---

## 🕹️ Использование

### Пользовательский интерфейс

- `/start` — регистрация и начало работы
- Меню кнопок — навигация по курсам, просмотр покупок и истории

### Админ-панель

- `/admin` — доступ только для ADMIN_IDS
- Кнопки — управление курсами, пользователями, статистикой

---

## 💖 Донаты

Если вам понравился бот, вы можете отправить донат на :

#### BTC: bc1qa3c5xdc6a3n2l3w0sq3vysustczpmlvhdwr8vc

Спасибо за вашу поддержку! 🙏
