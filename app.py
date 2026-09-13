from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from database import get_db_connection, ensure_tables
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import json

app = Flask(__name__)
app.secret_key = 'taskmate_secret_key_student_vibe_coding'

# Pastikan tabel SQLite (tasks & users) sudah siap
ensure_tables()

@app.context_processor
def inject_user():
    return {'current_user': session.get('user', None)}

# Helper Filter untuk menghitung sisa hari deadline secara manusiawi
@app.template_filter('deadline_badge')
def deadline_badge_filter(deadline_str):
    try:
        today = date.today()
        d_date = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        diff = (d_date - today).days
        if diff < 0:
            return {'text': f'{abs(diff)} hari lewat', 'class': 'badge-overdue', 'urgent': True}
        elif diff == 0:
            return {'text': 'Hari ini!', 'class': 'badge-today', 'urgent': True}
        elif diff == 1:
            return {'text': 'Besok', 'class': 'badge-tomorrow', 'urgent': True}
        elif diff <= 3:
            return {'text': f'{diff} hari lagi', 'class': 'badge-approaching', 'urgent': True}
        else:
            return {'text': f'{diff} hari lagi', 'class': 'badge-upcoming', 'urgent': False}
    except Exception:
        return {'text': deadline_str, 'class': 'badge-upcoming', 'urgent': False}

def get_task(task_id):
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = %s', (task_id,)).fetchone()
    conn.close()
    if task is None:
        abort(404)
    return task

@app.route('/')
def index():
    status_filter = request.args.get('status', '').strip()
    priority_filter = request.args.get('priority', '').strip()
    search_query = request.args.get('q', '').strip()

    conn = get_db_connection()

    # 1. Hitung Statistik & Metrik Dashboard
    total_count = conn.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]
    todo_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Belum Dikerjakan'").fetchone()[0]
    in_progress_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Sedang Dikerjakan'").fetchone()[0]
    completed_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Selesai'").fetchone()[0]
    urgent_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE priority = 'Tinggi' AND status != 'Selesai'").fetchone()[0]

    # Hitung persentase progres penyelesaian
    progress_percent = int(round((completed_count / total_count * 100))) if total_count > 0 else 0

    stats = {
        'total': total_count,
        'todo': todo_count,
        'in_progress': in_progress_count,
        'completed': completed_count,
        'urgent': urgent_count,
        'progress_percent': progress_percent
    }

    # 2. Ambil Tugas dengan Deadline Terdekat (yang belum selesai)
    upcoming_tasks = conn.execute('''
        SELECT * FROM tasks 
        WHERE status != 'Selesai' 
        ORDER BY deadline ASC 
        LIMIT 4
    ''').fetchall()

    # 3. Bangun Kueri Filter Dinamis yang Aman
    query = 'SELECT * FROM tasks WHERE 1=1'
    params = []

    if status_filter and status_filter != 'Semua':
        query += ' AND status = %s'
        params.append(status_filter)

    if priority_filter and priority_filter != 'Semua':
        query += ' AND priority = %s'
        params.append(priority_filter)

    if search_query:
        query += ' AND (title ILIKE %s OR course ILIKE %s OR description ILIKE %s)'
        wildcard = f'%{search_query}%'
        params.extend([wildcard, wildcard, wildcard])

    query += " ORDER BY CASE status WHEN 'Selesai' THEN 2 ELSE 1 END, deadline ASC, id DESC"
    tasks = conn.execute(query, params).fetchall()

    courses = [row[0] for row in conn.execute("SELECT DISTINCT course FROM tasks WHERE course != '' ORDER BY course ASC").fetchall()]
    
    # 4. Ambil Seluruh Data Tugas untuk Kalender Interaktif
    all_tasks_raw = conn.execute('SELECT id, title, course, description, deadline, priority, status FROM tasks ORDER BY deadline ASC').fetchall()
    calendar_tasks_list = [
        {
            'id': row['id'],
            'title': row['title'],
            'course': row['course'],
            'description': row['description'] or '',
            'deadline': row['deadline'],
            'priority': row['priority'],
            'status': row['status']
        }
        for row in all_tasks_raw
    ]
    calendar_tasks_json = json.dumps(calendar_tasks_list)

    conn.close()

    today_str = datetime.now().strftime('%d %b %Y')

    return render_template('index.html', 
                           tasks=tasks, 
                           stats=stats, 
                           upcoming_tasks=upcoming_tasks,
                           courses=courses,
                           selected_status=status_filter, 
                           selected_priority=priority_filter,
                           search_query=search_query,
                           today_str=today_str,
                           calendar_tasks_json=calendar_tasks_json)

