DROP TABLE IF EXISTS tasks;

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    course TEXT NOT NULL,
    description TEXT,
    deadline TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Belum Dikerjakan',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    auth_provider TEXT DEFAULT 'local',
    avatar TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data contoh awal agar kita dapat langsung menguji tampilan daftar tugas nanti
INSERT INTO tasks (title, course, description, deadline, priority, status)
VALUES 
('Membuat Laporan Praktikum 1', 'Pemrograman Web', 'Laporan modul pengenalan HTML, CSS, dan Flask', '2026-09-20', 'Tinggi', 'Belum Dikerjakan'),
('Mengerjakan Latihan Bab 3', 'Kalkulus II', 'Latihan nomor 1 sampai 15 pada buku referensi', '2026-09-18', 'Sedang', 'Sedang Dikerjakan'),
('Membaca Paper Jurnal AI', 'Kecerdasan Buatan', 'Review paper untuk bahan diskusi kelompok', '2026-09-15', 'Rendah', 'Selesai');

