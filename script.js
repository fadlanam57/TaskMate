/* ==========================================================================
   TaskMate - Personal Student Workspace Script
   Sidebar Toggle (Fixed Bug), Right Calendar Panel & Interactivity
   ========================================================================== */

// --------------------------------------------------------------------------
// 1. SIDEBAR STATE MANAGEMENT (FIX BUG: SINGLE BOOLEAN & DYNAMIC ICON)
// --------------------------------------------------------------------------

let isSidebarOpen = true;

/**
 * Sinkronisasi visual sidebar, topbar toggle button, dan ikon
 */
function updateSidebarUI() {
    const shell = document.getElementById('workspaceShell');
    const sidebar = document.getElementById('appSidebar');
    const toggleBtn = document.getElementById('topbarSidebarToggle');
    const collapseBtn = document.querySelector('.sidebar-collapse-btn');

    if (isSidebarOpen) {
        document.documentElement.classList.remove('sidebar-collapsed');
        document.body.classList.remove('sidebar-collapsed');
        if (shell) shell.classList.remove('sidebar-collapsed');
        if (sidebar) sidebar.classList.remove('is-collapsed');

        // Ikon saat sidebar TERBUKA: Close / Panah Kiri (Tutup Sidebar)
        if (toggleBtn) {
            toggleBtn.setAttribute('aria-expanded', 'true');
            toggleBtn.setAttribute('title', 'Tutup Sidebar (Ctrl+B)');
            toggleBtn.innerHTML = `
                <svg class="toggle-icon-svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            `;
        }
        if (collapseBtn) {
            collapseBtn.setAttribute('title', 'Tutup Sidebar (Ctrl+B)');
        }
    } else {
        document.documentElement.classList.add('sidebar-collapsed');
        document.body.classList.add('sidebar-collapsed');
        if (shell) shell.classList.add('sidebar-collapsed');
        if (sidebar) sidebar.classList.add('is-collapsed');

        // Ikon saat sidebar TERTUTUP: Hamburger ☰ (Buka Sidebar)
        if (toggleBtn) {
            toggleBtn.setAttribute('aria-expanded', 'false');
            toggleBtn.setAttribute('title', 'Buka Sidebar (Ctrl+B)');
            toggleBtn.innerHTML = `
                <svg class="toggle-icon-svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="3" y1="12" x2="21" y2="12"></line>
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
            `;
        }

        // Render kalender jika sidebar tertutup
        if (typeof renderCurrentCalendar === 'function') {
            renderCurrentCalendar();
        }
    }
}

/**
 * Atur status sidebar secara eksplisit
 */
function setSidebarState(isOpen, saveToStorage = true) {
    isSidebarOpen = isOpen;
    updateSidebarUI();
    if (saveToStorage) {
        localStorage.setItem('taskmate_sidebar_collapsed', isSidebarOpen ? 'false' : 'true');
    }
}

/**
 * Toggle kondisi sidebar (klik satu kali untuk tutup, klik lagi untuk buka)
 */
function toggleSidebar() {
    if (window.innerWidth <= 860) {
        toggleSidebarMobile();
    } else {
        setSidebarState(!isSidebarOpen);
    }
}

function toggleSidebarDesktop() {
    setSidebarState(!isSidebarOpen);
}

function toggleSidebarUniversal() {
    toggleSidebar();
}

/**
 * Drawer toggle untuk layar HP/Tablet
 */
function toggleSidebarMobile() {
    const sidebar = document.getElementById('appSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    if (sidebar && backdrop) {
        sidebar.classList.toggle('is-open');
        backdrop.classList.toggle('is-open');
    }
}

/**
 * Toggle kalender panel pada layar kecil (mobile/tablet)
 */
function toggleCalendarMobile() {
    const calPanel = document.getElementById('calendarPanel');
    const backdrop = document.getElementById('sidebarBackdrop');
    if (calPanel) {
        calPanel.classList.toggle('mobile-cal-open');
        if (backdrop) backdrop.classList.toggle('is-open');
        if (calPanel.classList.contains('mobile-cal-open')) {
            renderCurrentCalendar();
        }
    }
}

