import os
import psycopg2
from psycopg2.extras import DictCursor

class PostgresConnectionWrapper:
    """
    Wrapper koneksi psycopg2 untuk menyediakan antarmuka .execute()
    yang kompatibel dengan gaya SQLite sebelumnya, menggunakan DictCursor.
    """
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, *args, **kwargs):
        if 'cursor_factory' not in kwargs:
            kwargs['cursor_factory'] = DictCursor
        return self._conn.cursor(*args, **kwargs)

    def execute(self, query, params=None):
        cur = self.cursor()
        cur.execute(query, params or ())
        return cur

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)

def get_db_connection():
    """
    Membuka koneksi ke PostgreSQL menggunakan connection string
    dari environment variable DATABASE_URL.
    """
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError(
            "Environment variable DATABASE_URL belum diatur! "
            "Silakan tentukan DATABASE_URL pada environment variable Vercel atau file .env."
        )

    # Supabase / Heroku / Vercel terkadang menggunakan format 'postgres://'
    # sedangkan psycopg2 memerlukan 'postgresql://'
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    raw_conn = psycopg2.connect(database_url, cursor_factory=DictCursor)
    return PostgresConnectionWrapper(raw_conn)

def ensure_tables():
    """
    Memastikan semua tabel (tasks, users) telah terbentuk di PostgreSQL
    tanpa menghapus data yang ada.
    """
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("[TaskMate] Peringatan: DATABASE_URL belum disetel. Melewati ensure_tables().")
        return

    try:
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                course TEXT NOT NULL,
                description TEXT,
                deadline TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Belum Dikerjakan',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                auth_provider VARCHAR(50) DEFAULT 'local',
                avatar TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        conn.commit()
        conn.close()
        print("[TaskMate] Tabel database PostgreSQL berhasil diverifikasi.")
    except Exception as e:
        print(f"[TaskMate] Peringatan saat inisialisasi tabel: {e}")

def init_db():
    """
    Inisialisasi tabel database dan mengisi data contoh dari schema.sql.
    """
    conn = get_db_connection()
    with open('schema.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()
    conn.execute(sql_script)
    conn.commit()
    conn.close()
    print("[TaskMate] Database PostgreSQL berhasil diinisialisasi dari schema.sql!")

if __name__ == '__main__':
    ensure_tables()
