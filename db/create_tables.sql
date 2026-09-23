-- Создание таблицы пользователей бота
CREATE TABLE IF NOT EXISTS users (
    vk_id INTEGER PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    age INTEGER,
    city VARCHAR(100),
    gender INTEGER, -- 1 = жен, 2 = муж (согласно документации VK API)
    search_gender VARCHAR(10), -- 'man', 'woman' или NULL
    photo_url VARCHAR(1000)  -- Ссылка на аватарку пользователя
);

-- Создание таблицы кандидатов для знакомств
CREATE TABLE IF NOT EXISTS candidates (
    vk_id INTEGER PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    profile_link VARCHAR(255) NOT NULL
);

-- Создание таблицы фотографий кандидатов
-- Связь один-ко-многим: один кандидат может иметь несколько фото
CREATE TABLE IF NOT EXISTS photos (
    id SERIAL PRIMARY KEY,
    candidate_vk_id INTEGER NOT NULL REFERENCES candidates(vk_id) ON DELETE CASCADE,
    url VARCHAR(1000) NOT NULL,
    likes_count INTEGER DEFAULT 0
);

-- Создание таблицы избранных (связь многие-ко-многим)
-- Составной первичный ключ гарантирует, что один кандидат
-- не будет добавлен в избранное одним пользователем дважды
CREATE TABLE IF NOT EXISTS favorites (
    user_vk_id INTEGER NOT NULL REFERENCES users(vk_id) ON DELETE CASCADE,
    candidate_vk_id INTEGER NOT NULL REFERENCES candidates(vk_id) ON DELETE CASCADE,
    PRIMARY KEY (user_vk_id, candidate_vk_id)
);

-- Создание таблицы "чёрного списка" (связь многие-ко-многим)
-- Составной первичный ключ гарантирует, что один кандидат
-- не будет добавлен в чёрный список одним пользователем дважды
CREATE TABLE IF NOT EXISTS blacklist (
    user_vk_id INTEGER NOT NULL REFERENCES users(vk_id) ON DELETE CASCADE,
    candidate_vk_id INTEGER NOT NULL REFERENCES candidates(vk_id) ON DELETE CASCADE,
    PRIMARY KEY (user_vk_id, candidate_vk_id)
);

-- Создание индексов для ускорения поиска
CREATE INDEX IF NOT EXISTS idx_photos_candidate ON photos(candidate_vk_id);
CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_vk_id);