/**
 * Inisialisasi preferensi sidebar dari localStorage
 */
function initSidebarState() {
    if (window.innerWidth > 860) {
        const isCollapsed = localStorage.getItem('taskmate_sidebar_collapsed') === 'true';
        setSidebarState(!isCollapsed, false);
    } else {
        // Default tertutup di mobile
        isSidebarOpen = false;
        updateSidebarUI();
    }
}


// --------------------------------------------------------------------------
// 2. PANEL KALENDER KANAN & PENANDA DEADLINE
// --------------------------------------------------------------------------

const MONTH_NAMES = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
];

let calYear = 2026;
let calMonth = 8; // 8 = September (0-indexed)
let calendarTasks = [];
let tasksByDate = {}; // { '2026-09-24': [...] }

function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function loadCalendarTasks() {
    try {
        const scriptEl = document.getElementById('calendarTasksData');
        if (scriptEl && scriptEl.textContent) {
            calendarTasks = JSON.parse(scriptEl.textContent);
        }
    } catch (e) {
        console.warn('Gagal memuat calendarTasksData', e);
        calendarTasks = [];
    }

    tasksByDate = {};
    calendarTasks.forEach(task => {
        if (task.deadline) {
            const d = task.deadline.trim();
            if (!tasksByDate[d]) {
                tasksByDate[d] = [];
            }
            tasksByDate[d].push(task);
        }
    });
}

function changeCalendarMonth(delta) {
    calMonth += delta;
    if (calMonth < 0) {
        calMonth = 11;
        calYear -= 1;
    } else if (calMonth > 11) {
        calMonth = 0;
        calYear += 1;
    }
    renderCurrentCalendar();
}

function goToTodayMonth() {
    // Arahkan ke bulan September 2026 (atau bulan aktual)
    calYear = 2026;
    calMonth = 8;
    renderCurrentCalendar();
}

function renderCurrentCalendar() {
    const monthLabel = document.getElementById('calendarMonthLabel');
    const gridEl = document.getElementById('calendarDaysGrid');
    if (!monthLabel || !gridEl) return;

    monthLabel.textContent = `${MONTH_NAMES[calMonth]} ${calYear}`;
    closeCalendarPopover();

    // Hitung hari pertama dan jumlah hari
    // Konversi Minggu (0) ke hari ke-6, Senin (1) ke hari ke-0
    const firstDayIndex = new Date(calYear, calMonth, 1).getDay();
    const startingCol = (firstDayIndex === 0) ? 6 : firstDayIndex - 1;
    const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
    const daysInPrevMonth = new Date(calYear, calMonth, 0).getDate();

    // Tanggal patokan simulasi "Hari Ini": 14 September 2026
    const todayStr = '2026-09-14';

    let html = '';

    // Hari-hari dari bulan sebelumnya
    for (let i = startingCol - 1; i >= 0; i--) {
        const prevDay = daysInPrevMonth - i;
        html += `<div class="calendar-day-cell is-other-month">${prevDay}</div>`;
    }

    // Hari-hari pada bulan aktif
    for (let day = 1; day <= daysInMonth; day++) {
        const monthPad = String(calMonth + 1).padStart(2, '0');
        const dayPad = String(day).padStart(2, '0');
        const dateStr = `${calYear}-${monthPad}-${dayPad}`;

        const isToday = (dateStr === todayStr);
        const dayTasks = tasksByDate[dateStr] || [];
        const hasTasks = dayTasks.length > 0;

        let cellClasses = 'calendar-day-cell';
        if (isToday) cellClasses += ' is-today';
        if (hasTasks) cellClasses += ' has-deadline';

        // Tentukan prioritas tertinggi untuk dot penanda
        let dotHtml = '';
        if (hasTasks) {
            let hasTinggi = false;
            let hasSedang = false;
            let hasRendah = false;
            let allCompleted = true;

            dayTasks.forEach(t => {
                if (t.status !== 'Selesai') allCompleted = false;
                if (t.priority === 'Tinggi') hasTinggi = true;
                else if (t.priority === 'Sedang') hasSedang = true;
                else if (t.priority === 'Rendah') hasRendah = true;
            });

            if (allCompleted) {
                dotHtml = `<span class="cell-deadline-dot dot-selesai" title="Semua tugas selesai"></span>`;
            } else if (hasTinggi) {
                dotHtml = `<span class="cell-deadline-dot dot-tinggi" title="Tugas prioritas tinggi!"></span>`;
            } else if (hasSedang) {
                dotHtml = `<span class="cell-deadline-dot dot-sedang" title="Tugas prioritas sedang"></span>`;
            } else {
                dotHtml = `<span class="cell-deadline-dot dot-rendah" title="Tugas prioritas rendah"></span>`;
            }
        }

        const clickHandler = hasTasks
            ? `onclick="handleCalendarDateClick('${dateStr}', ${day})"`
            : `onclick="closeCalendarPopover()"`;

        const titleAttr = hasTasks ? `title="${dayTasks.length} tugas jatuh tempo"` : '';

        html += `
            <div class="${cellClasses}" data-date="${dateStr}" ${clickHandler} ${titleAttr} tabindex="0" role="button">
                <span class="cell-day-number">${day}</span>
                ${dotHtml}
            </div>
        `;
    }

    // Hari-hari pelengkap bulan berikutnya (agar kelipatan 7 baris rapi)
    const totalRendered = startingCol + daysInMonth;
    const remainingSlots = (totalRendered <= 35) ? (35 - totalRendered) : (42 - totalRendered);
    for (let nextDay = 1; nextDay <= remainingSlots; nextDay++) {
        html += `<div class="calendar-day-cell is-other-month">${nextDay}</div>`;
    }

    gridEl.innerHTML = html;
    renderUpcomingMiniWidget();
}

