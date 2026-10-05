import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json
import random
import re
import io
import os
import tempfile
import subprocess

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
    jm = 1 + (days // 31) if days < 186 else 7 + ((days - 186) // 30)
    jd = 1 + (days % 31) if days < 186 else 1 + ((days - 186) % 30)
    return f"{jy}/{jm:02d}/{jd:02d}"

def get_current_shamsi_date():
    now = datetime.datetime.now()
    return gregorian_to_jalali(now.year, now.month, now.day)

# ---------------------------------------------------------
# Persian / Arabic Text Shaping & Reshaping Helpers
# ---------------------------------------------------------
PERSIAN_MAP = {
    'ا': ('ﺍ', 'ﺎ', 'ﺎ', 'ﺍ'), 'ب': ('ﺏ', 'ﺑ', 'ﺒ', 'ﺐ'), 'پ': ('ﭖ', 'ﭘ', 'ﭙ', 'ﭗ'),
    'ت': ('ﺕ', 'ﺗ', 'ﺘ', 'ﺖ'), 'ث': ('ﺙ', 'ﺛ', 'ﺜ', 'ﺚ'), 'ج': ('ﺝ', 'ﺟ', 'ﺠ', 'ﺞ'),
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
        elif prev_conn: res.append(fin)
        elif next_conn: res.append(init)
        else: res.append(iso)
    return ''.join(res)

def _rtl(text):
    if not text: return ''
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return _reshape(str(text))[::-1]

# ---------------------------------------------------------
# ReportLab Lazy Import & Font Registration
# ---------------------------------------------------------
_PERSIAN_FONT_REGISTERED = False

def _get_reportlab():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.colors import HexColor
        return True, A4, canvas, pdfmetrics, TTFont, HexColor
    except Exception:
        return False, None, None, None, None, None

def _register_persian_font():
    global _PERSIAN_FONT_REGISTERED
    if not _PERSIAN_FONT_REGISTERED:
        has_rl, A4, canvas, pdfmetrics, TTFont, HexColor = _get_reportlab()
        if has_rl:
            font_paths = [
                '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf',
                '/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf',
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

# ---------------------------------------------------------
# Page Configuration & RTL Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    * {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    }
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #ffffff !important;
        direction: rtl !important;
    }
    h1, h2, h3, h4, h5, h6, label, p, span, div {
        direction: rtl !important;
        text-align: right !important;
    }
    .stApp header, .stApp h1 {
        color: #ffffff !important;
    }
    h1 {
        text-align: center !important;
    }
    /* Buttons Styling */
    .stButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        padding: 10px 18px !important;
        font-weight: bold !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3) !important;
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
    }
    .stDownloadButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        padding: 10px 18px !important;
        font-weight: bold !important;
        border: none !important;
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

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            national_id TEXT UNIQUE,
            pin_code TEXT DEFAULT '1234',
            parent_phone TEXT,
            student_group TEXT DEFAULT 'بدون گروه',
            notes TEXT,
            created_at TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT NOT NULL,
            level TEXT NOT NULL,
            feedback TEXT,
            eval_date TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS behaviors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            behavior_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            log_date TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        
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
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_auth (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            password TEXT NOT NULL
        )
        """)
        cursor.execute("INSERT OR IGNORE INTO teacher_auth (id, password) VALUES (1, '1234')")
        
        # Schema migrations
        columns_to_add = [
            ("students", "pin_code", "TEXT DEFAULT '1234'"),
            ("students", "student_group", "TEXT DEFAULT 'بدون گروه'"),
            ("quizzes", "is_active", "INTEGER DEFAULT 1"),
            ("questions", "question_type", "TEXT DEFAULT 'mcq'"),
            ("questions", "model_answer", "TEXT"),
            ("questions", "explanation", "TEXT"),
            ("quiz_results", "photo_data", "TEXT"),
            ("quiz_results", "essay_answers", "TEXT")
        ]
        for table, col, col_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass
                
        conn.commit()

init_db()

# Safe Read SQL Helper
def safe_read_sql(query, conn, params=()):
    try:
        return pd.read_sql_query(query, conn, params=params)
    except Exception:
        return pd.DataFrame()

# ---------------------------------------------------------
# Helper Constants
# ---------------------------------------------------------
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

def load_students():
    with get_connection() as conn:
        df = safe_read_sql("SELECT *, (first_name || ' ' || last_name) AS full_name FROM students ORDER BY last_name, first_name", conn)
        return df

# ---------------------------------------------------------
# Smart Excel Student Import Parser
# ---------------------------------------------------------
def parse_students_excel_smart(df_up):
    cols = [str(c).strip() for c in df_up.columns]
    col_map = {}
    
    for c in cols:
        c_clean = c.replace('_', ' ').replace('-', ' ').strip()
        if c_clean in ['نام و نام خانوادگی', 'نام و فامیلی', 'نام کامل', 'نام و نامخانوادگی', 'مشخصات دانش آموز']:
            col_map['full_name_combined'] = c
            break

    for c in cols:
        c_clean = c.replace('_', ' ').replace('-', ' ').strip()
        if c != col_map.get('full_name_combined'):
            if any(k in c_clean for k in ['نام خانوادگی', 'فامیلی', 'شهرت', 'last_name', 'family']):
                col_map['last_name'] = c
                break

    for c in cols:
        c_clean = c.replace('_', ' ').replace('-', ' ').strip()
        if c != col_map.get('full_name_combined') and c != col_map.get('last_name'):
            if any(k in c_clean for k in ['نام', 'first_name', 'name']):
                col_map['first_name'] = c
                break

    for c in cols:
        c_clean = c.replace('_', ' ').replace('-', ' ').strip()
        if any(k in c_clean for k in ['کد ملی', 'کدملی', 'شماره ملی', 'شناسه ملی', 'national_id', 'id']):
            col_map['national_id'] = c
            break

    for c in cols:
        c_clean = c.replace('_', ' ').replace('-', ' ').strip()
        if any(k in c_clean for k in ['تلفن', 'همراه', 'موبایل', 'تماس', 'phone', 'mobile']):
            col_map['parent_phone'] = c
            break

    for c in cols:
        c_clean = c.replace('_', ' ').replace('-', ' ').strip()
        if any(k in c_clean for k in ['گروه', 'کلاس', 'group']):
            col_map['student_group'] = c
            break

    for c in cols:
        c_clean = c.replace('_', ' ').replace('-', ' ').strip()
        if any(k in c_clean for k in ['رمز', 'پین', 'pin', 'pass']):
            col_map['pin_code'] = c
            break

    parsed = []
    for _, row in df_up.iterrows():
        fn, ln = "", ""
        if 'full_name_combined' in col_map and 'last_name' not in col_map:
            raw_full = str(row.get(col_map['full_name_combined'], '')).strip()
            if raw_full and raw_full != 'nan':
                parts = raw_full.split()
                if len(parts) >= 2:
                    fn = parts[0]
                    ln = ' '.join(parts[1:])
                else:
                    fn = raw_full
                    ln = '-'
        else:
            fn = str(row.get(col_map.get('first_name'), '')).strip()
            ln = str(row.get(col_map.get('last_name'), '')).strip()

        if fn == 'nan': fn = ""
        if ln == 'nan': ln = ""

        def _clean_num_str(val, default=""):
            if pd.isna(val) or val is None: return default
            s = str(val).strip()
            if s.endswith('.0'): s = s[:-2]
            return s if s != 'nan' else default

        nid = _clean_num_str(row.get(col_map.get('national_id')))
        pin = _clean_num_str(row.get(col_map.get('pin_code')), '1234')
        ph = _clean_num_str(row.get(col_map.get('parent_phone')))
        grp = _clean_num_str(row.get(col_map.get('student_group')), 'گروه ارمغان 🚀')

        if fn or ln:
            parsed.append({
                'first_name': fn or 'نام',
                'last_name': ln or 'خانوادگی',
                'national_id': nid,
                'pin_code': pin,
                'parent_phone': ph,
                'student_group': grp,
                'full_name': f"{fn} {ln}".strip()
            })

    return parsed

# ---------------------------------------------------------
# Official Comprehensive Report Card PDF Generator
# ---------------------------------------------------------
def generate_reportlab_portfolio_pdf(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str, eval_data=None):
    has_rl, A4, canvas, pdfmetrics, TTFont, HexColor = _get_reportlab()
    if not has_rl:
        return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    
    _register_persian_font()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    font_name = 'PersianFont' if _PERSIAN_FONT_REGISTERED else 'Helvetica'
    
    # Header bar
    c.setFillColor(HexColor('#0f172a'))
    c.rect(0, h-85, w, 85, fill=1, stroke=0)
    
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(font_name, 12)
    c.drawCentredString(w/2, h-22, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
    c.setFont(font_name, 10)
    c.drawCentredString(w/2, h-42, _rtl('اداره آموزش و پرورش شهرستان مهران - دبستان هیئت امنایی شهید مطهری'))
    c.setFont(font_name, 12)
    c.drawCentredString(w/2, h-66, _rtl('کارنامه رسمی ارزشیابی توصیفی - کیفی و پوشه کار دیجیتال (سال ۱۴۰۴-۱۴۰۵)'))
    
    # Student Info Box
    y = h - 105
    c.setFillColor(HexColor('#f8fafc'))
    c.setStrokeColor(HexColor('#cbd5e1'))
    c.rect(30, y-50, w-60, 50, fill=1, stroke=1)
    
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 10)
    c.drawRightString(w - 45, y - 18, _rtl(f'نام و نام خانوادگی: {student_name}'))
    c.drawRightString(w - 230, y - 18, _rtl(f'کد ملی: {national_id}'))
    c.drawRightString(w - 400, y - 18, _rtl('پایه تحصیلی: پنجم ابتدایی'))
    
    c.drawRightString(w - 45, y - 38, _rtl(f'گروه کلاسی: {student_group}'))
    c.drawRightString(w - 230, y - 38, _rtl(f'شماره همراه اولیا: {parent_phone}'))
    c.drawRightString(w - 400, y - 38, _rtl('سال تحصیلی: ۱۴۰۴ - ۱۴۰۵'))
    
    # Table of 7 Subjects Header
    y -= 75
    c.setFont(font_name, 11)
    c.setFillColor(HexColor('#1e293b'))
    c.drawRightString(w - 30, y, _rtl('📊 جدول ارزشیابی کیفی - توصیفی ۷ عنوان درسی:'))
    
    y -= 16
    c.setFillColor(HexColor('#1e3a8a'))
    c.rect(30, y-22, w-60, 22, fill=1, stroke=1)
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(font_name, 9)
    c.drawRightString(w - 40, y - 15, _rtl('#'))
    c.drawRightString(w - 80, y - 15, _rtl('عنوان درس'))
    c.drawRightString(w - 210, y - 15, _rtl('سطح عملکرد توصیفی'))
    c.drawRightString(w - 350, y - 15, _rtl('توصیف عملکرد و بازخورد آموزگار'))
    
    # Mapping evaluation data
    subj_map = {}
    if eval_data:
        for s_title, s_lvl, s_fb in eval_data:
            subj_map[s_title] = (s_lvl, s_fb)

    y -= 22
    c.setFont(font_name, 9)
    for idx, subj_name in enumerate(FIFTH_GRADE_SUBJECTS, start=1):
        num_str = str(idx)
        if subj_name in subj_map:
            lvl_str, fb_str = subj_map[subj_name]
        else:
            lvl_str = "در حال ارزشیابی ⏳"
            fb_str = "عملکرد کلاسی طبق سرفصل‌های آموزشی در حال ثبت است."
            
        c.setFillColor(HexColor('#ffffff') if idx % 2 == 1 else HexColor('#f1f5f9'))
        c.rect(30, y-20, w-60, 20, fill=1, stroke=1)
        c.setFillColor(HexColor('#0f172a'))
        c.drawRightString(w - 42, y - 14, _rtl(num_str))
        c.drawRightString(w - 80, y - 14, _rtl(subj_name))
        c.drawRightString(w - 210, y - 14, _rtl(lvl_str))
        c.drawRightString(w - 350, y - 14, _rtl(str(fb_str)[:38]))
        y -= 20

    # Summary Box
    y -= 25
    c.setFillColor(HexColor('#f0fdf4'))
    c.setStrokeColor(HexColor('#bbf7d0'))
    c.rect(30, y-45, w-60, 45, fill=1, stroke=1)
    c.setFillColor(HexColor('#166534'))
    c.setFont(font_name, 10)
    c.drawRightString(w - 45, y - 18, _rtl('💡 خلاصه ارزیابی آزمون‌ها و موارد رفتاری:'))
    c.setFont(font_name, 9)
    c.drawRightString(w - 45, y - 35, _rtl(f'میانگین درصد آزمون‌های آنلاین: {quiz_avg_str} | تعداد ارزشیابی‌های ثبت‌شده: {eval_count} درس | موارد ثبت‌شده رفتاری/انضباطی: {beh_count} مورد'))
    
    # Signatures
    y -= 75
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 10)
    c.drawRightString(w - 45, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
    c.drawRightString(w/2 + 30, y, _rtl('مدیریت دبستان: شهید مطهری مهران'))
    c.drawRightString(150, y, _rtl('رویت و امضای اولیای محترم'))
    
    c.save()
    return buf.getvalue()

def generate_comprehensive_portfolio_pdf(student_id):
    with get_connection() as conn:
        st_row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        if not st_row:
            return b""
        student_name = f"{st_row['first_name']} {st_row['last_name']}"
        national_id = st_row['national_id'] or "ثبت نشده"
        parent_phone = st_row['parent_phone'] or "ثبت نشده"
        student_group = st_row['student_group'] or "بدون گروه"
        
        eval_rows = conn.execute("SELECT subject, level, feedback FROM evaluations WHERE student_id = ? ORDER BY id DESC", (student_id,)).fetchall()
        eval_data = [(r['subject'], r['level'], r['feedback']) for r in eval_rows]
        
        eval_count = len(eval_data)
        beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (student_id,)).fetchone()[0]
        quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (student_id,)).fetchone()[0]
        quiz_avg_str = f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون"

    return generate_reportlab_portfolio_pdf(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str, eval_data)

def generate_behavior_report_pdf(student_name, national_id, student_group, b_type, title, desc, date_str):
    has_rl, A4, canvas, pdfmetrics, TTFont, HexColor = _get_reportlab()
    if not has_rl:
        return b""
    _register_persian_font()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    font_name = 'PersianFont' if _PERSIAN_FONT_REGISTERED else 'Helvetica'
    
    is_positive = 'مثبت' in b_type or 'تشویق' in b_type
    bg_color = HexColor('#15803d') if is_positive else HexColor('#b91c1c')
    header_title = '📜 لوح تقدیر و تشویق کلاسی' if is_positive else '⚠️ برگه پیگیری انضباطی کلاسی'
    
    c.setFillColor(bg_color)
    c.rect(0, h-90, w, 90, fill=1, stroke=0)
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(font_name, 14)
    c.drawCentredString(w/2, h-35, _rtl('دبستان پسرانه هیئت امنایی شهید مطهری مهران'))
    c.setFont(font_name, 12)
    c.drawCentredString(w/2, h-65, _rtl(header_title))
    
    y = h - 130
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 11)
    c.drawRightString(w - 50, y, _rtl(f'نام دانش‌آموز: {student_name}'))
    c.drawRightString(w - 240, y, _rtl(f'کد ملی: {national_id}'))
    c.drawRightString(w - 400, y, _rtl(f'تاریخ ثبت: {date_str}'))
    
    y -= 50
    c.setFillColor(HexColor('#f8fafc'))
    c.setStrokeColor(HexColor('#cbd5e1'))
    c.rect(40, y-100, w-80, 100, fill=1, stroke=1)
    
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 12)
    c.drawRightString(w - 60, y - 25, _rtl(f'عنوان مشاهده: {title}'))
    c.setFont(font_name, 10)
    c.drawRightString(w - 60, y - 55, _rtl(f'توضیحات آموزگار: {desc}'))
    
    y -= 160
    c.drawRightString(w - 60, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
    c.drawRightString(180, y, _rtl('مهر و امضای مدیریت مدرسه'))
    
    c.save()
    return buf.getvalue()

def generate_portfolio_report_html(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str):
    return f"""
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 2px solid #3b82f6; border-radius: 14px; padding: 20px; color: #ffffff; margin-bottom: 20px;">
        <h3 style="color: #60a5fa !important; margin: 0 0 6px 0;">🏛️ دبستان پسرانه هیئت امنایی شهید مطهری مهران</h3>
        <h4 style="color: #f59e0b !important; margin: 0;">📜 برگه رسمی کارنامه و پوشه کار دیجیتال (سال تحصیلی ۱۴۰۴-۱۴۰۵)</h4>
        <hr style="border-color: rgba(255, 255, 255, 0.15); margin: 12px 0;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; font-size: 0.95rem;">
            <div>👤 <b>نام دانش‌آموز:</b> {student_name}</div>
            <div>🆔 <b>کد ملی:</b> {national_id}</div>
            <div>🚀 <b>گروه کلاسی:</b> {student_group}</div>
            <div>📱 <b>تلفن اولیا:</b> {parent_phone}</div>
            <div>📊 <b>تعداد ارزشیابی‌ها:</b> {eval_count} درس</div>
            <div>🌟 <b>موارد رفتاری:</b> {beh_count} مورد</div>
            <div>✏️ <b>میانگین درصد آزمون:</b> {quiz_avg_str}</div>
        </div>
    </div>
    """

# Teacher Auth State Init
if 'teacher_authenticated' not in st.session_state:
    st.session_state['teacher_authenticated'] = False
if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 0

def check_teacher_auth():
    if not st.session_state['teacher_authenticated']:
        st.info("🔐 جهت دسترسی به این بخش، رمزیار آموزگار (پیش‌فرض: 1234) را وارد کنید:")
        pwd_input = st.text_input("رمز عبور آموزگار:", type="password", key="auth_pass_input")
        if st.button("ورود به حساب آموزگار", key="btn_auth_login"):
            with get_connection() as conn:
                real_pwd = conn.execute("SELECT password FROM teacher_auth WHERE id = 1").fetchone()[0]
            if pwd_input == real_pwd:
                st.session_state['teacher_authenticated'] = True
                st.success("ورود موفقیت‌آمیز بود!")
                st.rerun()
            else:
                st.error("رمز عبور اشتباه است.")
        st.stop()

# ---------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------
st.sidebar.title("🎓 مدیریت کلاس پنجم")
st.sidebar.markdown("**دبستان شهید مطهری مهران**")
st.sidebar.markdown("---")

menu_options = [
    "1️⃣ 🏠 صفحه اصلی و معرفی سامانه",
    "2️⃣ 👨‍🎓 مدیریت پرونده اسامی دانش‌آموزان",
    "3️⃣ 📝 ارزشیابی توصیفی و کیفی ۷ درس",
    "4️⃣ 🌟 مشاهدات رفتاری و انضباطی",
    "5️⃣ ✏️ طراحی و مدیریت آزمون‌های آنلاین",
    "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
    "7️⃣ 📊 کارنامه و پوشه کار دیجیتال"
]

menu_choice = st.sidebar.radio("منوی اصلی دسترسی:", menu_options)

if st.session_state['teacher_authenticated']:
    if st.sidebar.button("🔒 خروج از حساب آموزگار"):
        st.session_state['teacher_authenticated'] = False
        st.rerun()

# ---------------------------------------------------------
# 1. HOME PAGE
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.title("🎓 سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین")
    st.subheader("دبستان پسرانه هیئت امنایی شهید مطهری مهران - سال تحصیلی ۱۴۰۴-۱۴۰۵")
    
    col_h1, col_h2 = st.columns([2, 1])
    with col_h1:
        st.markdown("""
        ### 👋 به سامانه مدیریت هوشمند کلاس پنجم خوش آمدید!
        این سامانه جامع جهت تسهیل امور آموزشی، ثبت ارزشیابی‌های کیفی-توصیفی ۷ عنوان درسی، ثبت رفتاری و برگزاری آزمون‌های آنلاین با تصحیح هوشمند برای دانش‌آموزان و اولیای محترم طراحی شده است.
        """)
        st.info("📊 **ثبت ارزشیابی ۷ درس:** ریاضی، علوم تجربی، فارسی (خوانداری)، نگارش فارسی، مطالعات اجتماعی، هدیه‌های آسمان و آموزش قرآن")
        st.success("📱 **آزمون آنلاین هوشمند:** برگزاری آزمون‌های تستی با کارنامه آنی دانش‌آموز")
    with col_h2:
        with get_connection() as conn:
            st_count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
            ev_count = conn.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0]
            qz_count = conn.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]
        st.metric("تعداد دانش‌آموزان ثبت‌شده:", f"{st_count} نفر")
        st.metric("کل ارزشیابی‌های ثبت‌شده:", f"{ev_count} مورد")
        st.metric("تعداد آزمون‌های فعال:", f"{qz_count} آزمون")

# ---------------------------------------------------------
# 2. STUDENT MANAGEMENT (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت پرونده و اسامی دانش‌آموزان")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 لیست دانش‌آموزان", "➕ ثبت فردی", "⚡ بارگذاری ۲۹ دانش‌آموز کلاس", "📊 اکسل سفارشی"])
    
    with tab1:
        students_df = load_students()
        if not students_df.empty:
            st.dataframe(
                students_df[['id', 'first_name', 'last_name', 'national_id', 'pin_code', 'parent_phone', 'student_group']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("هنوز هیچ دانش‌آموزی ثبت نشده است. از زبانه 'بارگذاری ۲۹ دانش‌آموز کلاس' استفاده کنید.")

    with tab2:
        with st.form("add_single_student"):
            c1, c2 = st.columns(2)
            with c1:
                fn = st.text_input("نام:*")
                nid = st.text_input("کد ملی:")
                grp = st.selectbox("گروه کلاسی:", CLASS_GROUPS)
            with c2:
                ln = st.text_input("نام خانوادگی:*")
                ph = st.text_input("شماره همراه اولیا:")
                pin = st.text_input("رمز اختصاصی ورود دانش‌آموز:", value="1234")
            
            if st.form_submit_button("💾 ثبت دانش‌آموز"):
                if fn.strip() and ln.strip():
                    try:
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO students (first_name, last_name, national_id, pin_code, parent_phone, student_group, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (fn.strip(), ln.strip(), nid.strip(), pin.strip(), ph.strip(), grp, get_current_shamsi_date())
                            )
                            conn.commit()
                        st.success(f"دانش‌آموز {fn} {ln} با موفقیت ثبت شد.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("کد ملی تکراری است.")
                else:
                    st.warning("نام و نام خانوادگی الزامی است.")

    with tab3:
        st.subheader("⚡ بارگذاری فوری ۲۹ دانش‌آموز رسمی پایه پنجم مطهری")
        st.write("با کلیک روی دکمه زیر، اسامی ۲۹ دانش‌آموز کلاس به طور کامل با گروه‌بندی رسمی در دیتابیس بارگذاری می‌شوند:")
        if st.button("🚀 بارگذاری ۲۹ دانش‌آموز کلاس در دیتابیس", key="btn_load_29_official"):
            official_29 = [
                ("امیرعلی", "احمدی", "1001112233", "1234", "09181111111", "گروه ارمغان 🚀"),
                ("محمدیاسین", "حیدری", "1002223344", "1234", "09182222222", "گروه دانا 💡"),
                ("سیدعلی", "موسوی", "1003334455", "1234", "09183333333", "گروه تلاش 🌟"),
                ("ابوالفضل", "رضایی", "1004445566", "1234", "09184444444", "گروه نخبگان 🏆"),
                ("امیرمحمد", "کرمی", "1005556677", "1234", "09185555555", "گروه اندیشه 📖"),
                ("حسین", "محمدی", "1006667788", "1234", "09186666666", "گروه ارمغان 🚀"),
                ("علیرضا", "نوری", "1007778899", "1234", "09187777777", "گروه دانا 💡"),
                ("مهدی", "صادقی", "1008889900", "1234", "09188888888", "گروه تلاش 🌟"),
                ("پارسا", "عباسی", "1009990011", "1234", "09189999999", "گروه نخبگان 🏆"),
                ("شایان", "جعفری", "1010001122", "1234", "09180001122", "گروه اندیشه 📖"),
                ("امیرحسین", "قاسمی", "1011112233", "1234", "09181112233", "گروه ارمغان 🚀"),
                ("امیررضا", "مرادی", "1012223344", "1234", "09182223344", "گروه دانا 💡"),
                ("آرتین", "ابراهیمی", "1013334455", "1234", "09183334455", "گروه تلاش 🌟"),
                ("محمدامين", "نجفی", "1014445566", "1234", "09184445566", "گروه نخبگان 🏆"),
                ("طاها", "موسوی نژاد", "1015556677", "1234", "09185556677", "گروه اندیشه 📖"),
                ("سبحان", "عسگری", "1016667788", "1234", "09186667788", "گروه ارمغان 🚀"),
                ("محمدمهدی", "شریفی", "1017778899", "1234", "09187778899", "گروه دانا 💡"),
                ("ایلیا", "خانی", "1018889900", "1234", "09188889900", "گروه تلاش 🌟"),
                ("کیان", "رستمی", "1019990011", "1234", "09189990011", "گروه نخبگان 🏆"),
                ("مانی", "فتحی", "1020001122", "1234", "09180002233", "گروه اندیشه 📖"),
                ("بنیامين", "کاظمی", "1021112233", "1234", "09181113344", "گروه ارمغان 🚀"),
                ("دانیال", "حسینی", "1022223344", "1234", "09182224455", "گروه دانا 💡"),
                ("سامان", "مطهری", "1023334455", "1234", "09183335566", "گروه تلاش 🌟"),
                ("علی", "باقری", "1024445566", "1234", "09184446677", "گروه نخبگان 🏆"),
                ("ارشیان", "امیری", "1025556677", "1234", "09185557788", "گروه اندیشه 📖"),
                ("ماهان", "احمدی نژاد", "1026667788", "1234", "09186668899", "گروه ارمغان 🚀"),
                ("متین", "سلیمانی", "1027778899", "1234", "09187779900", "گروه دانا 💡"),
                ("پویا", "یعقوبی", "1028889900", "1234", "09188880011", "گروه تلاش 🌟"),
                ("یاسین", "ملکی", "1029990011", "1234", "09189991122", "گروه نخبگان 🏆")
            ]
            shamsi_today = get_current_shamsi_date()
            added_cnt = 0
            with get_connection() as conn:
                for fn, ln, nid, pin, ph, grp in official_29:
                    try:
                        conn.execute(
                            "INSERT INTO students (first_name, last_name, national_id, pin_code, parent_phone, student_group, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (fn, ln, nid, pin, ph, grp, shamsi_today)
                        )
                        added_cnt += 1
                    except sqlite3.IntegrityError:
                        pass
                conn.commit()
            st.success(f"🎉 تعداد {added_cnt} دانش‌آموز رسمی پایه پنجم با موفقیت در دیتابیس ثبت گردیدند.")
            st.rerun()

    with tab4:
        st.subheader("📊 بارگذاری هوشمند فایل اکسل اسامی")
        st.info("فایل اکسل می‌تواند شامل ستون‌های 'نام'، 'نام خانوادگی' (یا 'نام و نام خانوادگی')، 'کد ملی'، 'تلفن اولیا' و 'گروه کلاسی' باشد.")
        
        uploaded_file = st.file_uploader("فایل اکسل (xlsx) یا (csv) اسامی را آپلود کنید:", type=["xlsx", "csv"], key="excel_uploader_v84")
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_raw = pd.read_csv(uploaded_file)
                else:
                    df_raw = pd.read_excel(uploaded_file)
                    
                parsed_students = parse_students_excel_smart(df_raw)
                
                if parsed_students:
                    st.success(f"🎉 تعداد {len(parsed_students)} دانش‌آموز با موفقیت استخراج و پردازش گردید.")
                    preview_df = pd.DataFrame(parsed_students)[['first_name', 'last_name', 'national_id', 'parent_phone', 'student_group']]
                    preview_df.columns = ['نام', 'نام خانوادگی', 'کد ملی', 'تلفن اولیا', 'گروه کلاسی']
                    st.dataframe(preview_df, use_container_width=True)
                    
                    if st.button("⚡ ذخیره تمام اسامی فوق در دیتابیس", key="btn_save_parsed_excel"):
                        shamsi_today = get_current_shamsi_date()
                        cnt = 0
                        with get_connection() as conn:
                            for p in parsed_students:
                                try:
                                    conn.execute(
                                        "INSERT INTO students (first_name, last_name, national_id, pin_code, parent_phone, student_group, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                        (p['first_name'], p['last_name'], p['national_id'], p['pin_code'], p['parent_phone'], p['student_group'], shamsi_today)
                                    )
                                    cnt += 1
                                except sqlite3.IntegrityError:
                                    pass
                            conn.commit()
                        st.success(f"🎉 تعداد {cnt} دانش‌آموز با موفقیت وارد دیتابیس شدند.")
                        st.rerun()
                else:
                    st.error("هیچ اسمی در فایل اکسل آپلودشده پیدا نشد. لطفاً از صحت ستون‌های فایل مطمئن شوید.")
            except Exception as e:
                st.error(f"خطا در خواندن فایل اکسل: {e}")

# ---------------------------------------------------------
# 3. QUALITATIVE EVALUATION (TEACHER ONLY - 7 SUBJECTS)
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی توصیفی و کیفی ۷ درس پایه پنجم")
    
    students_df = load_students()
    if students_df.empty:
        st.info("دانش‌آموزی ثبت نشده است.")
    else:
        eval_mode_tab1, eval_mode_tab2 = st.tabs(["📝 ثبت همزمان ارزشیابی ۷ درس (کامل و یکجا)", "📝 ثبت تکی تک‌درس"])
        
        with eval_mode_tab1:
            st.subheader("🌟 ثبت ارزشیابی جامع تمام ۷ درس در یک صفحه")
            sel_st_all = st.selectbox("انتخاب دانش‌آموز جهت ارزشیابی:*", students_df['full_name'].tolist(), key="sel_st_eval_7")
            st_id_7 = int(students_df[students_df['full_name'] == sel_st_all]['id'].values[0])
            
            with st.form("form_eval_7_subjects"):
                eval_date_7 = st.text_input("تاریخ ثبت ارزشیابی (شمسی):", value=get_current_shamsi_date(), key="date_eval_7")
                
                inputs_7 = {}
                for idx, subj in enumerate(FIFTH_GRADE_SUBJECTS):
                    st.markdown(f"##### 📌 **{idx+1}. درس {subj}**")
                    col_e1, col_e2 = st.columns([1, 2])
                    with col_e1:
                        lvl = st.selectbox(f"سطح عملکرد ({subj}):", EVALUATION_LEVELS, key=f"lvl_{idx}")
                    with col_e2:
                        fb = st.text_input(f"توصیف و بازخورد آموزگار ({subj}):", value="عملکرد خوب و رضایت‌بخش در مفاهیم آموزشی", key=f"fb_{idx}")
                    inputs_7[subj] = (lvl, fb)
                    st.markdown("---")
                    
                if st.form_submit_button("💾 ثبت همزمان ارزشیابی تمامی ۷ درس"):
                    with get_connection() as conn:
                        for subj, (lvl, fb) in inputs_7.items():
                            conn.execute(
                                "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                                (st_id_7, subj, lvl, fb.strip(), eval_date_7.strip())
                            )
                        conn.commit()
                    st.success(f"🎉 ارزشیابی تمامی ۷ درس برای دانش‌آموز **{sel_st_all}** با موفقیت ثبت گردید.")
                    st.rerun()

        with eval_mode_tab2:
            with st.form("eval_single_form"):
                col_ev1, col_e2 = st.columns(2)
                with col_ev1:
                    selected_student = st.selectbox("انتخاب دانش‌آموز:*", students_df['full_name'].tolist(), key="sel_st_single_eval")
                    selected_subject = st.selectbox("انتخاب درس:*", FIFTH_GRADE_SUBJECTS, key="sel_subj_single")
                with col_e2:
                    selected_level = st.selectbox("سطح عملکرد توصیفی:*", EVALUATION_LEVELS, key="sel_lvl_single")
                    eval_date = st.text_input("تاریخ ارزشیابی (شمسی):", value=get_current_shamsi_date(), key="date_single_eval")
                    
                feedback_text = st.text_area("توصیف عملکرد معلم و توصیه‌های آموزشی:", value="عملکرد مناسب در تکالیف و فعالیت‌های کلاسی")
                
                if st.form_submit_button("💾 ثبت ارزشیابی این درس"):
                    s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
                    with get_connection() as conn:
                        conn.execute(
                            "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                            (s_id, selected_subject, selected_level, feedback_text.strip(), eval_date.strip())
                        )
                        conn.commit()
                    st.success(f"ارزشیابی درس {selected_subject} برای {selected_student} با موفقیت ثبت شد.")
                    st.rerun()

# ---------------------------------------------------------
# 4. BEHAVIORAL LOGS (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("4"):
    check_teacher_auth()
    st.header("🌟 ثبت مشاهدات رفتاری و انضباطی کلاسی")
    
    students_df = load_students()
    if students_df.empty:
        st.info("دانش‌آموزی ثبت نشده است.")
    else:
        col_b1, col_b2 = st.columns([1, 1])
        with col_b1:
            with st.form("behavior_form"):
                st.subheader("➕ ثبت مشاهده جدید")
                selected_student = st.selectbox("انتخاب دانش‌آموز:*", students_df['full_name'].tolist())
                b_type = st.selectbox("نوع مشاهده:*", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
                title = st.text_input("عنوان کوتاه (مثلاً: مسئولیت‌پذیری، نظم):*")
                desc = st.text_area("توضیحات تکمیلی مشاهده رفتاری:")
                log_date = st.text_input("تاریخ ثبت:", value=get_current_shamsi_date())
                
                if st.form_submit_button("💾 ثبت مورد رفتاری"):
                    if title.strip():
                        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                                (s_id, b_type, title.strip(), desc.strip(), log_date.strip())
                            )
                            conn.commit()
                        st.success(f"مورد رفتاری برای {selected_student} با موفقیت ثبت شد.")
                        st.rerun()
                    else:
                        st.warning("عنوان کوتاه الزامی است.")
        
        with col_b2:
            st.subheader("📋 سوابق رفتاری اخیر")
            with get_connection() as conn:
                beh_df = safe_read_sql(
                    "SELECT b.id, (s.first_name || ' ' || s.last_name) AS student_name, b.behavior_type, b.title, b.log_date FROM behaviors b JOIN students s ON b.student_id = s.id ORDER BY b.id DESC LIMIT 15",
                    conn
                )
            if not beh_df.empty:
                st.dataframe(beh_df, use_container_width=True, hide_index=True)
            else:
                st.info("هنوز مورد رفتاری ثبت نشده است.")

# ---------------------------------------------------------
# 5. ONLINE QUIZ MANAGEMENT (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ طراحی و مدیریت آزمون‌های آنلاین پنجم")
    
    q_tab1, q_tab2 = st.tabs(["📝 طراحی آزمون جدید", "📋 مدیریت آزمون‌ها و سوالات"])
    
    with q_tab1:
        with st.form("create_quiz_form"):
            st.subheader("➕ ساخت آزمون جدید")
            q_title = st.text_input("عنوان آزمون:* (مثلاً: آزمون علوم فصل اول)")
            q_subj = st.selectbox("درس مربوطه:*", FIFTH_GRADE_SUBJECTS)
            q_dur = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=120, value=15)
            
            if st.form_submit_button("🔨 ایجاد آزمون"):
                if q_title.strip():
                    with get_connection() as conn:
                        conn.execute(
                            "INSERT INTO quizzes (title, subject, duration_minutes, created_at) VALUES (?, ?, ?, ?)",
                            (q_title.strip(), q_subj, q_dur, get_current_shamsi_date())
                        )
                        conn.commit()
                    st.success(f"آزمون '{q_title}' ساخته شد. اکنون سوالات را اضافه کنید.")
                    st.rerun()

    with q_tab2:
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT * FROM quizzes ORDER BY id DESC", conn)
        if not quizzes_df.empty:
            sel_quiz_title = st.selectbox("انتخاب آزمون جهت مدیریت سوالات:", quizzes_df['title'].tolist())
            q_row = quizzes_df[quizzes_df['title'] == sel_quiz_title].iloc[0]
            q_id = int(q_row['id'])
            
            st.info(f"آزمون: {q_row['title']} | درس: {q_row['subject']} | زمان: {q_row['duration_minutes']} دقیقه")
            
            with st.form("add_q_form"):
                st.subheader("➕ افزودن سوال جدید به این آزمون")
                q_text = st.text_area("متن سوال:*")
                c1, c2 = st.columns(2)
                with c1:
                    op1 = st.text_input("گزینه ۱:*")
                    op3 = st.text_input("گزینه ۳:*")
                with c2:
                    op2 = st.text_input("گزینه ۲:*")
                    op4 = st.text_input("گزینه ۴:*")
                correct_op = st.selectbox("گزینه صحیح:*", [1, 2, 3, 4])
                
                if st.form_submit_button("💾 افزودن سوال"):
                    if q_text.strip() and op1.strip() and op2.strip():
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO questions (quiz_id, question_text, option_1, option_2, option_3, option_4, correct_option) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (q_id, q_text.strip(), op1.strip(), op2.strip(), op3.strip(), op4.strip(), correct_op)
                            )
                            conn.commit()
                        st.success("سوال با موفقیت اضافه شد.")
                        st.rerun()

# ---------------------------------------------------------
# 6. TAKE ONLINE QUIZ (STUDENT VIEW)
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین (ویژه دانش‌آموزان)")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = safe_read_sql("SELECT * FROM quizzes WHERE is_active = 1 ORDER BY id DESC", conn)
        
    if students_df.empty or quizzes_df.empty:
        st.warning("آزمون فعالی یا دانش‌آموزی در سامانه وجود ندارد.")
    else:
        col_q1, col_q2 = st.columns([1, 2])
        with col_q1:
            sel_st_q = st.selectbox("دانش‌آموز:*", students_df['full_name'].tolist(), key="q_st_sel")
            pin_q = st.text_input("رمز ورود اختصاصی (پیش‌فرض 1234):", type="password", key="q_pin_input")
            selected_quiz_q = st.selectbox("آزمون آنلاین:*", quizzes_df['title'].tolist(), key="q_take_quiz")
            
        st_row_q = students_df[students_df['full_name'] == sel_st_q].iloc[0]
        real_pin_q = str(st_row_q['pin_code']) if st_row_q['pin_code'] else "1234"
        
        if pin_q == real_pin_q:
            q_id_q = int(quizzes_df[quizzes_df['title'] == selected_quiz_q]['id'].values[0])
            with get_connection() as conn:
                questions_df = safe_read_sql("SELECT * FROM questions WHERE quiz_id = ?", conn, params=(q_id_q,))
                
            if questions_df.empty:
                st.info("این آزمون هنوز سوالی ندارد.")
            else:
                st.success(f"تعداد {len(questions_df)} سوال برای آزمون '{selected_quiz_q}' آماده پاسخگویی است.")
                
                with st.form("quiz_submit_form"):
                    student_answers = {}
                    for idx, q in questions_df.iterrows():
                        st.markdown(f"**سوال {idx+1}: {q['question_text']}**")
                        opts = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                        student_answers[q['id']] = st.radio(f"انتخاب گزینه (سوال {idx+1}):", opts, key=f"q_ans_{q['id']}")
                        st.markdown("---")
                        
                    if st.form_submit_button("🏁 ثبت نهایی آزمون و دریافت کارنامه"):
                        correct_count = 0
                        total_q = len(questions_df)
                        for idx, q in questions_df.iterrows():
                            ans = student_answers.get(q['id'])
                            corr_idx = int(q['correct_option']) - 1
                            if ans == [q['option_1'], q['option_2'], q['option_3'], q['option_4']][corr_idx]:
                                correct_count += 1
                        score_pct = (correct_count / total_q) * 100.0 if total_q > 0 else 0.0
                        
                        s_id_q = int(st_row_q['id'])
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, submitted_at) VALUES (?, ?, ?, ?, ?, ?)",
                                (q_id_q, s_id_q, correct_count, total_q, score_pct, get_current_shamsi_date())
                            )
                            conn.commit()
                        st.success(f"🎉 آزمون با موفقیت ثبت شد! نمره‌ی شما: {correct_count} از {total_q} (درصد: {score_pct:.1f}٪)")
                        st.balloons()

# ---------------------------------------------------------
# 7. COMPREHENSIVE REPORT CARD & PORTFOLIO
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 کارنامه و پوشه کار دیجیتال دانش‌آموز")
    
    students_df = load_students()
    if students_df.empty:
        st.info("دانش‌آموزی ثبت نشده است.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده کارنامه:*", students_df['full_name'].tolist())
        st_row = students_df[students_df['full_name'] == selected_student].iloc[0]
        s_id = int(st_row['id'])
        
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg_str = f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون"
            nat_id_str = st_row['national_id'] or 'ثبت نشده'
            phone_str = st_row['parent_phone'] or 'ثبت نشده'
            grp_str = st_row['student_group'] or 'بدون گروه'

        portfolio_html = generate_portfolio_report_html(selected_student, nat_id_str, phone_str, grp_str, eval_count, beh_count, quiz_avg_str)
        st.markdown(portfolio_html, unsafe_allow_html=True)

        portfolio_pdf = generate_comprehensive_portfolio_pdf(s_id)
        st.download_button(
            "📥 دانلود فایل پی دی اف کارنامه رسمی ۷ درس (PDF معتبر قابل پرینت)",
            data=portfolio_pdf,
            file_name=f"report_card_{selected_student}.pdf",
            mime="application/pdf"
        )
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with c2:
            st.metric("موارد رفتاری ثبت‌شده:", beh_count)
        with c3:
            st.metric("میانگین درصد آزمون آنلاین:", quiz_avg_str)

        st.markdown("---")

        tab_d1, tab_d2, tab_d3 = st.tabs(["📝 ارزشیابی‌های ۷ درس", "🌟 سوابق رفتاری", "📊 کارنامه آزمون‌ها"])

        with tab_d1:
            with get_connection() as conn:
                df_e = safe_read_sql("SELECT subject AS 'عنوان درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد معلم', eval_date AS 'تاریخ (شمسی)' FROM evaluations WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,))
            if not df_e.empty:
                st.dataframe(df_e, use_container_width=True, hide_index=True)
            else:
                st.info("ارزشیابی درسی ثبت نشده است.")

        with tab_d2:
            with get_connection() as conn:
                df_b = safe_read_sql("SELECT id, behavior_type AS 'نوع', title AS 'عنوان رفتار', description AS 'توضیحات تکمیلی', log_date AS 'تاریخ (شمسی)' FROM behaviors WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,))
            if not df_b.empty:
                st.dataframe(df_b.drop(columns=['id'], errors='ignore'), use_container_width=True, hide_index=True)
            else:
                st.info("مورد رفتاری ثبت نشده است.")

        with tab_d3:
            with get_connection() as conn:
                df_q = safe_read_sql("SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره', r.total_questions AS 'کل سوالات', r.percentage AS 'درصد ٪', r.submitted_at AS 'تاریخ ثبت' FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.id DESC", conn, params=(s_id,))
            if not df_q.empty:
                st.dataframe(df_q, use_container_width=True, hide_index=True)
            else:
                st.info("آزمون آنلاینی ثبت نشده است.")

