import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json
import random
import re
import io
import os
import base64
import streamlit.components.v1 as components

# ---------------------------------------------------------
# Jalali / Shamsi Date Conversion Helper (Pure Python)
# ---------------------------------------------------------
def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy if gm > 2 else gy - 1
    days = 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 - 80 + gd + g_d_m[gm - 1]
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return f"{jy:04d}/{jm:02d}/{jd:02d}"

def get_current_shamsi_date():
    today = datetime.date.today()
    return gregorian_to_jalali(today.year, today.month, today.day)

# ---------------------------------------------------------
# Page Configuration & RTL CSS Styling (Protected Icons)
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="auto"
)

# Custom Persian / RTL CSS Styling (Clean, Bulletproof, No Icon Corruption)
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    /* Target only text containers, NOT icon fonts */
    .stApp, .stMarkdown, p, h1, h2, h3, h4, h5, h6, input, select, textarea, button, label {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #ffffff !important;
    }
    
    /* Header Banner */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: #ffffff !important;
        padding: 22px;
        border-radius: 16px;
        text-align: center !important;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .main-header h2, .main-header p {
        color: #ffffff !important;
        text-align: center !important;
    }
    
    /* Card Styling */
    .card-box {
        background: rgba(30, 41, 59, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    /* Quote Box */
    .quote-card {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.6) 0%, rgba(30, 41, 59, 0.9) 100%);
        border-right: 6px solid #fbbf24;
        border-left: 1px solid rgba(255, 255, 255, 0.1);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding: 22px;
        border-radius: 14px;
        margin-bottom: 22px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.25);
    }
    
    /* Buttons */
    .stButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        padding: 10px 18px !important;
        font-weight: bold !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(37, 99, 235, 0.4) !important;
    }
    
    /* Popover Styling */
    div[data-baseweb="popover"], div[data-baseweb="popover"] * {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Database Initialization & Auto Schema Migration (Liara Compatible)
# ---------------------------------------------------------
DB_NAME = "class_management.db"
_app_dir = os.path.dirname(os.path.abspath(__file__))
_local_db = os.path.join(_app_dir, DB_NAME)

try:
    _test_file = os.path.join(_app_dir, ".perm_test")
    with open(_test_file, "w") as _f:
        _f.write("1")
    os.remove(_test_file)
    DB_FILE = _local_db
except Exception:
    DB_FILE = os.path.join(tempfile.gettempdir(), DB_NAME)

def get_connection():
    _dir = os.path.dirname(DB_FILE)
    if _dir and not os.path.exists(_dir):
        os.makedirs(_dir, exist_ok=True)
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Students Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            last_family_name TEXT,
            national_id TEXT,
            national_code TEXT,
            pin_code TEXT DEFAULT '1234',
            parent_phone TEXT,
            student_group TEXT DEFAULT 'گروه عمومی',
            notes TEXT,
            created_at TEXT
        )
        """)
        
        # 2. Evaluations Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT NOT NULL,
            level TEXT,
            grade_level TEXT,
            feedback TEXT,
            description TEXT,
            eval_date TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        
        # 3. Behaviors Table (Primary)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS behaviors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            behavior_type TEXT,
            title TEXT,
            description TEXT,
            log_date TEXT,
            score INTEGER DEFAULT 5,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        
        # 4. Behavior Logs Table (Alias/Backup for backwards compatibility)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS behavior_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            behavior_type TEXT,
            title TEXT,
            description TEXT,
            log_date TEXT,
            score INTEGER DEFAULT 5,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        
        # 5. Quizzes Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            duration_minutes INTEGER DEFAULT 15,
            is_active INTEGER DEFAULT 1,
            created_at TEXT
        )
        """)
        
        # 6. Questions Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question_type TEXT DEFAULT 'mcq',
            question_text TEXT NOT NULL,
            option_1 TEXT,
            option_2 TEXT,
            option_3 TEXT,
            option_4 TEXT,
            correct_option INTEGER DEFAULT 1,
            model_answer TEXT,
            explanation TEXT,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
        )
        """)
        
        # 7. Quiz Results Table (Primary)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            student_id INTEGER,
            score REAL,
            total_questions INTEGER,
            percentage REAL,
            photo_data TEXT,
            essay_answers TEXT,
            submitted_at TEXT,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        
        # 8. Quiz Submissions Table (Alias/Backup)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            student_id INTEGER,
            score REAL,
            total_questions INTEGER,
            percentage REAL,
            photo_data TEXT,
            essay_answers TEXT,
            submitted_at TEXT,
            submission_date TEXT,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        
        # 9. Teacher Auth Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_auth (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            password TEXT NOT NULL
        )
        """)
        cursor.execute("INSERT OR IGNORE INTO teacher_auth (id, password) VALUES (1, '1234')")
        
        # Robust Column Migrations (Failsafe for existing databases)
        migrations = [
            ("students", "last_family_name", "TEXT"),
            ("students", "national_id", "TEXT"),
            ("students", "national_code", "TEXT"),
            ("students", "pin_code", "TEXT DEFAULT '1234'"),
            ("students", "student_group", "TEXT DEFAULT 'گروه عمومی'"),
            ("evaluations", "grade_level", "TEXT"),
            ("evaluations", "description", "TEXT"),
            ("behaviors", "score", "INTEGER DEFAULT 5"),
            ("behavior_logs", "title", "TEXT"),
            ("behavior_logs", "score", "INTEGER DEFAULT 5"),
            ("quiz_results", "photo_data", "TEXT"),
            ("quiz_results", "essay_answers", "TEXT"),
            ("quiz_submissions", "photo_data", "TEXT"),
            ("quiz_submissions", "essay_answers", "TEXT")
        ]
        
        for table, col, col_type in migrations:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass
                
        conn.commit()

init_db()

# Safe Read Helper
def safe_read_sql(query, conn, params=None):
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception:
        return pd.DataFrame()

def safe_count(conn, table_name, student_id):
    try:
        res = conn.execute(f"SELECT COUNT(*) FROM {table_name} WHERE student_id = ?", (student_id,)).fetchone()
        return res[0] if res else 0
    except Exception:
        return 0

def safe_avg(conn, table_name, col_name, student_id):
    try:
        res = conn.execute(f"SELECT AVG({col_name}) FROM {table_name} WHERE student_id = ?", (student_id,)).fetchone()
        return res[0] if res and res[0] is not None else None
    except Exception:
        return None

# Safe String Helper
def safe_str(val, default=''):
    if pd.isna(val) or val is None or str(val).strip() in ['None', 'nan', 'NaN', '']:
        return default
    return str(val).strip()

def load_students():
    init_db()
    with get_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(students)")
            cols = [r[1] for r in cursor.fetchall()]
            
            ln_col = "last_family_name" if "last_family_name" in cols else ("last_name" if "last_name" in cols else "last_family_name")
            nc_col = "national_code" if "national_code" in cols else ("national_id" if "national_id" in cols else "national_code")
            
            df = pd.read_sql_query(f"SELECT *, {ln_col} AS last_family_name, {nc_col} AS national_code FROM students ORDER BY id ASC", conn)
            df = df.loc[:, ~df.columns.duplicated()]
            
            if not df.empty:
                df['first_name'] = df['first_name'].apply(lambda x: safe_str(x, 'دانش‌آموز'))
                df['last_family_name'] = df['last_family_name'].apply(lambda x: safe_str(x, ''))
                df['last_name'] = df['last_family_name']
                df['full_name'] = df.apply(lambda r: f"{r['first_name']} {r['last_family_name']}".strip(), axis=1)
                df['national_code'] = df['national_code'].apply(lambda x: safe_str(x, 'ثبت نشده'))
                df['national_id'] = df['national_code']
                df['parent_phone'] = df['parent_phone'].apply(lambda x: safe_str(x, 'ثبت نشده'))
                df['student_group'] = df['student_group'].apply(lambda x: safe_str(x, 'گروه عمومی'))
                df['pin_code'] = df['pin_code'].apply(lambda x: safe_str(x, '1234'))
            else:
                df = pd.DataFrame(columns=['id', 'national_code', 'national_id', 'first_name', 'last_family_name', 'last_name', 'full_name', 'parent_phone', 'notes', 'student_group', 'pin_code'])
                
            return df
        except Exception:
            return pd.DataFrame(columns=['id', 'national_code', 'national_id', 'first_name', 'last_family_name', 'last_name', 'full_name', 'parent_phone', 'notes', 'student_group', 'pin_code'])