@app.route('/add', methods=['POST'])
def add_task():
    title = request.form.get('title', '').strip()
    course = request.form.get('course', '').strip()
    description = request.form.get('description', '').strip()
    deadline = request.form.get('deadline', '').strip()
    priority = request.form.get('priority', '').strip()
    status = request.form.get('status', 'Belum Dikerjakan').strip()

    if not title or not course or not deadline or not priority:
        flash('Mohon lengkapi judul, mata kuliah, deadline, dan prioritas tugas!', 'danger')
        return redirect(url_for('index'))

    if priority not in ['Rendah', 'Sedang', 'Tinggi']:
        priority = 'Sedang'

    if status not in ['Belum Dikerjakan', 'Sedang Dikerjakan', 'Selesai']:
        status = 'Belum Dikerjakan'

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO tasks (title, course, description, deadline, priority, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (title, course, description, deadline, priority, status))
    conn.commit()
    conn.close()

    flash(f'Tugas "{title}" berhasil ditambahkan!', 'success')
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_task(id):
    task = get_task(id)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        course = request.form.get('course', '').strip()
        description = request.form.get('description', '').strip()
        deadline = request.form.get('deadline', '').strip()
        priority = request.form.get('priority', '').strip()
        status = request.form.get('status', '').strip()

        if not title or not course or not deadline or not priority or not status:
            flash('Semua kolom wajib diisi dengan benar!', 'danger')
            return render_template('edit.html', task=task)

        conn = get_db_connection()
        conn.execute('''
            UPDATE tasks 
            SET title = %s, course = %s, description = %s, deadline = %s, priority = %s, status = %s
            WHERE id = %s
        ''', (title, course, description, deadline, priority, status, id))
        conn.commit()
        conn.close()

        flash(f'Tugas "{title}" berhasil diperbarui!', 'success')
        return redirect(url_for('index'))

    return render_template('edit.html', task=task)

@app.route('/status/<int:id>', methods=['POST'])
def update_status(id):
    new_status = request.form.get('new_status', '').strip()
    valid_statuses = ['Belum Dikerjakan', 'Sedang Dikerjakan', 'Selesai']

    if new_status in valid_statuses:
        conn = get_db_connection()
        conn.execute('UPDATE tasks SET status = %s WHERE id = %s', (new_status, id))
        conn.commit()
        conn.close()
        flash(f'Status tugas diubah menjadi "{new_status}"', 'success')
    else:
        flash('Status tugas tidak valid!', 'danger')

    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete_task(id):
    task = get_task(id)
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id = %s', (id,))
    conn.commit()
    conn.close()

    flash(f'Tugas "{task["title"]}" berhasil dihapus.', 'info')
    return redirect(url_for('index'))

# ==========================================================================
# RUTENYA AUTENTIKASI: LOGIN, REGISTER, GOOGLE SIGN-IN, LOGOUT
# ==========================================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Email dan password wajib diisi!', 'danger')
            return redirect(url_for('index', open_auth='login'))

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = %s', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            name = user['name']
            session['user'] = {
                'id': user['id'],
                'name': name,
                'email': user['email'],
                'provider': user['auth_provider'],
                'initial': name[0].upper() if name else 'M'
            }
            flash(f'Selamat datang kembali, {name}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email atau password salah. Silakan coba lagi!', 'danger')
            return redirect(url_for('index', open_auth='login'))

    return redirect(url_for('index', open_auth='login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not name or not email or not password or not confirm_password:
            flash('Semua kolom pendaftaran wajib diisi!', 'danger')
            return redirect(url_for('index', open_auth='register'))

        if password != confirm_password:
            flash('Konfirmasi password tidak cocok!', 'danger')
            return redirect(url_for('index', open_auth='register'))

        if len(password) < 4:
            flash('Password minimal terdiri dari 4 karakter!', 'danger')
            return redirect(url_for('index', open_auth='register'))

        conn = get_db_connection()
        existing_user = conn.execute('SELECT id FROM users WHERE email = %s', (email,)).fetchone()
        if existing_user:
            conn.close()
            flash('Email sudah terdaftar. Silakan langsung masuk!', 'danger')
            return redirect(url_for('index', open_auth='login'))

        hashed = generate_password_hash(password)
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO users (name, email, password_hash, auth_provider)
            VALUES (%s, %s, %s, 'local')
            RETURNING id
        ''', (name, email, hashed))
        user_id = cur.fetchone()['id']
        conn.commit()
        conn.close()

        session['user'] = {
            'id': user_id,
            'name': name,
            'email': email,
            'provider': 'local',
            'initial': name[0].upper() if name else 'M'
        }
        flash(f'Pendaftaran berhasil! Selamat datang di TaskMate, {name}.', 'success')
        return redirect(url_for('index'))

    return redirect(url_for('index', open_auth='register'))

@app.route('/auth/google', methods=['GET', 'POST'])
def google_auth():
    # Simulasi Google OAuth resmi 1-klik untuk workspace mahasiswa
    name = request.form.get('name') or request.args.get('name') or 'Fadlan Abdillah'
    email = request.form.get('email') or request.args.get('email') or 'fadlan@student.ac.id'

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = %s', (email,)).fetchone()
    if not user:
        dummy_hash = generate_password_hash('google_student_verified_auth')
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO users (name, email, password_hash, auth_provider)
            VALUES (%s, %s, %s, 'google')
            RETURNING id
        ''', (name, email, dummy_hash))
        user_id = cur.fetchone()['id']
        conn.commit()
    else:
        user_id = user['id']
        name = user['name']
    conn.close()

    session['user'] = {
        'id': user_id,
        'name': name,
        'email': email,
        'provider': 'google',
        'initial': name[0].upper() if name else 'G'
    }
    flash(f'Berhasil masuk dengan Akun Google ({name})!', 'success')
    return redirect(url_for('index'))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user', None)
    flash('Anda telah keluar dari workspace TaskMate.', 'info')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form.get('email', '').strip()
    if email:
        flash(f'Petunjuk reset password telah dikirim ke {email} (Simulasi).', 'info')
    else:
        flash('Mohon masukkan alamat email yang terdaftar!', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)

