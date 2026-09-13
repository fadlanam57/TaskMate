import os
import re
import sqlite3

try:
    import psycopg2
    from psycopg2.extras import DictCursor
except ImportError:
    psycopg2 = None
    DictCursor = None

# Lokasi file taskmate.db lokal (berada di root project)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'taskmate.db')

def adapt_query_for_sqlite(query):
    """
    Menyesuaikan query SQL agar kompatibel dengan SQLite:
    - Mengubah operator ILIKE (PostgreSQL) menjadi LIKE (SQLite).
    - Mengubah placeholder %s (psycopg2) menjadi ? (sqlite3).
    """
    # Ganti ILIKE menjadi LIKE
    adapted = re.sub(r'\bILIKE\b', 'LIKE', query, flags=re.IGNORECASE)
    # Ganti %s menjadi ? dengan aman (melindungi %% jika ada)
    adapted = adapted.replace('%%', '__ESCAPED_PERCENT__')
    adapted = re.sub(r'%s', '?', adapted)
    adapted = adapted.replace('__ESCAPED_PERCENT__', '%')
    return adapted

class SQLiteCursorWrapper:
    """
    Wrapper cursor SQLite untuk kompatibilitas penuh:
    - Menyesuaikan query (%s -> ?, ILIKE -> LIKE).
    - Menangani klausa RETURNING id jika SQLite versi lama tidak mendukungnya.
    """
    def __init__(self, cursor):
        self._cursor = cursor
        self._custom_row = None

    def execute(self, query, params=None):
        self._custom_row = None
        adapted = adapt_query_for_sqlite(query)
        try:
            if params is not None:
                self._cursor.execute(adapted, params)
            else:
                self._cursor.execute(adapted)
        except sqlite3.OperationalError as e:
            # Fallback jika klausul RETURNING tidak didukung di SQLite versi lama
            if 'RETURNING' in query.upper() and ('syntax error' in str(e).lower() or 'near' in str(e).lower()):
                query_no_returning = re.sub(r'\s+RETURNING\s+.*$', '', adapted, flags=re.IGNORECASE)
                if params is not None:
                    self._cursor.execute(query_no_returning, params)
                else:
                    self._cursor.execute(query_no_returning)
                self._custom_row = {'id': self._cursor.lastrowid}
            else:
                raise
        return self

    def executemany(self, query, seq_of_params):
        adapted = adapt_query_for_sqlite(query)
        self._cursor.executemany(adapted, seq_of_params)
        return self

    def fetchone(self):
        if self._custom_row is not None:
            row = self._custom_row
            self._custom_row = None
            return row
        return self._cursor.fetchone()

    def fetchall(self):
        if self._custom_row is not None:
            row = self._custom_row
            self._custom_row = None
            return [row]
        return self._cursor.fetchall()

    def fetchmany(self, size=None):
        if self._custom_row is not None:
            row = self._custom_row
            self._custom_row = None
            return [row]
        if size is not None:
            return self._cursor.fetchmany(size)
        return self._cursor.fetchmany()

    def close(self):
        return self._cursor.close()

    def __iter__(self):
        return iter(self._cursor)

    def __getattr__(self, name):
        return getattr(self._cursor, name)

class SQLiteConnectionWrapper:
    """
    Wrapper koneksi SQLite untuk menyediakan antarmuka .execute()
    yang kompatibel dengan gaya PostgreSQL psycopg2 / SQLite dengan penyesuaian query otomatis.
    """
    db_type = 'sqlite'

    def __init__(self, conn):
        self._conn = conn

    def cursor(self, *args, **kwargs):
        return SQLiteCursorWrapper(self._conn.cursor(*args, **kwargs))

    def execute(self, query, params=None):
        cur = self.cursor()
        cur.execute(query, params)
        return cur

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)

class PostgresConnectionWrapper:
    """
    Wrapper koneksi psycopg2 untuk menyediakan antarmuka .execute()
    yang kompatibel dengan gaya SQLite sebelumnya, menggunakan DictCursor.
    """
    db_type = 'postgres'

    def __init__(self, conn):
        self._conn = conn

    def cursor(self, *args, **kwargs):
        if 'cursor_factory' not in kwargs and DictCursor is not None:
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

def get_sqlite_connection():
    """
    Membuka koneksi ke database SQLite lokal (taskmate.db).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return SQLiteConnectionWrapper(conn)

def get_db_connection():
    """
    Membuka koneksi database:
    1. Jika DATABASE_URL tersedia (misalnya di Vercel / Cloud), gunakan PostgreSQL.
    2. Jika DATABASE_URL tidak tersedia (mode lokal), gunakan SQLite (taskmate.db).
    Tidak akan menyebabkan aplikasi error jika DATABASE_URL belum diatur.
    """
    database_url = os.environ.get('DATABASE_URL', '').strip()
    if database_url:
        if psycopg2 is None:
            print("[TaskMate] Peringatan: DATABASE_URL tersedia tetapi modul psycopg2 belum terpasang. Menggunakan SQLite lokal.")
            return get_sqlite_connection()

        try:
            # Supabase / Heroku / Vercel terkadang menggunakan format 'postgres://'
            # sedangkan psycopg2 memerlukan 'postgresql://'
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)

            raw_conn = psycopg2.connect(database_url, cursor_factory=DictCursor)
            return PostgresConnectionWrapper(raw_conn)
        except Exception as e:
            print(f"[TaskMate] Peringatan: Gagal terhubung ke PostgreSQL ({e}). Beralih ke SQLite lokal.")
            return get_sqlite_connection()

    return get_sqlite_connection()

def ensure_tables():
    """
    Memastikan semua tabel (tasks, users) telah terbentuk tanpa menghapus data yang ada.
    Mendukung SQLite lokal maupun PostgreSQL di cloud.
    """
    try:
        conn = get_db_connection()
        is_pg = getattr(conn, 'db_type', 'sqlite') == 'postgres'

        if is_pg:
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
        else:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    auth_provider TEXT DEFAULT 'local',
                    avatar TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            conn.commit()
            conn.close()
            print("[TaskMate] Tabel database SQLite (taskmate.db) berhasil diverifikasi.")
    except Exception as e:
        print(f"[TaskMate] Peringatan saat inisialisasi tabel: {e}")

def init_db():
    """
    Inisialisasi tabel database dan mengisi data contoh dari schema.sql (jika diperlukan).
    """
    conn = get_db_connection()
    schema_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    if os.path.exists(schema_file):
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        is_pg = getattr(conn, 'db_type', 'sqlite') == 'postgres'
        if is_pg:
            conn.execute(sql_script)
            conn.commit()
            print("[TaskMate] Database PostgreSQL berhasil diinisialisasi dari schema.sql!")
        else:
            conn._conn.executescript(sql_script)
            print("[TaskMate] Database SQLite berhasil diinisialisasi dari schema.sql!")
    conn.close()

if __name__ == '__main__':
    ensure_tables()
