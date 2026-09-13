-- =============================================================================
-- TaskMate Database Schema for PostgreSQL (Supabase / Neon / Vercel Postgres)
-- =============================================================================

-- 1. Tabel Tasks (Daftar Tugas Kuliah)
DROP TABLE IF EXISTS tasks CASCADE;

CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    course TEXT NOT NULL,
    description TEXT,
    deadline TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Belum Dikerjakan',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabel Users (Autentikasi Mahasiswa)
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    auth_provider VARCHAR(50) DEFAULT 'local',
    avatar TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Data Awal Contoh Tugas Kuliah
INSERT INTO tasks (title, course, description, deadline, priority, status)
VALUES 
('Membuat Laporan Praktikum 1', 'Pemrograman Web', 'Laporan modul pengenalan HTML, CSS, dan Flask', '2026-09-20', 'Tinggi', 'Belum Dikerjakan'),
('Mengerjakan Latihan Bab 3', 'Kalkulus II', 'Latihan nomor 1 sampai 15 pada buku referensi', '2026-09-18', 'Sedang', 'Sedang Dikerjakan'),
('Membaca Paper Jurnal AI', 'Kecerdasan Buatan', 'Review paper untuk bahan diskusi kelompok', '2026-09-15', 'Rendah', 'Selesai');
