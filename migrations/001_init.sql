-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица курсов
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    short_description TEXT,
    full_description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    materials_link TEXT NOT NULL
);

-- Таблица купленных курсов
CREATE TABLE IF NOT EXISTS user_courses (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    course_id INTEGER NOT NULL REFERENCES courses(id),
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, course_id)
);

-- Таблица истории платежей
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    course_id INTEGER NOT NULL REFERENCES courses(id),
    amount NUMERIC(10, 2) NOT NULL,
    status TEXT NOT NULL,
    message_id BIGINT,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
