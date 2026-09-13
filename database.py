import sqlite3

DATABASE_NAME = 'taskmate.db'

def get_db_connection():
    """
    Membuka koneksi ke SQLite dengan row_factory untuk akses dictionary-like.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_tables():
    """
    Memastikan semua tabel (tasks, users) telah terbentuk tanpa menghapus data yang ada.
    """
    conn = get_db_connection()
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

def init_db():
    """
    Inisialisasi tabel database dan mengisi data contoh.
    """
    conn = get_db_connection()
    with open('schema.sql', 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Database taskmate.db berhasil diinisialisasi!")

if __name__ == '__main__':
    ensure_tables()
    print("Tabel database berhasil diverifikasi.")