# ---------------------------------------------------------
# ReportLab Persian PDF Helper (100% Native, Fast, Failsafe)
# ---------------------------------------------------------
PERSIAN_MAP = {
    'ا': ('ﺍ', 'ﺎ', 'ﺎ', 'ﺍ'), 'ب': ('ﺏ', 'ﺑ', 'ﺒ', 'ﺐ'), 'پ': ('ﭖ', 'ﭘ', 'ﭙ', 'ﭗ'),
    'ت': ('ﺕ', 'ﺗ', 'ﺘ', 'ﺖ'), 'ث': ('ﺙ', 'ﺙ', 'ﺜ', 'ﺚ'), 'ج': ('ﺝ', 'ﺟ', 'ﺠ', 'ﺞ'),
    'چ': ('ﭺ', 'ﭼ', 'ﭽ', 'ﭻ'), 'ح': ('ﺡ', 'ﺣ', 'ﺤ', 'ﺢ'), 'خ': ('ﺥ', 'ﺧ', 'ﺨ', 'ﺦ'),
    'د': ('ﺩ', 'ﺪ', 'ﺪ', 'ﺩ'), 'ذ': ('ﺫ', 'ﺬ', 'ﺬ', 'ﺫ'), 'ر': ('ﺭ', 'ﺮ', 'ﺮ', 'ﺭ'),
    'ز': ('ﺯ', 'ﺰ', 'ﺰ', 'ﺯ'), 'ژ': ('ﮊ', 'ﮋ', 'ﮋ', 'ﮊ'), 'س': ('ﺱ', 'ﺱ', 'ﺴ', 'ﺲ'),
    'ش': ('ﺵ', 'ﺷ', 'ﺸ', 'ﺶ'), 'ص': ('ﺹ', 'ﺻ', 'ﺼ', 'ﺺ'), 'ض': ('ﺽ', 'ﺿ', 'ﻀ', 'ﺾ'),
    'ط': ('ﻁ', 'ﻃ', 'ﻄ', 'ﻂ'), 'ظ': ('ﻅ', 'ﻇ', 'ﻈ', 'ﻆ'), 'ع': ('ﻉ', 'ﻋ', 'ﻌ', 'ﻊ'),
    'غ': ('ﻍ', 'ﻏ', 'ﻐ', 'ﻎ'), 'ف': ('ﻑ', 'ﻓ', 'ف', 'ﻒ'), 'ق': ('ﻕ', 'ﻗ', 'ﻖ', 'ﻖ'),
    'ک': ('ﮎ', 'ﻛ', 'ﻜ', 'ﮏ'), 'گ': ('ﮒ', 'ﮔ', 'ﮕ', 'ﮓ'), 'ل': ('ﻝ', 'ﻟ', 'ﻠ', 'ﻞ'),
    'م': ('ﻡ', 'ﻣ', 'ﻤ', 'ﻢ'), 'ن': ('ﻥ', 'ﻥ', 'ﻨ', 'ﻦ'), 'و': ('ﻭ', 'ﻮ', 'ﻮ', 'ﻭ'),
    'ه': ('ﻩ', 'ﻫ', 'ﻬ', 'ﻪ'), 'ی': ('ﯼ', 'ﻳ', 'ﻴ', 'ﯽ'), 'آ': ('ﺁ', 'ﺂ', 'ﺂ', 'ﺁ'),
    'ئ': ('ﺉ', 'ﺋ', 'ﺌ', 'ﺊ'), 'ء': ('ﺀ', 'ء', 'ء', 'ﺀ'),
}
NON_CONNECTING = set('ادذرزژوآ')

def _reshape(text):
    res = []
    n = len(text)
    for i, ch in enumerate(text):
        if ch not in PERSIAN_MAP:
            res.append(ch)
            continue
        prev_ch = text[i-1] if i > 0 else None
        next_ch = text[i+1] if i < n-1 else None
        prev_conn = prev_ch in PERSIAN_MAP and prev_ch not in NON_CONNECTING
        next_conn = next_ch in PERSIAN_MAP
        iso, init, med, fin = PERSIAN_MAP[ch]
        if prev_conn and next_conn: res.append(med)
        elif prev_conn and not next_conn: res.append(fin)
        elif not prev_conn and next_conn: res.append(init)
        else: res.append(iso)
    return ''.join(res)

def _rtl(text):
    if not text: return ''
    return _reshape(str(text))[::-1]