function handleCalendarDateClick(dateStr, dayNumber) {
    const popover = document.getElementById('calendarTaskPopover');
    const titleEl = document.getElementById('popoverDateTitle');
    const listEl = document.getElementById('popoverTaskList');
    if (!popover || !titleEl || !listEl) return;

    const tasks = tasksByDate[dateStr] || [];
    if (tasks.length === 0) {
        closeCalendarPopover();
        return;
    }

    // Tandai tanggal yang aktif dipilih
    document.querySelectorAll('.calendar-day-cell.is-selected').forEach(el => el.classList.remove('is-selected'));
    const cell = document.querySelector(`.calendar-day-cell[data-date="${dateStr}"]`);
    if (cell) cell.classList.add('is-selected');

    // Format header tanggal
    const parts = dateStr.split('-');
    const d = parseInt(parts[2], 10);
    const m = parseInt(parts[1], 10) - 1;
    const y = parts[0];
    titleEl.textContent = `${d} ${MONTH_NAMES[m]} ${y} • ${tasks.length} Tugas`;

    listEl.innerHTML = tasks.map(t => {
        const pClass = t.priority ? t.priority.toLowerCase() : 'sedang';
        const isDone = t.status === 'Selesai';
        const statusClass = t.status ? t.status.toLowerCase().replace(/\s+/g, '-') : 'belum-dikerjakan';

        return `
            <div class="popover-task-item ${isDone ? 'is-done' : ''}">
                <div class="popover-task-top">
                    <span class="popover-course-tag">${escapeHtml(t.course)}</span>
                    <span class="badge-priority-dot priority-${pClass}">
                        <span class="color-dot"></span>
                        ${t.priority}
                    </span>
                </div>
                <h5 class="popover-task-name">${escapeHtml(t.title)}</h5>
                <div class="popover-task-status-row">
                    <span class="badge-status-subtle status-${statusClass}">${t.status}</span>
                    <a href="/?q=${encodeURIComponent(t.title)}" class="popover-view-link">Lihat &rarr;</a>
                </div>
            </div>
        `;
    }).join('');

    popover.style.display = 'block';
    popover.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function closeCalendarPopover() {
    const popover = document.getElementById('calendarTaskPopover');
    if (popover) popover.style.display = 'none';
    document.querySelectorAll('.calendar-day-cell.is-selected').forEach(el => el.classList.remove('is-selected'));
}

function renderUpcomingMiniWidget() {
    const countEl = document.getElementById('calendarUpcomingCount');
    const listEl = document.getElementById('calendarUpcomingList');
    if (!listEl) return;

    // Filter tugas yang belum selesai dan urutkan berdasarkan deadline terdekat
    const pendingTasks = calendarTasks
        .filter(t => t.status !== 'Selesai' && t.deadline)
        .sort((a, b) => a.deadline.localeCompare(b.deadline))
        .slice(0, 3);

    if (countEl) {
        countEl.textContent = `${pendingTasks.length} mendesak`;
    }

    if (pendingTasks.length === 0) {
        listEl.innerHTML = `<p class="widget-empty-msg">Tidak ada tugas mendekati deadline.</p>`;
        return;
    }

    listEl.innerHTML = pendingTasks.map(t => {
        const pClass = t.priority ? t.priority.toLowerCase() : 'sedang';
        return `
            <div class="widget-task-row" onclick="handleCalendarDateClick('${t.deadline}', 0)">
                <div class="widget-task-info">
                    <span class="widget-task-title">${escapeHtml(t.title)}</span>
                    <span class="widget-task-meta">${escapeHtml(t.course)} &bull; ${t.deadline}</span>
                </div>
                <span class="badge-priority-dot priority-${pClass}">
                    <span class="color-dot"></span>
                </span>
            </div>
        `;
    }).join('');
}


// --------------------------------------------------------------------------
// 3. AUTENTIKASI: MODAL LOGIN, REGISTER & GOOGLE SIGN-IN
// --------------------------------------------------------------------------

function openAuthModal(tab = 'login') {
    openModal('authModal');
    switchAuthTab(tab);
}

function switchAuthTab(tab) {
    const loginPanel = document.getElementById('authLoginPanel');
    const registerPanel = document.getElementById('authRegisterPanel');
    const forgotPanel = document.getElementById('authForgotPanel');

    const tabBtnLogin = document.getElementById('tabBtnLogin');
    const tabBtnRegister = document.getElementById('tabBtnRegister');
    const modalTitle = document.getElementById('authModalTitle');
    const modalSubtitle = document.getElementById('authModalSubtitle');
    const tabsNav = document.querySelector('.auth-tabs-nav');

    if (loginPanel) {
        loginPanel.classList.remove('is-active');
        loginPanel.style.display = 'none';
    }
    if (registerPanel) {
        registerPanel.classList.remove('is-active');
        registerPanel.style.display = 'none';
    }
    if (forgotPanel) {
        forgotPanel.classList.remove('is-active');
        forgotPanel.style.display = 'none';
    }

    if (tabsNav) tabsNav.style.display = 'flex';
    if (tabBtnLogin) tabBtnLogin.classList.remove('is-active');
    if (tabBtnRegister) tabBtnRegister.classList.remove('is-active');

    if (tab === 'login') {
        if (loginPanel) {
            loginPanel.style.display = 'block';
            loginPanel.classList.add('is-active');
        }
        if (tabBtnLogin) tabBtnLogin.classList.add('is-active');
        if (modalTitle) modalTitle.textContent = 'Masuk ke TaskMate';
        if (modalSubtitle) modalSubtitle.textContent = 'Workspace manajemen tugas kuliah mahasiswa';

        setTimeout(() => {
            const emailInput = document.getElementById('loginEmail');
            if (emailInput) emailInput.focus();
        }, 100);

    } else if (tab === 'register') {
        if (registerPanel) {
            registerPanel.style.display = 'block';
            registerPanel.classList.add('is-active');
        }
        if (tabBtnRegister) tabBtnRegister.classList.add('is-active');
        if (modalTitle) modalTitle.textContent = 'Daftar Akun Mahasiswa';
        if (modalSubtitle) modalSubtitle.textContent = 'Mulai atur seluruh jadwal tugas semester ini';

        setTimeout(() => {
            const nameInput = document.getElementById('regName');
            if (nameInput) nameInput.focus();
        }, 100);

    } else if (tab === 'forgot') {
        if (forgotPanel) {
            forgotPanel.style.display = 'block';
            forgotPanel.classList.add('is-active');
        }
        if (tabsNav) tabsNav.style.display = 'none';
        if (modalTitle) modalTitle.textContent = 'Pemulihan Kata Sandi';
        if (modalSubtitle) modalSubtitle.textContent = 'Masukkan email akun TaskMate Anda';

        setTimeout(() => {
            const forgotEmail = document.getElementById('forgotEmail');
            if (forgotEmail) forgotEmail.focus();
        }, 100);
    }
}

function openForgotPasswordPrompt() {
    switchAuthTab('forgot');
}


// --------------------------------------------------------------------------
// 4. MODAL GENERAL HELPERS
// --------------------------------------------------------------------------

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';

        const firstInput = modal.querySelector('input:not([type="hidden"]), select, textarea');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 80);
        }
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

