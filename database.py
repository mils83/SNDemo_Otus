import psycopg2
import time
from psycopg2.pool import ThreadedConnectionPool, PoolError
import os

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "social_network")
DB_USER = os.getenv("DB_USER", "postgres") # В проде поменять на нормального пользователя.
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres") # В проде поменять на нормального пользователя.

# Пул соединений: суммарный размер по всем воркерам uvicorn должен оставаться
# заметно ниже max_connections в PostgreSQL (по умолчанию 100), иначе под
# пиковым параллелизмом БД начнёт отдавать "too many clients".
DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", "1"))
DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", "20"))

_pool: ThreadedConnectionPool | None = None


def _get_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(
            DB_POOL_MIN, DB_POOL_MAX,
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
    return _pool


def get_db_connection(timeout: float = 30.0):
    """Выдать соединение из пула, при исчерпании пула — дождаться освобождения."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            return _get_pool().getconn()
        except PoolError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.02)


def put_db_connection(conn):
    """Вернуть соединение в пул. ВСЕГДА вызывать вместо conn.close()."""
    _get_pool().putconn(conn)