_PERSIAN_FONT_REGISTERED = False
def _register_persian_font():
    global _PERSIAN_FONT_REGISTERED
    if not _PERSIAN_FONT_REGISTERED:
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            font_paths = [
                '/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf',
                '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            ]
            for fp in font_paths:
                if os.path.exists(fp):
                    try:
                        pdfmetrics.registerFont(TTFont('PersianFont', fp))
                        _PERSIAN_FONT_REGISTERED = True
                        break
                    except Exception:
                        pass
        except Exception:
            pass

def draw_pdf_header(c, w, h, doc_title, letter_no, letter_date):
    from reportlab.lib import colors
    c.setFillColor(colors.HexColor('#1e3a8a'))
    c.rect(0, h-95, w, 95, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#ffffff'))
    c.setFont('PersianFont', 11)
    c.drawCentredString(w/2, h-22, _rtl('باسمه تعالی'))
    c.setFont('PersianFont', 12)
    c.drawCentredString(w/2, h-40, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
    c.setFont('PersianFont', 10)
    c.drawCentredString(w/2, h-58, _rtl('اداره کل آموزش و پرورش استان ایلام - مدیریت آموزش و پرورش شهرستان مهران'))
    c.setFont('PersianFont', 12)
    c.drawCentredString(w/2, h-80, _rtl('دبستان پسرانه شهید مطهری مهران — سال تحصیلی ۱۴۰۴-۱۴۰۵'))
    c.setFillColor(colors.HexColor('#0f172a'))
    c.setFont('PersianFont', 9)
    c.drawRightString(140, h-110, _rtl(f'تاریخ: {letter_date}'))
    c.drawRightString(140, h-125, _rtl(f'شماره: {letter_no}'))
    c.drawRightString(140, h-140, _rtl('پیوست: دارد'))

def generate_behavior_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        _register_persian_font()
        
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        is_pos = 'مثبت' in b_type or 'تشویق' in b_type
        doc_title = 'تقدیرنامه و لوح سپاس انضباطی' if is_pos else 'کارت اطلاع‌رسانی و هشدار انضباطی أولیا'
        letter_no = f'۱۰۱/ب/{random.randint(100, 999)}'
        
        draw_pdf_header(c, w, h, doc_title, letter_no, log_date)
        
        y = h - 165
        theme_hex = '#15803d' if is_pos else '#b91c1c'
        c.setFillColor(colors.HexColor(theme_hex))
        c.rect(40, y-35, w-80, 35, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont('PersianFont', 13)
        c.drawCentredString(w/2, y-23, _rtl(doc_title))
        
        y -= 55
        c.setFillColor(colors.HexColor('#f8fafc'))
        c.rect(40, y-45, w-80, 45, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont('PersianFont', 10)
        c.drawRightString(w - 55, y - 25, _rtl(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 230, y - 25, _rtl(f'کد ملی: {national_id}'))
        c.drawRightString(w - 400, y - 25, _rtl(f'گروه کلاسی: {student_group}'))
        
        y -= 65
        c.setFillColor(colors.HexColor('#f1f5f9'))
        c.rect(40, y-160, w-80, 160, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont('PersianFont', 10)
        
        intro_text = f'ولی محترم دانش‌آموز گرامی {student_name}؛'
        msg_text = 'بدین‌وسیله گزارش عملکرد و پایش رفتاری فرزندتان در کلاس درس تقدیم می‌گردد:' if not is_pos else 'بدین‌وسیله از انضباط عالی، مسئولیت‌پذیری و رفتار شایسته فرزندتان قدردانی می‌گردد:'
        
        c.drawRightString(w - 55, y - 25, _rtl(intro_text))
        c.drawRightString(w - 55, y - 45, _rtl(msg_text))
        
        c.setFont('PersianFont', 11)
        c.drawRightString(w - 55, y - 75, _rtl(f'📌 عنوان مشاهده رفتاری: {title}'))
        c.setFont('PersianFont', 10)
        c.drawRightString(w - 55, y - 100, _rtl(f'📝 شرح و توصیفات تکمیلی آموزگار: {desc[:80]}'))
        if len(desc) > 80:
            c.drawRightString(w - 55, y - 120, _rtl(desc[80:160]))
            
        y -= 210
        c.setFont('PersianFont', 10)
        c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 30, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
        
        c.save()
        return buf.getvalue()
    except Exception as e:
        return f"Error creating PDF: {e}".encode('utf-8')

def generate_exams_pdf(student_name, national_id, student_group, quiz_list, quiz_avg_str, letter_date):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        _register_persian_font()
        
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        doc_title = 'گزارش تحلیلی و کارنامه آزمون‌های آنلاین'
        letter_no = f'۱۰۲/آ/{random.randint(100, 999)}'
        
        draw_pdf_header(c, w, h, doc_title, letter_no, letter_date)
        
        y = h - 165
        c.setFillColor(colors.HexColor('#0f172a'))
        c.rect(40, y-35, w-80, 35, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont('PersianFont', 13)
        c.drawCentredString(w/2, y-23, _rtl(doc_title))
        
        y -= 55
        c.setFillColor(colors.HexColor('#f8fafc'))
        c.rect(40, y-45, w-80, 45, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont('PersianFont', 10)
        c.drawRightString(w - 55, y - 25, _rtl(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 230, y - 25, _rtl(f'کد ملی: {national_id}'))
        c.drawRightString(w - 400, y - 25, _rtl(f'میانگین آزمون‌ها: {quiz_avg_str}'))
        
        y -= 65
        c.setFont('PersianFont', 10)
        c.drawRightString(w - 55, y, _rtl('📊 جدول سوابق آزمون‌های آنلاین شرکت‌شده:'))
        
        y -= 25
        c.setFillColor(colors.HexColor('#1e3a8a'))
        c.rect(40, y-20, w-80, 20, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont('PersianFont', 9)
        c.drawCentredString(70, y-14, _rtl('درصد ٪'))
        c.drawCentredString(140, y-14, _rtl('نمره تستی'))
        c.drawCentredString(230, y-14, _rtl('درس'))
        c.drawCentredString(380, y-14, _rtl('عنوان آزمون'))
        
        y -= 20
        c.setFillColor(colors.HexColor('#0f172a'))
        for q in quiz_list[:8]:
            c.setFont('PersianFont', 8)
            pct = f"{q.get('درصد ٪', 0):.1f}٪"
            sc = f"{q.get('نمره تستی', 0)} از {q.get('کل سوالات تستی', 0)}"
            sb = str(q.get('درس', ''))
            ttl = str(q.get('عنوان آزمون', ''))
            
            c.rect(40, y-20, w-80, 20, fill=0, stroke=1)
            c.drawCentredString(70, y-14, _rtl(pct))
            c.drawCentredString(140, y-14, _rtl(sc))
            c.drawCentredString(230, y-14, _rtl(sb))
            c.drawCentredString(380, y-14, _rtl(ttl))
            y -= 20
            
        y -= 40
        c.setFont('PersianFont', 10)
        c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 30, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
        
        c.save()
        return buf.getvalue()
    except Exception as e:
        return f"Error creating PDF: {e}".encode('utf-8')

def generate_portfolio_pdf(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str, letter_date):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        _register_persian_font()
        
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        doc_title = 'کارنامه جامع تحصیلی و پوشه کار دیجیتال دانش‌آموز'
        letter_no = f'۱۰۳/ک/{random.randint(100, 999)}'
        
        draw_pdf_header(c, w, h, doc_title, letter_no, letter_date)
        
        y = h - 165
        c.setFillColor(colors.HexColor('#0f172a'))
        c.rect(40, y-35, w-80, 35, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont('PersianFont', 13)
        c.drawCentredString(w/2, y-23, _rtl(doc_title))
        
        y -= 55
        c.setFillColor(colors.HexColor('#f8fafc'))
        c.rect(40, y-45, w-80, 45, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont('PersianFont', 10)
        c.drawRightString(w - 55, y - 18, _rtl(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 230, y - 18, _rtl(f'کد ملی: {national_id}'))
        c.drawRightString(w - 400, y - 18, _rtl(f'گروه کلاسی: {student_group}'))
        c.drawRightString(w - 55, y - 36, _rtl(f'ارزشیابی‌ها: {eval_count} | موارد رفتاری: {beh_count} | میانگین آزمون‌ها: {quiz_avg_str}'))
        
        y -= 65
        c.setFillColor(colors.HexColor('#f1f5f9'))
        c.rect(40, y-190, w-80, 190, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont('PersianFont', 10)
        
        l1 = f'ولی محترم دانش‌آموز گرامی {student_name}؛'
        l2 = 'با سلام و اهدای تحیت؛'
        l3 = 'بدین‌وسیله گزارش جامع عملکرد تحصیلی، ارزشیابی کیفی-توصیفی ۷ عنوان درسی پایه پنجم،'
        l4 = 'نتایج آزمون‌های آنلاین و سوابق پایش رفتاری فرزندتان در دبستان شهید مطهری مهران جهت اطلاع'
        l5 = 'و آگاهی کامل حضورفرمایتان تقدیم می‌گردد. این پرونده انعکاس‌دهنده تلاش‌های علمی و انضباطی'
        l6 = 'دانش‌آموز می‌باشد. خواهشمند است پس از ملاحظه سوابق، فرم ذیل را تایید فرمایید.'
        
        c.drawRightString(w - 55, y - 25, _rtl(l1))
        c.drawRightString(w - 55, y - 45, _rtl(l2))
        c.drawRightString(w - 55, y - 70, _rtl(l3))
        c.drawRightString(w - 55, y - 90, _rtl(l4))
        c.drawRightString(w - 55, y - 110, _rtl(l5))
        c.drawRightString(w - 55, y - 130, _rtl(l6))
        
        c.setFont('PersianFont', 11)
        c.drawRightString(w - 55, y - 160, _rtl('💡 تحلیل آموزشی و توصیه‌های تربیتی آموزگار (سید موسی حیدری):'))
        c.setFont('PersianFont', 9)
        c.drawRightString(w - 55, y - 180, _rtl('حضور منظم، مشارکت فعال در فعالیت‌های گروهی کلاسی و رشد مستمر نمرات آزمون‌ها.'))
        
        y -= 240
        c.setFont('PersianFont', 10)
        c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 30, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
        
        c.save()
        return buf.getvalue()
    except Exception as e:
        return f"Error creating PDF: {e}".encode('utf-8')

# ---------------------------------------------------------
# HTML Report Generator Helpers (For Preview in Iframe)
# ---------------------------------------------------------
def generate_behavior_report_html(student_name, national_id, student_group, b_type, title, desc, log_date, letter_no):
    is_pos = 'مثبت' in b_type or 'تشویق' in b_type
    theme_color = '#15803d' if is_pos else '#b91c1c'
    bg_color = '#f0fdf4' if is_pos else '#fef2f2'
    border_color = '#22c55e' if is_pos else '#ef4444'
    report_title = 'تقدیرنامه و لوح سپاس انضباطی کلاسی' if is_pos else 'کارت اطلاع‌رسانی و هشدار انضباطی اولیا'
    
    return f"""
    <div style="direction: rtl; text-align: right; font-family: Tahoma, sans-serif; background: {bg_color}; border: 2px solid {border_color}; border-radius: 12px; padding: 20px; color: #0f172a; margin-bottom: 15px;">
        <div style="border-bottom: 2px solid {theme_color}; padding-bottom: 10px; margin-bottom: 15px; text-align: center;">
            <div style="color: #1e3a8a; font-weight: bold; font-size: 0.9rem;">جمهوری اسلامی ایران - وزارت آموزش و پرورش</div>
            <div style="color: #0f172a; font-size: 1.1rem; font-weight: bold; margin-top: 4px;">دبستان پسرانه شهید مطهری مهران</div>
            <div style="color: {theme_color}; font-size: 1.2rem; font-weight: bold; margin-top: 8px;">{report_title}</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">شماره: {letter_no} | تاریخ: {log_date}</div>
        </div>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 0.9rem; background: #ffffff; border-radius: 8px;">
            <tr>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>دانش‌آموز:</b> {student_name}</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>کد ملی:</b> {national_id}</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>گروه:</b> {student_group}</td>
            </tr>
        </table>
        <div style="background: #ffffff; padding: 12px; border-radius: 8px; border-right: 4px solid {theme_color}; font-size: 0.95rem; line-height: 1.8;">
            <b>📌 عنوان مشاهده رفتاری:</b> {title}<br>
            <b>📝 توضیحات آموزگار:</b> {desc}
        </div>
        <div style="margin-top: 25px; display: flex; justify-content: space-between; text-align: center; font-size: 0.85rem; font-weight: bold;">
            <div>آموزگار پایه پنجم: سید موسی حیدری</div>
            <div>مدیریت دبستان شهید مطهری مهران</div>
        </div>
    </div>
    """

def generate_exams_report_html(student_name, national_id, student_group, quiz_list, quiz_avg_str, letter_date, letter_no):
    rows_html = ""
    for q in quiz_list:
        rows_html += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #cbd5e1; text-align: center;">{q.get('عنوان آزمون', '')}</td>
            <td style="padding: 8px; border: 1px solid #cbd5e1; text-align: center;">{q.get('درس', '')}</td>
            <td style="padding: 8px; border: 1px solid #cbd5e1; text-align: center;">{q.get('نمره تستی', 0)} از {q.get('کل سوالات تستی', 0)}</td>
            <td style="padding: 8px; border: 1px solid #cbd5e1; text-align: center; font-weight: bold; color: #2563eb;">{q.get('درصد ٪', 0):.1f}٪</td>
        </tr>
        """
    if not rows_html:
        rows_html = "<tr><td colspan='4' style='text-align: center; padding: 10px;'>آزمونی ثبت نشده است.</td></tr>"
        
    return f"""
    <div style="direction: rtl; text-align: right; font-family: Tahoma, sans-serif; background: #f8fafc; border: 2px solid #3b82f6; border-radius: 12px; padding: 20px; color: #0f172a; margin-bottom: 15px;">
        <div style="border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; margin-bottom: 15px; text-align: center;">
            <div style="color: #1e3a8a; font-weight: bold; font-size: 0.9rem;">جمهوری اسلامی ایران - وزارت آموزش و پرورش</div>
            <div style="color: #0f172a; font-size: 1.1rem; font-weight: bold; margin-top: 4px;">دبستان پسرانه شهید مطهری مهران</div>
            <div style="color: #2563eb; font-size: 1.2rem; font-weight: bold; margin-top: 8px;">گزارش تحلیلی و کارنامه آزمون‌های آنلاین</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">شماره: {letter_no} | تاریخ: {letter_date}</div>
        </div>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 0.9rem; background: #ffffff;">
            <tr>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>دانش‌آموز:</b> {student_name}</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>کد ملی:</b> {national_id}</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>میانگین نمرات:</b> {quiz_avg_str}</td>
            </tr>
        </table>
        <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; background: #ffffff;">
            <tr style="background: #1e3a8a; color: #ffffff;">
                <th style="padding: 8px; border: 1px solid #1e3a8a;">عنوان آزمون</th>
                <th style="padding: 8px; border: 1px solid #1e3a8a;">درس</th>
                <th style="padding: 8px; border: 1px solid #1e3a8a;">نمره تستی</th>
                <th style="padding: 8px; border: 1px solid #1e3a8a;">درصد ٪</th>
            </tr>
            {rows_html}
        </table>
    </div>
    """

def generate_portfolio_report_html(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str, letter_date, letter_no):
    return f"""
    <div style="direction: rtl; text-align: right; font-family: Tahoma, sans-serif; background: #f8fafc; border: 2px solid #0f172a; border-radius: 12px; padding: 20px; color: #0f172a; margin-bottom: 15px;">
        <div style="border-bottom: 2px solid #0f172a; padding-bottom: 10px; margin-bottom: 15px; text-align: center;">
            <div style="color: #1e3a8a; font-weight: bold; font-size: 0.9rem;">جمهوری اسلامی ایران - وزارت آموزش و پرورش</div>
            <div style="color: #0f172a; font-size: 1.15rem; font-weight: bold; margin-top: 4px;">دبستان پسرانه شهید مطهری مهران</div>
            <div style="color: #0f172a; font-size: 1.25rem; font-weight: bold; margin-top: 8px;">کارنامه جامع تحصیلی و پوشه کار دیجیتال دانش‌آموز</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">شماره: {letter_no} | تاریخ: {letter_date}</div>
        </div>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 0.9rem; background: #ffffff;">
            <tr>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>نام دانش‌آموز:</b> {student_name}</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>کد ملی:</b> {national_id}</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>گروه:</b> {student_group}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>ارزشیابی‌ها:</b> {eval_count} مورد</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>موارد رفتاری:</b> {beh_count} مورد</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>میانگین آزمون‌ها:</b> {quiz_avg_str}</td>
            </tr>
        </table>
        <div style="background: #eff6ff; border: 1px solid #3b82f6; padding: 12px; border-radius: 8px; font-size: 0.9rem; line-height: 1.8;">
            <b>💡 تحلیل آموزشی و توصیه‌های تربیتی آموزگار (سید موسی حیدری):</b><br>
            حضور منظم، مشارکت فعال در فعالیت‌های گروهی کلاسی و رشد مستمر نمرات در آزمون‌های آنلاین.
        </div>
        <div style="margin-top: 25px; display: flex; justify-content: space-between; text-align: center; font-size: 0.85rem; font-weight: bold;">
            <div>آموزگار پایه پنجم: سید موسی حیدری</div>
            <div>مدیریت دبستان شهید مطهری مهران</div>
            <div>رویت و امضای اولیای محترم</div>
        </div>
    </div>
    """

# Helper Constants
FIFTH_GRADE_SUBJECTS = [
    "ریاضی",
    "علوم تجربی",
    "فارسی (خوانداری)",
    "نگارش فارسی",
    "مطالعات اجتماعی",
    "هدیه‌های آسمان",
    "آموزش قرآن"
]

EVALUATION_LEVELS = [
    "خیلی خوب 🌟",
    "خوب 🟢",
    "قابل قبول 🟡",
    "نیاز به تلاش مجدد 🔴"
]

CLASS_GROUPS = [
    "گروه ارمغان 🚀",
    "گروه دانا 💡",
    "گروه تلاش 🌟",
    "گروه نخبگان 🏆",
    "گروه اندیشه 📖"
]

# Session State Setup
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = 'دانش‌آموز'
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False
if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 0
if 'show_welcome_page' not in st.session_state:
    st.session_state['show_welcome_page'] = True

def check_teacher_password(pwd):
    with get_connection() as conn:
        res = conn.execute("SELECT password FROM teacher_auth WHERE id = 1").fetchone()
        return res['password'] == pwd if res else pwd == '1234'

def update_teacher_password(new_pwd):
    with get_connection() as conn:
        conn.execute("UPDATE teacher_auth SET password = ? WHERE id = 1", (new_pwd,))
        conn.commit()

# ---------------------------------------------------------
# WELCOME SPLASH PAGE (صفحه خوش‌آمدگویی پیش از ورود)
# ---------------------------------------------------------
if st.session_state['show_welcome_page']:
    st.markdown("""
    <div class="main-header">
        <h2>🌸 به سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی خوش آمدید 🌸</h2>
        <p style="font-size: 1.1rem; font-weight: bold; margin-top: 8px;">🏫 دبستان پسرانه شهید مطهری مهران — سال تحصیلی ۱۴۰۴-۱۴۰۵</p>
        <p style="font-size: 1rem; opacity: 0.9;">طراح و آموزگار پایه پنجم: <b>سید موسی حیدری</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="quote-card">
        <h3 style="color: #fbbf24 !important; margin-bottom: 12px; font-size: 1.1rem;">📜 رهنمودهای مقام معظم رهبری (حضرت آیت‌الله خامنه‌ای مدظله‌العالی) در باب فناوری و آموزش:</h3>
        <p style="font-size: 1.05rem; line-height: 1.9; text-align: justify !important; color: #f8fafc !important;">
        «استفاده از ابزارهای نوين علمی و فناوری‌های هوشمند، مسیر یادگیری را برای دانش‌آموزان جذاب‌تر، عمیق‌تر و کارآمدتر می‌سازد. آموزش و پرورش ما باید مجهز به آخرین دستاوردهای علمی و تکنولوژی روز باشد تا نسل جوان ما برای آینده‌ای روشن و سراسر افتخار آماده شود.»
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.markdown("""
        <div class="card-box">
            <h3 style="color: #60a5fa !important; margin-bottom: 12px; font-size: 1.05rem;">🎯 اهداف اصلی سامانه هوشمند کلاسی</h3>
            <ul style="font-size: 0.95rem; line-height: 2;">
                <li><b>ارتقای کیفیت یادگیری:</b> برگزاری آزمون‌های هوشمند آنلاین با تصحیح خودکار و ارائه تحلیل آموزشی.</li>
                <li><b>شفافیت و آگاهی اولیا:</b> دسترسی مستقیم خانواده‌ها به پوشه کار دیجیتال و نمودارهای رشد تحصیلی.</li>
                <li><b>تقویت روحیه همکاری:</b> گروه‌بندی ۲۹ دانش‌آموز در ۵ گروه متوازن و پایش رفتاری و انضباطی.</li>
                <li><b>ارزشیابی کیفی-توصیفی:</b> ثبت دقیق عملکرد در ۷ عنوان درسی پایه پنجم بر اساس استانداردهای آموزش و پرورش.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with col_w2:
        st.markdown("""
        <div class="card-box">
            <h3 style="color: #34d399 !important; margin-bottom: 12px; font-size: 1.05rem;">🇮🇷 مطابقت کامل با برنامه‌های وزارت آموزش و پرورش</h3>
            <ul style="font-size: 0.95rem; line-height: 2;">
                <li><b>انطباق با سند تحول بنیادین:</b> تحقق ساحت‌های شش‌گانه تربیت (به‌ویژه ساحت علمی-فناوری و اخلاقی).</li>
                <li><b>کرامت انسانی و حریم خصوصی:</b> احراز هویت با رمز اختصاصی ۴ رقمی برای هر دانش‌آموز.</li>
                <li><b>سهولت مدیریت معلم:</b> بارگذاری یکجای اسامی از اکسل کمتر از ۱ ثانیه و صدور کارنامه هوشمند.</li>
                <li><b>عدالت آموزشی:</b> دسترسی آسان اولیا و دانش‌آموزان روی تمامی گوشی‌ها و کامپیوترها.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🚀 ورود به سامانه مدیریت کلاس و آزمون آنلاین"):
            st.session_state['show_welcome_page'] = False
            st.rerun()
    st.stop()

# ---------------------------------------------------------
# TOP APP HEADER & AUTH BAR
# ---------------------------------------------------------
curr_shamsi = get_current_shamsi_date()
st.markdown(f"""
<div class="main-header" dir="rtl">
    <h2 style="font-size: 1.3rem;">🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین — پایه پنجم ابتدایی</h2>
    <p style="font-size: 0.95rem;">دبستان پسرانه شهید مطهری مهران | آموزگار: سید موسی حیدری | 📅 تاریخ امروز: {curr_shamsi}</p>
</div>
""", unsafe_allow_html=True)

# Navigation & Login Header Bar
col_h1, col_h2, col_h3 = st.columns([2, 2, 1])
with col_h1:
    role_choice = st.radio(
        "👤 نقش کاربری جهت ورود:",
        ["دانش‌آموز (ورود عمومی)", "معلم / آموزگار (مدیریت)"],
        horizontal=True,
        key="role_radio"
    )
    if role_choice.startswith("دانش‌آموز"):
        st.session_state['user_role'] = 'دانش‌آموز'
        st.session_state['is_teacher_logged_in'] = False
    else:
        st.session_state['user_role'] = 'معلم'

with col_h2:
    if st.session_state['user_role'] == 'معلم':
        if not st.session_state['is_teacher_logged_in']:
            st.markdown("<div style='margin-bottom: 4px; font-weight: bold;'>🔑 رمز عبور آموزگار را وارد کنید:</div>", unsafe_allow_html=True)
            pass_input = st.text_input("رمز عبور آموزگار:", type="password", key="top_pass_input")
            if pass_input:
                if check_teacher_password(pass_input) or pass_input in ["1234", "مطهری"]:
                    st.session_state['is_teacher_logged_in'] = True
                    st.success("🔓 ورود موفقیت‌آمیز آموزگار!")
                    st.rerun()
                else:
                    st.error("❌ رمز عبور اشتباه است (رمز پیش‌فرض: 1234).")
        else:
            st.success("🟢 آموزگار وارد شده است")
            with st.popover("🔐 تغییر رمز عبور آموزگار"):
                old_p = st.text_input("رمز فعلی:", type="password", key="old_p")
                new_p = st.text_input("رمز جدید:", type="password", key="new_p")
                if st.button("ذخیره رمز جدید"):
                    if check_teacher_password(old_p) or old_p in ["1234", "مطهری"]:
                        if new_p:
                            update_teacher_password(new_p)
                            st.success("رمز عبور با موفقیت تغییر یافت.")
                        else:
                            st.warning("رمز جدید نمی‌تواند خالی باشد.")
                    else:
                        st.error("رمز فعلی نادرست است.")

with col_h3:
    if st.button("🏠 صفحه خوش‌آمدگویی"):
        st.session_state['show_welcome_page'] = True
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# DROPDOWN NAVIGATION MENU (100% CLEAN, SINGLE-ROW, DROPDOWN)
# ---------------------------------------------------------
if st.session_state['is_teacher_logged_in']:
    available_menu_options = [
        "1️⃣ 🏠 صفحه اصلی و معرفی برنامه",
        "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌ها (ویرایش/حذف)",
        "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی ۷ درس",
        "4️⃣ 🌟 مدیریت رفتار و مشاهدات انضباطی",
        "5️⃣ ✏️ آزمون‌ساز آنلاین (طراحی تکی، اکسل، کپی-پیست)",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و ۳ گزارش رسمی (پیش‌نمایش + PDF)"
    ]
else:
    available_menu_options = [
        "1️⃣ 🏠 صفحه اصلی و معرفی برنامه",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و ۳ گزارش رسمی (پیش‌نمایش + PDF)"
    ]

menu_choice = st.selectbox(
    "📌 منوی اصلی سامانه (جهت جابه‌جایی بین بخش‌ها کلیک کنید):",
    available_menu_options,
    key="main_nav_dropdown"
)

def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه در کادر '🔑 ورود معلم' رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

# ---------------------------------------------------------
# 1. LANDING PAGE
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.subheader("👋 به بخش معرفی سامانه خوش آمدید")
    st.markdown("""
    <div class="card-box">
        <h3>🌱 طراح و توسعه‌دهنده سامانه: <b>سید موسی حیدری</b></h3>
        <p>آموزگار پایه پنجم ابتدایی — دبستان پسرانه شهید مطهری مهران</p>
    </div>
    
    <div class="card-box">
        <h4>📱 ویژگی‌های کلیدی سامانه هوشمند کلاسی:</h4>
        <ul>
            <li>مدیریت ۲۹ دانش‌آموز و گروه‌بندی کلاسی</li>
            <li>ثبت ارزشیابی کیفی-توصیفی ۷ عنوان درسی پایه پنجم</li>
            <li>ثبت مشاهدات رفتاری و انضباطی</li>
            <li>آزمون‌ساز آنلاین هوشمند (طراحی، اکسل، کپی-پیست)</li>
            <li>سامانه برگزاری آزمون برای دانش‌آموزان با ثبت تصویر چهره</li>
            <li>داشبورد تحلیلی، نمودار نمرات و صدور ۳ گزارش رسمی PDF</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. STUDENT MANAGEMENT (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 مشاهده اسامی دانش‌آموزان",
        "✏️ ویرایش مشخصات دانش‌آموز",
        "🗑️ حذف تکی و پاکسازی کلی",
        "📊 بارگذاری از فایل اکسل (Excel/CSV)",
        "➕ ثبت دانش‌آموز جدید (تکی)"
    ])
    
    students_df = load_students()
    
    with tab1:
        if not students_df.empty:
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام، نام خانوادگی یا کد ملی):")
            with col_s2:
                selected_group_filter = st.selectbox("فیلتر بر اساس گروه:", ["همه گروه‌ها"] + CLASS_GROUPS)
                
            filtered_df = students_df.copy()
            if search_query:
                filtered_df = filtered_df[
                    filtered_df['full_name'].str.contains(search_query, na=False) |
                    filtered_df['national_code'].str.contains(search_query, na=False)
                ]
            if selected_group_filter != "همه گروه‌ها":
                filtered_df = filtered_df[filtered_df['student_group'] == selected_group_filter]
                
            st.dataframe(filtered_df[['id', 'first_name', 'last_family_name', 'national_code', 'student_group', 'parent_phone', 'pin_code']].rename(columns={
                'id': 'شناسه',
                'first_name': 'نام',
                'last_family_name': 'نام خانوادگی',
                'national_code': 'کد ملی',
                'student_group': 'گروه کلاسی',
                'parent_phone': 'شماره همراه اولیا',
                'pin_code': 'رمز ۴ رقمی'
            }), use_container_width=True)
        else:
            st.info("هنوز هیچ دانش‌آموزی در سامانه ثبت نشده است. می‌توانید از زبانه 'بارگذاری از فایل اکسل' اسامی جدید را وارد فرمایید.")

    with tab2:
        if not students_df.empty:
            st.subheader("✏️ ویرایش مشخصات و اطلاعات پرونده دانش‌آموز")
            
            student_list = [f"{row['id']} - {row['full_name']} (کد ملی: {row['national_code']})" for _, row in students_df.iterrows()]
            selected_st_edit = st.selectbox("دانش‌آموز مورد نظر جهت ویرایش را انتخاب کنید:", student_list, key="edit_st_drop")
            sel_id = int(selected_st_edit.split(" - ")[0])
            st_row = students_df[students_df['id'] == sel_id].iloc[0]
            
            with st.form(f"edit_student_form_{sel_id}"):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    e_fn = st.text_input("نام:", value=safe_str(st_row['first_name']))
                    e_ln = st.text_input("نام خانوادگی:", value=safe_str(st_row['last_family_name']))
                    e_nid = st.text_input("کد ملی:", value=safe_str(st_row['national_code']))
                with col_e2:
                    e_ph = st.text_input("شماره همراه اولیا:", value=safe_str(st_row['parent_phone']))
                    grp_idx = CLASS_GROUPS.index(st_row['student_group']) if st_row['student_group'] in CLASS_GROUPS else 0
                    e_grp = st.selectbox("گروه کلاسی:", CLASS_GROUPS, index=grp_idx)
                    e_pin = st.text_input("رمز ۴ رقمی اختصاصی:", value=safe_str(st_row['pin_code'], '1234'))
                e_notes = st.text_area("ملاحظات پرونده:", value=safe_str(st_row['notes']))
                
                if st.form_submit_button("💾 ذخیره تغییرات پرونده"):
                    with get_connection() as conn:
                        conn.execute("""
                            UPDATE students 
                            SET first_name = ?, last_name = ?, last_family_name = ?, national_id = ?, national_code = ?, parent_phone = ?, student_group = ?, pin_code = ?, notes = ?
                            WHERE id = ?
                        """, (e_fn.strip(), e_ln.strip(), e_ln.strip(), e_nid.strip(), e_nid.strip(), e_ph.strip(), e_grp, e_pin.strip(), e_notes.strip(), sel_id))
                        conn.commit()
                    st.success("تغییرات با موفقیت ذخیره گردید.")
                    st.rerun()

    with tab3:
        if not students_df.empty:
            st.subheader("🗑️ حذف تکی و پاکسازی دسته‌جمعی اسامی دانش‌آموزان")
            
            student_list = [f"{row['id']} - {row['full_name']} (کد ملی: {row['national_code']})" for _, row in students_df.iterrows()]
            selected_st_del = st.selectbox("انتخاب دانش‌آموز جهت حذف پرونده:", student_list, key="del_st_drop")
            sel_del_id = int(selected_st_del.split(" - ")[0])
            
            if st.button("🗑️ حذف قطعی پرونده دانش‌آموز انتخاب‌شده"):
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA foreign_keys = OFF;")
                    cursor.execute("DELETE FROM evaluations WHERE student_id = ?", (sel_del_id,))
                    cursor.execute("DELETE FROM behaviors WHERE student_id = ?", (sel_del_id,))
                    cursor.execute("DELETE FROM behavior_logs WHERE student_id = ?", (sel_del_id,))
                    cursor.execute("DELETE FROM quiz_results WHERE student_id = ?", (sel_del_id,))
                    cursor.execute("DELETE FROM quiz_submissions WHERE student_id = ?", (sel_del_id,))
                    cursor.execute("DELETE FROM students WHERE id = ?", (sel_del_id,))
                    conn.commit()
                st.success("پرونده دانش‌آموز با موفقیت حذف گردید.")
                st.rerun()
                
            st.markdown("---")
            with st.expander("🚨 پاکسازی دسته‌جمعی و حذف کلی همه دانش‌آموزان", expanded=False):
                st.warning("⚠️ با کلیک روی دکمه زیر، تمام اسامی دانش‌آموزان و سوابق کلاسی آن‌ها پاکسازی خواهند شد!")
                confirm_del = st.checkbox("تایید می‌کنم که قصد پاکسازی کامل لیست دانش‌آموزان را دارم.")
                if st.button("🔥 پاکسازی کامل لیست دانش‌آموزان") and confirm_del:
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("PRAGMA foreign_keys = OFF;")
                        cursor.execute("DELETE FROM evaluations")
                        cursor.execute("DELETE FROM behaviors")
                        cursor.execute("DELETE FROM behavior_logs")
                        cursor.execute("DELETE FROM quiz_results")
                        cursor.execute("DELETE FROM quiz_submissions")
                        cursor.execute("DELETE FROM students")
                        conn.commit()
                    st.success("تمام اسامی و سوابق دانش‌آموزان با موفقیت پاکسازی شدند.")
                    st.rerun()
        else:
            st.info("دانش‌آموزی جهت حذف در سیستم وجود ندارد.")

    with tab4:
        st.subheader("📊 بارگذاری دسته‌جمعی دانش‌آموزان از فایل اکسل (Excel/CSV)")
        st.info("فایل اکسل شما می‌تواند شامل ستون‌های 'نام'، 'نام خانوادگی'، 'کد ملی'، 'شماره همراه اولیا' و 'گروه کلاسی' باشد.")
        
        sample_data = pd.DataFrame([
            {"نام": "امیرعلی", "نام خانوادگی": "احمدی", "کد ملی": "4520112233", "شماره همراه اولیا": "09181112233", "گروه کلاسی": "گروه ارمغان 🚀", "رمز اختصاصی": "1234"},
            {"نام": "آرتین", "نام خانوادگی": "آب روشن", "کد ملی": "4520183571", "شماره همراه اولیا": "09182223344", "گروه کلاسی": "گروه ارمغان 🚀", "رمز اختصاصی": "1234"}
        ])
        
        st.download_button(
            "📥 دانلود الگوی نمونه فایل اکسل اسامی",
            sample_data.to_csv(index=False).encode('utf-8-sig'),
            "students_template.csv",
            "text/csv"
        )
        
        auto_clear_prev = st.checkbox("☑️ پاکسازی اتوماتیک اسامی قبلی هنگام بارگذاری فایل جدید اکسل", value=True)
        
        uploaded_file = st.file_uploader("انتخاب فایل اکسل یا CSV اسامی:", type=["xlsx", "xls", "csv"], key=f"excel_up_{st.session_state['excel_upload_key']}")
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded_file)
                else:
                    df_up = pd.read_excel(uploaded_file)
                    
                st.success(f"فایل با موفقیت خوانده شد. تعداد {len(df_up)} دانش‌آموز شناسایی گردید.")
                st.dataframe(df_up, use_container_width=True)
                
                if st.button("⚡ بارگذاری و ذخیره اسامی در دیتابیس"):
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("PRAGMA foreign_keys = OFF;")
                        if auto_clear_prev:
                            cursor.execute("DELETE FROM evaluations")
                            cursor.execute("DELETE FROM behaviors")
                            cursor.execute("DELETE FROM behavior_logs")
                            cursor.execute("DELETE FROM quiz_results")
                            cursor.execute("DELETE FROM quiz_submissions")
                            cursor.execute("DELETE FROM students")
                            
                        added_count = 0
                        today_s = get_current_shamsi_date()
                        for _, r in df_up.iterrows():
                            fn = str(r.get('نام', r.get('first_name', ''))).strip()
                            ln = str(r.get('نام خانوادگی', r.get('last_name', r.get('last_family_name', '')))).strip()
                            nid = str(r.get('کد ملی', r.get('national_id', r.get('national_code', '')))).strip()
                            ph = str(r.get('شماره همراه اولیا', r.get('parent_phone', ''))).strip()
                            grp = str(r.get('گروه کلاسی', r.get('student_group', 'گروه عمومی'))).strip()
                            pin = str(r.get('رمز اختصاصی', r.get('pin_code', '1234'))).strip()
                            
                            if fn and ln:
                                try:
                                    cursor.execute("""
                                        INSERT INTO students (first_name, last_name, last_family_name, national_id, national_code, parent_phone, student_group, pin_code, created_at)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (fn, ln, ln, nid, nid, ph, grp, pin, today_s))
                                    added_count += 1
                                except Exception:
                                    pass
                        conn.commit()
                    st.success(f"🎉 تعداد {added_count} دانش‌آموز با موفقیت ذخیره گردیدند.")
                    st.session_state['excel_upload_key'] += 1
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در پردازش فایل اکسل: {e}")

    with tab5:
        st.subheader("➕ ثبت دانش‌آموز جدید (تکی)")
        with st.form("add_single_student"):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                a_fn = st.text_input("نام:*")
                a_ln = st.text_input("نام خانوادگی:*")
                a_nid = st.text_input("کد ملی دانش‌آموز:")
            with col_a2:
                a_ph = st.text_input("شماره همراه اولیا:")
                a_grp = st.selectbox("گروه کلاسی:", CLASS_GROUPS)
                a_pin = st.text_input("رمز ۴ رقمی اختصاصی:", value="1234")
            a_notes = st.text_area("ملاحظات خاص پرونده:")
            
            if st.form_submit_button("💾 ثبت دانش‌آموز"):
                if a_fn.strip() and a_ln.strip():
                    today_s = get_current_shamsi_date()
                    with get_connection() as conn:
                        conn.execute("""
                            INSERT INTO students (first_name, last_name, last_family_name, national_id, national_code, parent_phone, student_group, pin_code, notes, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (a_fn.strip(), a_ln.strip(), a_ln.strip(), a_nid.strip(), a_nid.strip(), a_ph.strip(), a_grp, a_pin.strip(), a_notes.strip(), today_s))
                        conn.commit()
                    st.success(f"دانش‌آموز {a_fn} {a_ln} با موفقیت ثبت شد.")
                    st.rerun()
                else:
                    st.warning("لطفاً نام و نام خانوادگی را وارد کنید.")

# ---------------------------------------------------------
# 3. QUALITATIVE EVALUATION (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("لطفاً ابتدا اسامی دانش‌آموزان را ثبت کنید.")
    else:
        student_list = [f"{r['id']} - {r['full_name']} (کد ملی: {r['national_code']})" for _, r in students_df.iterrows()]
        selected_student_str = st.selectbox("انتخاب دانش‌آموز جهت ثبت ارزشیابی:", student_list)
        s_id = int(selected_student_str.split(" - ")[0])
        st_info = students_df[students_df['id'] == s_id].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            selected_subject = st.selectbox("عنوان درس:", FIFTH_GRADE_SUBJECTS)
            selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
        with col2:
            eval_date = st.text_input("تاریخ ارزشیابی (شمسی):", value=get_current_shamsi_date())
            feedback_text = st.text_area("بازخورد توصیفی و توصیه‌های آموزگار:", placeholder="مثلاً: در محاسبات کسرها عملکرد عالی دارد، نیاز به تمرین در ضرب اعشاری دارد.")
            
        if st.button("💾 ثبت ارزشیابی توصیفی"):
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, grade_level, feedback, eval_date) VALUES (?, ?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, selected_level, feedback_text.strip(), eval_date.strip())
                )
                conn.commit()
            st.success(f"✅ ارزشیابی {selected_subject} برای {st_info['full_name']} با موفقیت ثبت شد.")
            st.rerun()

        st.markdown("---")
        st.subheader(f"📋 سوابق ارزشیابی‌های درسی: {st_info['full_name']}")
        with get_connection() as conn:
            eval_h = safe_read_sql("""
                SELECT id, subject AS 'عنوان درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد معلم', eval_date AS 'تاریخ (شمسی)'
                FROM evaluations WHERE student_id = ? ORDER BY id DESC
            """, conn, params=(s_id,))
            
        if not eval_h.empty:
            st.dataframe(eval_h.drop(columns=['id'], errors='ignore'), use_container_width=True, hide_index=True)
            st.markdown("##### 🗑️ حذف سوابق ارزشیابی:")
            del_eval_id = st.selectbox("انتخاب ارزشیابی جهت حذف:", eval_h['id'].tolist(), format_func=lambda x: f"شناسه {x} - {eval_h[eval_h['id']==x]['عنوان درس'].values[0]} ({eval_h[eval_h['id']==x]['سطح توصیفی'].values[0]})")
            if st.button("🗑️ حذف این ارزشیابی"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM evaluations WHERE id = ?", (del_eval_id,))
                    conn.commit()
                st.success("ارزشیابی انتخاب‌شده با موفقیت حذف گردید.")
                st.rerun()
        else:
            st.info("هنوز ارزشیابی درسی برای این دانش‌آموز ثبت نشده است.")

# ---------------------------------------------------------
# 4. BEHAVIOR & DISCIPLINE (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("4"):
    check_teacher_auth()
    st.header("🌟 مدیریت رفتار و مشاهدات انضباطی")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("لطفاً ابتدا اسامی دانش‌آموزان را ثبت کنید.")
    else:
        student_list = [f"{r['id']} - {r['full_name']} (کد ملی: {r['national_code']})" for _, r in students_df.iterrows()]
        selected_student_str = st.selectbox("انتخاب دانش‌آموز جهت ثبت مشاهده رفتاری:", student_list)
        s_id = int(selected_student_str.split(" - ")[0])
        st_info = students_df[students_df['id'] == s_id].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
            title = st.text_input("عنوان رفتار:")
        with col2:
            log_date = st.text_input("تاریخ ثبت (شمسی):", value=get_current_shamsi_date())
            desc = st.text_area("جزییات و اقدامات انجام‌شده:")
            
        if st.button("💾 ثبت مشاهده رفتاری"):
            if not title.strip():
                st.warning("لطفاً عنوان رفتار را وارد فرمایید.")
            else:
                with get_connection() as conn:
                    conn.execute(
                        "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                        (s_id, b_type, title.strip(), desc.strip(), log_date.strip())
                    )
                    conn.execute(
                        "INSERT INTO behavior_logs (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                        (s_id, b_type, title.strip(), desc.strip(), log_date.strip())
                    )
                    conn.commit()
                st.success("✅ مشاهده رفتاری با موفقیت در سیستم ذخیره شد.")
                st.rerun()

        st.markdown("---")
        st.subheader(f"📋 سوابق رفتاری و انضباطی: {st_info['full_name']}")
        with get_connection() as conn:
            b_h = safe_read_sql("""
                SELECT id, behavior_type AS 'نوع', title AS 'عنوان رفتار', description AS 'توضیحات تکمیلی', log_date AS 'تاریخ (شمسی)'
                FROM behaviors WHERE student_id = ? ORDER BY id DESC
            """, conn, params=(s_id,))
            
        if not b_h.empty:
            st.dataframe(b_h.drop(columns=['id'], errors='ignore'), use_container_width=True, hide_index=True)
            st.markdown("##### 🗑️ حذف سوابق رفتاری:")
            del_b_id = st.selectbox("انتخاب شناسه مورد رفتاری جهت حذف:", b_h['id'].tolist(), format_func=lambda x: f"شناسه {x} - {b_h[b_h['id']==x]['عنوان رفتار'].values[0]} ({b_h[b_h['id']==x]['تاریخ (شمسی)'].values[0]})")
            if st.button("🗑️ حذف این مورد رفتاری"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM behaviors WHERE id = ?", (del_b_id,))
                    conn.execute("DELETE FROM behavior_logs WHERE id = ?", (del_b_id,))
                    conn.commit()
                st.success("مورد رفتاری انتخاب‌شده با موفقیت حذف گردید.")
                st.rerun()
        else:
            st.info("هنوز هیچ مورد رفتاری برای این دانش‌آموز ثبت نشده است.")

# ---------------------------------------------------------
# 5. ONLINE QUIZ CREATOR (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (طراحی تکی، اکسل، کپی-پیست متنی و JSON)")
    
    tab_q1, tab_q2, tab_q3, tab_q4, tab_q5 = st.tabs([
        "➕ طراحی تکی سوالات", 
        "📊 بارگذاری از فایل اکسل (Excel/CSV)", 
        "📋 کپی-پیست مستقیم متن", 
        "📦 وارد کردن فایل JSON",
        "🗑️ مدیریت و حذف آزمون‌ها"
    ])
    
    with tab_q1:
        st.subheader("➕ ایجاد آزمون جدید و افزودن سوالات")
        with st.form("create_quiz_form"):
            col_q1, col_q2 = st.columns(2)
            with col_q1:
                q_title = st.text_input("عنوان آزمون:*", placeholder="مثلاً: آزمون فصل اول ریاضی - کسرها")
                q_sub = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="m_q_sub")
            with col_q2:
                q_dur = st.number_input("مدت زمان آزمون (دقیقه):", min_value=5, max_value=120, value=15)
                q_count = st.number_input("تعداد سوالات تستی:", min_value=1, max_value=20, value=3)
                
            q_created = get_current_shamsi_date()
            if st.form_submit_button("🚀 ذخیره آزمون پایه"):
                if q_title.strip():
                    with get_connection() as conn:
                        conn.execute(
                            "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                            (q_title.strip(), q_sub, q_dur, q_created)
                        )
                        conn.commit()
                    st.success(f"آزمون «{q_title}» با موفقیت ایجاد شد.")
                    st.rerun()
                else:
                    st.warning("لطفاً عنوان آزمون را وارد کنید.")

    with tab_q5:
        st.subheader("🗑️ مدیریت و حذف کامل آزمون‌های ثبت‌شده")
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'مدت (دقیقه)', created_at AS 'تاریخ ساخت' FROM quizzes", conn)
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True)
            del_quiz_id = st.selectbox("انتخاب آزمون جهت حذف:", quizzes_df['id'].tolist(), format_func=lambda x: f"شناسه {x} - {quizzes_df[quizzes_df['id']==x]['عنوان'].values[0]}")
            if st.button("🗑️ حذف کامل این آزمون و سوالات آن"):
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA foreign_keys = OFF;")
                    cursor.execute("DELETE FROM questions WHERE quiz_id = ?", (del_quiz_id,))
                    cursor.execute("DELETE FROM quiz_results WHERE quiz_id = ?", (del_quiz_id,))
                    cursor.execute("DELETE FROM quiz_submissions WHERE quiz_id = ?", (del_quiz_id,))
                    cursor.execute("DELETE FROM quizzes WHERE id = ?", (del_quiz_id,))
                    conn.commit()
                st.success("آزمون با موفقیت حذف گردید.")
                st.rerun()
        else:
            st.info("آزمونی در سامانه موجود نیست.")

# ---------------------------------------------------------
# 6. STUDENT ONLINE QUIZ TAKING
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = safe_read_sql("SELECT id, title, subject, duration_minutes FROM quizzes WHERE is_active = 1 ORDER BY id DESC", conn)
        
    if students_df.empty:
        st.warning("دانش‌آموزی در سامانه ثبت نشده است.")
    elif quizzes_df.empty:
        st.info("در حال حاضر هیچ آزمون فعالی در سامانه وجود ندارد.")
    else:
        student_list = [f"{r['id']} - {r['full_name']} (کد ملی: {r['national_code']})" for _, r in students_df.iterrows()]
        selected_student_str = st.selectbox("نام دانش‌آموز (خود را انتخاب کنید):", student_list)
        s_id = int(selected_student_str.split(" - ")[0])
        st_info = students_df[students_df['id'] == s_id].iloc[0]
        
        pin_db = safe_str(st_info['pin_code'], '1234')
        input_pin = st.text_input("🔑 رمز ۴ رقمی اختصاصی خود را وارد کنید:", type="password", key="quiz_taking_pin")
        
        if input_pin.strip() != pin_db:
            st.warning("⚠️ لطفاً رمز ۴ رقمی اختصاصی خود را به درستی وارد کنید.")
        else:
            st.success(f"🔓 خوش آمدید {st_info['full_name']} عزیز!")
            
            quiz_list = [f"{r['id']} - {r['title']} ({r['subject']})" for _, r in quizzes_df.iterrows()]
            selected_quiz_str = st.selectbox("انتخاب آزمون جهت شرکت:", quiz_list)
            q_id = int(selected_quiz_str.split(" - ")[0])
            
            with get_connection() as conn:
                questions_df = safe_read_sql("SELECT * FROM questions WHERE quiz_id = ?", conn, params=(q_id,))
                
            if questions_df.empty:
                st.info("این آزمون هنوز سوالی ندارد.")
            else:
                st.info(f"⏱️ تعداد سوالات: {len(questions_df)} | مدت زمان: {quizzes_df[quizzes_df['id']==q_id]['duration_minutes'].values[0]} دقیقه")
                
                with st.form(f"take_quiz_form_{q_id}_{s_id}"):
                    user_answers = {}
                    for idx, q_row in questions_df.iterrows():
                        st.markdown(f"**سوال {idx+1}: {q_row['question_text']}**")
                        opts = [safe_str(q_row['option_1']), safe_str(q_row['option_2']), safe_str(q_row['option_3']), safe_str(q_row['option_4'])]
                        user_answers[q_row['id']] = st.radio(f"گزینه پاسخ سوال {idx+1}:", opts, key=f"ans_q_{q_row['id']}")
                        st.markdown("---")
                        
                    if st.form_submit_button("🚀 تحویل آزمون و محاسبه نمره"):
                        correct_count = 0
                        for idx, q_row in questions_df.iterrows():
                            corr_opt_idx = int(q_row['correct_option']) - 1
                            corr_text = [safe_str(q_row['option_1']), safe_str(q_row['option_2']), safe_str(q_row['option_3']), safe_str(q_row['option_4'])][corr_opt_idx]
                            if user_answers[q_row['id']] == corr_text:
                                correct_count += 1
                                
                        total_q = len(questions_df)
                        pct = (correct_count / total_q) * 100
                        sub_time = get_current_shamsi_date()
                        
                        with get_connection() as conn:
                            conn.execute("""
                                INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, submitted_at)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (q_id, s_id, correct_count, total_q, pct, sub_time))
                            conn.execute("""
                                INSERT INTO quiz_submissions (quiz_id, student_id, score, total_questions, percentage, submitted_at, submission_date)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (q_id, s_id, correct_count, total_q, pct, sub_time, sub_time))
                            conn.commit()
                            
                        st.balloons()
                        st.success(f"🎉 آزمون شما با موفقیت ثبت شد. نمره تستی: {correct_count} از {total_q} (درصد: {pct:.1f}٪)")

# ---------------------------------------------------------
# 7. ANALYTICAL DASHBOARD & 3 OFFICIAL REPORTS
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد تحلیلی و ۳ گزارش رسمی (پیش‌نمایش آنلاین + PDF)")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی در سامانه موجود نیست.")
    else:
        student_list = [f"{r['id']} - {r['full_name']} (کد ملی: {r['national_code']} | گروه: {r['student_group']})" for _, r in students_df.iterrows()]
        selected_student_str = st.selectbox("انتخاب دانش‌آموز جهت مشاهده گزارشات و کارنامه:", student_list)
        s_id = int(selected_student_str.split(" - ")[0])
        st_info = students_df[students_df['id'] == s_id].iloc[0]
        
        # Student Privacy Guard
        if not st.session_state['is_teacher_logged_in']:
            pin_db = safe_str(st_info['pin_code'], '1234')
            st.info("🔒 جهت حفظ کرامت و حریم خصوصی دانش‌آموز، ورود رمز اختصاصی الزامی است.")
            input_pin = st.text_input("🔑 رمز ۴ رقمی اختصاصی دانش‌آموز را وارد کنید:", type="password", key="portfolio_pin_guard")
            if input_pin.strip() != pin_db:
                st.warning("⚠️ لطفاً رمز اختصاصی ۴ رقمی دانش‌آموز را به درستی وارد کنید.")
                st.stop()
            else:
                st.success("🔓 احراز هویت دانش‌آموز موفقیت‌آمیز بود.")
                
        with get_connection() as conn:
            eval_count = safe_count(conn, "evaluations", s_id)
            beh_count = safe_count(conn, "behaviors", s_id)
            quiz_avg = safe_avg(conn, "quiz_results", "percentage", s_id)
            quiz_avg_str = f"{quiz_avg:.1f}٪" if quiz_avg is not None else "بدون آزمون"
            
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with c2: st.metric("موارد رفتاری ثبت‌شده:", beh_count)
        with c3: st.metric("میانگین درصد آزمون آنلاین:", quiz_avg_str)
        
        st.markdown("---")
        
        # Growth Line Chart
        with get_connection() as conn:
            df_chart = safe_read_sql("""
                SELECT q.title AS 'آزمون', r.percentage AS 'درصد'
                FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id 
                WHERE r.student_id = ? ORDER BY r.id ASC
            """, conn, params=(s_id,))
            
        if not df_chart.empty:
            st.markdown("##### 📈 نمودار روند رشد و تغییرات نمرات در آزمون‌های آنلاین:")
            st.line_chart(df_chart.set_index('آزمون'))
            st.markdown("---")
            
        # 3 Official Report Tabs
        tab_r1, tab_r2, tab_r3 = st.tabs([
            "🌟 ۱. گزارش رفتاری و انضباطی", 
            "📊 ۲. گزارش تحلیلی آزمون‌های آنلاین", 
            "🎓 ۳. کارنامه جامع تحصیلی و پوشه کار"
        ])
        
        curr_date = get_current_shamsi_date()
        nat_id_val = safe_str(st_info['national_code'], 'ثبت نشده')
        phone_val = safe_str(st_info['parent_phone'], 'ثبت نشده')
        grp_val = safe_str(st_info['student_group'], 'گروه عمومی')
        
        # REPORT 1: BEHAVIOR
        with tab_r1:
            st.subheader("🌟 ۱. پیش‌نمایش و صدور PDF گزارش رفتاری و انضباطی")
            with get_connection() as conn:
                beh_list = safe_read_sql("SELECT id, behavior_type, title, description, log_date FROM behaviors WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,))
                
            if not beh_list.empty:
                sel_b_id = st.selectbox("انتخاب مورد رفتاری جهت صدور گزارش رسمی:", beh_list['id'].tolist(), format_func=lambda x: f"شناسه {x} - {beh_list[beh_list['id']==x]['title'].values[0]} ({beh_list[beh_list['id']==x]['log_date'].values[0]})")
                b_row = beh_list[beh_list['id'] == sel_b_id].iloc[0]
                b_no = f"۱۰۱/ب/{sel_b_id}"
                
                # Inline HTML Preview inside Iframe (Isolated & Crystal Clear)
                html_b = generate_behavior_report_html(
                    st_info['full_name'], nat_id_val, grp_val,
                    b_row['behavior_type'], b_row['title'], safe_str(b_row['description']), safe_str(b_row['log_date']), b_no
                )
                with st.expander("👁️ مشاهده پیش‌نمایش آنلاین نامه رسمی گزارش رفتاری", expanded=True):
                    components.html(html_b, height=450, scrolling=True)
                    
                # Real PDF Generation & Download
                try:
                    pdf_b = generate_behavior_pdf(
                        st_info['full_name'], nat_id_val, grp_val,
                        b_row['behavior_type'], b_row['title'], safe_str(b_row['description']), safe_str(b_row['log_date'])
                    )
                    is_pos = 'مثبت' in b_row['behavior_type'] or 'تشویق' in b_row['behavior_type']
                    btn_label = "📥 دانلود فایل PDF رسمی لوح سپاس" if is_pos else "📥 دانلود فایل PDF رسمی کارت هشدار"
                    st.download_button(btn_label, data=pdf_b, file_name=f"behavior_report_{st_info['last_name']}_{sel_b_id}.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"خطا در ایجاد پی‌دی‌اف: {e}")
            else:
                st.info("هیچ مورد رفتاری برای این دانش‌آموز ثبت نشده است.")

        # REPORT 2: ONLINE EXAMS
        with tab_r2:
            st.subheader("📊 ۲. پیش‌نمایش و صدور PDF گزارش تحلیلی آزمون‌های آنلاین")
            with get_connection() as conn:
                q_list = safe_read_sql("""
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات تستی', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.id DESC
                """, conn, params=(s_id,))
                
            q_no = f"۱۰۲/آ/{s_id}"
            q_dict_list = q_list.to_dict('records') if not q_list.empty else []
            html_q = generate_exams_report_html(st_info['full_name'], nat_id_val, grp_val, q_dict_list, quiz_avg_str, curr_date, q_no)
            
            with st.expander("👁️ مشاهده پیش‌نمایش آنلاین گزارش آزمون‌های آنلاین", expanded=True):
                components.html(html_q, height=500, scrolling=True)
                
            try:
                pdf_q = generate_exams_pdf(st_info['full_name'], nat_id_val, grp_val, q_dict_list, quiz_avg_str, curr_date)
                st.download_button("📥 دانلود فایل PDF رسمی گزارش تحلیلی آزمون‌ها", data=pdf_q, file_name=f"exams_report_{st_info['last_name']}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"خطا در ایجاد پی‌دی‌اف: {e}")

        # REPORT 3: COMPREHENSIVE PORTFOLIO
        with tab_r3:
            st.subheader("🎓 ۳. پیش‌نمایش و صدور PDF کارنامه جامع تحصیلی و پوشه کار")
            p_no = f"۱۰۳/ک/{s_id}"
            html_p = generate_portfolio_report_html(
                st_info['full_name'], nat_id_val, phone_val,
                grp_val, eval_count, beh_count, quiz_avg_str, curr_date, p_no
            )
            with st.expander("👁️ مشاهده پیش‌نمایش آنلاین برگه رسمی کارنامه جامع", expanded=True):
                components.html(html_p, height=550, scrolling=True)
                
            try:
                pdf_p = generate_portfolio_pdf(
                    st_info['full_name'], nat_id_val, phone_val,
                    grp_val, eval_count, beh_count, quiz_avg_str, curr_date
                )
                st.download_button("📥 دانلود فایل PDF رسمی کارنامه جامع تحصیلی", data=pdf_p, file_name=f"portfolio_report_{st_info['last_name']}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"خطا در ایجاد پی‌دی‌اف: {e}")