function handleModalBackdropClick(event, modalId) {
    if (event.target.id === modalId) {
        closeModal(modalId);
    }
}


// --------------------------------------------------------------------------
// 5. KEYBOARD SHORTCUTS & EVENT LISTENERS
// --------------------------------------------------------------------------

document.addEventListener('keydown', function (e) {
    // 1. ESC: Tutup modal atau sidebar mobile
    if (e.key === 'Escape') {
        const activeModal = document.querySelector('.modal-backdrop-layer.active');
        if (activeModal) {
            closeModal(activeModal.id);
        }

        const sidebar = document.getElementById('appSidebar');
        const calPanel = document.getElementById('calendarPanel');
        const backdrop = document.getElementById('sidebarBackdrop');

        if (sidebar && sidebar.classList.contains('is-open')) {
            sidebar.classList.remove('is-open');
            if (backdrop) backdrop.classList.remove('is-open');
        }

        if (calPanel && calPanel.classList.contains('mobile-cal-open')) {
            calPanel.classList.remove('mobile-cal-open');
            if (backdrop) backdrop.classList.remove('is-open');
        }

        closeCalendarPopover();
    }

    // 2. Ctrl + B atau Cmd + B: Toggle Sidebar
    if ((e.ctrlKey || e.metaKey) && (e.key === 'b' || e.key === 'B')) {
        const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
        if (activeTag !== 'input' && activeTag !== 'textarea') {
            e.preventDefault();
            toggleSidebar();
        }
    }
});


// --------------------------------------------------------------------------
// 6. DOM READY INITIALIZATION
// --------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', function () {
    // 1. Inisialisasi data tugas kalender
    loadCalendarTasks();

    // 2. Inisialisasi status sidebar dari localStorage
    initSidebarState();

    // 3. Render kalender bulan September 2026
    renderCurrentCalendar();

    // 4. Deteksi parameter URL ?open_auth=login atau ?open_auth=register
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('open_auth')) {
        const authType = urlParams.get('open_auth');
        openAuthModal(authType === 'register' ? 'register' : 'login');
    }

    // 5. Auto-dismiss Toast Notifications
    const toasts = document.querySelectorAll('.toast-item, .toast-card');
    toasts.forEach(toast => {
        setTimeout(() => {
            toast.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-6px) scale(0.96)';
            setTimeout(() => toast.remove(), 350);
        }, 4500);
    });

    // 6. Set minimal tanggal deadline ke hari ini untuk form penambahan tugas
    const deadlineInput = document.getElementById('deadline');
    if (deadlineInput && !deadlineInput.value) {
        const today = new Date().toISOString().split('T')[0];
        deadlineInput.min = today;
    }
});
