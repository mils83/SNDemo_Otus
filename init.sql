CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    gender VARCHAR(10) NOT NULL,
    interests TEXT,
    city VARCHAR(100)
);
-- Индексы не создаем согласно требованиям ДЗ (урок 1).

-- ----------------------------------------------------------------------------
-- ДЗ №6 «Производительность индексов»: индекс для поиска анкет по префиксу
-- имени и фамилии (метод /user/search). В базовом скелете остаётся
-- закомментированным; для нагрузочных экспериментов применяется отдельным
-- скриптом scripts/create_indexes.sql.
--
-- Составной btree + varchar_pattern_ops:
--   * обе колонки условия поиска в одном индексе — второй столбец фильтрует
--     прямо в индексе, без обращения к heap;
--   * varchar_pattern_ops обязателен в не-C локали: без него планировщик не
--     умеет использовать btree для LIKE 'префикс%';
--   * CONCURRENTLY — построение доступно на живой таблице.
-- ----------------------------------------------------------------------------
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_first_name_last_name_pattern
--     ON users (first_name varchar_pattern_ops, last_name varchar_pattern_ops);
-- ANALYZE users;