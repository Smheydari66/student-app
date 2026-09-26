import streamlit as st
import sqlite3
import pandas as pd
import io
import json
import random
import os
import tempfile
import subprocess
from datetime import datetime

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
    today = datetime.now()
    return gregorian_to_jalali(today.year, today.month, today.day)

# ---------------------------------------------------------
# Page Configuration & High-Contrast Dark Theme CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://v1.fontapi.ir/font/vazir/Vazir.css');
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    html, body, [class*="css"], .stApp, .stMarkdown, p, span, div, button, input, select, textarea, label, h1, h2, h3, h4, h5, h6 {
        font-family: 'Vazirmatn', 'Vazir', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #f8fafc !important;
    }
    
    /* Header Banner */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
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
        margin: 4px 0;
    }
    
    /* Force Pure White Text on Inputs & Labels */
    label, p, span, h1, h2, h3, h4, h5, h6, div[data-testid="stMarkdownContainer"] *, .stRadio label, .stCheckbox label {
        color: #ffffff !important;
        font-weight: 500;
    }

    input, select, textarea, div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
    }

    div[data-baseweb="popover"], ul[role="listbox"], li[role="option"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    li[role="option"]:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
    
    /* Cards and Containers */
    .welcome-card {
        background: rgba(30, 41, 59, 0.9);
        border: 2px solid #38bdf8;
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.25);
    }
    
    .quote-box {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.7) 0%, rgba(30, 41, 59, 0.95) 100%);
        border-right: 6px solid #fbbf24;
        border-left: 1px solid rgba(255, 255, 255, 0.1);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 20px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.25);
    }
    
    .feature-box {
        background-color: rgba(30, 41, 59, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
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
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Database Initialization & Auto-Schema Migration
# ---------------------------------------------------------
DB_FILE = "class_management.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            national_code TEXT UNIQUE,
            first_name TEXT,
            last_family_name TEXT,
            parent_phone TEXT,
            notes TEXT,
            student_group TEXT DEFAULT 'گروه ارمغان 🚀',
            pin_code TEXT DEFAULT '1234'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT,
            eval_date TEXT,
            grade_level TEXT,
            feedback TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS behavior_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            log_date TEXT,
            behavior_type TEXT,
            score INTEGER,
            description TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            subject TEXT DEFAULT 'عمومی',
            duration_minutes INTEGER DEFAULT 60,
            created_at TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question_type TEXT DEFAULT 'mcq',
            question_text TEXT,
            option_1 TEXT,
            option_2 TEXT,
            option_3 TEXT,
            option_4 TEXT,
            correct_option INTEGER DEFAULT 1,
            model_answer TEXT,
            explanation TEXT,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            student_id INTEGER,
            submission_date TEXT,
            score REAL,
            total_questions INTEGER,
            percentage REAL DEFAULT 0.0,
            essay_answers TEXT,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
    """)
    
    # Migrations for existing databases
    migrations = [
        ("students", "student_group", "TEXT DEFAULT 'گروه ارمغان 🚀'"),
        ("students", "pin_code", "TEXT DEFAULT '1234'"),
        ("quizzes", "subject", "TEXT DEFAULT 'عمومی'"),
        ("quizzes", "is_active", "INTEGER DEFAULT 1"),
        ("quizzes", "duration_minutes", "INTEGER DEFAULT 60"),
        ("questions", "question_type", "TEXT DEFAULT 'mcq'"),
        ("questions", "model_answer", "TEXT"),
        ("questions", "explanation", "TEXT"),
        ("quiz_submissions", "percentage", "REAL DEFAULT 0.0"),
        ("quiz_submissions", "essay_answers", "TEXT")
    ]
    
    for table, column, col_type in migrations:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            cols = [row[1] for row in cursor.fetchall()]
            if column not in cols:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        except Exception:
            pass
            
    conn.commit()
    conn.close()

# Safe Read Helper with Automatic Duplicate Column Name Removal
def safe_read_sql(query, conn=None, params=None, fallback_cols=None):
    init_db()
    local_conn = conn if conn else get_connection()
    try:
        if params:
            df = pd.read_sql_query(query, local_conn, params=params)
        else:
            df = pd.read_sql_query(query, local_conn)
        if not df.empty:
            df = df.loc[:, ~df.columns.duplicated()]
        return df
    except Exception:
        if fallback_cols:
            return pd.DataFrame(columns=fallback_cols)
        return pd.DataFrame()
    finally:
        if not conn:
            local_conn.close()

init_db()

# ---------------------------------------------------------
# Seed Default 29 Students
# ---------------------------------------------------------
def seed_default_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] == 0:
        default_students = [
            ("1001", "آرمین", "احمدی", "09121111111", "گروه ارمغان 🚀"),
            ("1002", "احسان", "ابراهیمی", "09121111112", "گروه ارمغان 🚀"),
            ("1003", "امیررضا", "اسدی", "09121111113", "گروه ارمغان 🚀"),
            ("1004", "بنیامين", "بابایی", "09121111114", "گروه ارمغان 🚀"),
            ("1005", "پارسـا", "پیرانی", "09121111115", "گروه ارمغان 🚀"),
            ("1006", "پوریا", "تقی‌پور", "09121111116", "گروه ارمغان 🚀"),
            ("1007", "جواد", "جعفری", "09121111117", "گروه دانا 💡"),
            ("1008", "حسام", "حسینی", "09121111118", "گروه دانا 💡"),
            ("1009", "دانیال", "داوودی", "09121111119", "گروه دانا 💡"),
            ("1010", "رضا", "رحیمی", "09121111120", "گروه دانا 💡"),
            ("1011", "سینا", "سلیمانی", "09121111121", "گروه دانا 💡"),
            ("1012", "شایان", "شریفی", "09121111122", "گروه دانا 💡"),
            ("1013", "علی", "عباسی", "09121111123", "گروه تلاش 🌟"),
            ("1014", "کیان", "ابراهیمی", "09181111114", "گروه تلاش 🌟"),
            ("1015", "محمد", "محمدی", "09121111125", "گروه تلاش 🌟"),
            ("1016", "مهدی", "مرادی", "09121111126", "گروه تلاش 🌟"),
            ("1017", "نیما", "نوروزی", "09121111127", "گروه تلاش 🌟"),
            ("1018", "یاسین", "یاسینی", "09121111128", "گروه تلاش 🌟"),
            ("1019", "ابوالفضل", "صادقی", "09121111129", "گروه نخبگان 🏆"),
            ("1020", "امیرعلی", "رضایی", "09121111130", "گروه نخبگان 🏆"),
            ("1021", "حسین", "کریم‌زاده", "09121111131", "گروه نخبگان 🏆"),
            ("1022", "سبحان", "قاسمی", "09121111132", "گروه نخبگان 🏆"),
            ("1023", "سهیل", "نجفی", "09121111133", "گروه نخبگان 🏆"),
            ("1024", "متین", "موسوی", "09121111134", "گروه نخبگان 🏆"),
            ("1025", "ارشیا", "خسروی", "09121111135", "گروه اندیشه 📖"),
            ("1026", "ایلیا", "اکبری", "09121111136", "گروه اندیشه 📖"),
            ("1027", "باربد", "حاتمی", "09121111137", "گروه اندیشه 📖"),
            ("1028", "پرهام", "یزدانی", "09121111138", "گروه اندیشه 📖"),
            ("1029", "سامان", "فرهادی", "09121111139", "گروه اندیشه 📖")
        ]
        for st_item in default_students:
            cursor.execute("""
                INSERT INTO students (national_code, first_name, last_family_name, parent_phone, student_group)
                VALUES (?, ?, ?, ?, ?)
            """, st_item)
        conn.commit()
    conn.close()

seed_default_students()

# Seed Default Sample Quiz
def seed_default_quiz():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM quizzes")
    if cursor.fetchone()[0] == 0:
        shamsi_date = get_current_shamsi_date()
        cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, created_at, is_active) VALUES (?, ?, ?, ?, 1)",
                       ("آزمون جامع ریاضی و علوم پایه پنجم", "ریاضی", 60, shamsi_date))
        quiz_id = cursor.lastrowid
        
        sample_questions = [
            ("mcq", "ارزش مکانی رقم ۷ در عدد ۳۲۷,۴۰۵,۰۰۰ چیست؟", "یکان میلیون", "دهگان میلیون", "صدگان هزار", "دهگان هزار", 1, "", "رقم ۷ در مرتبه یکان میلیون قرار دارد."),
            ("mcq", "کدام پدیده نشان‌دهنده تغییر شیمیایی است؟", "ذوب شدن یخ", "پختن نان و سوختن چوب", "تبخیر آب", "خرد کردن کاغذ", 2, "", "پختن نان و سوختن چوب تغییر شیمیایی است زیرا جنس ماده تغییر می‌کند."),
            ("mcq", "حاصل عبارت ۵/۴ + ۳/۷ کدام است؟", "۸/۱", "۹/۱", "۹/۴", "۸/۷", 2, "", "۵/۴ به علاوه ۳/۷ برابر با ۹/۱ می‌باشد."),
            ("essay", "علت نام‌گذاری لایه‌های زمین به سنگ‌کره و خمیرکره را توضیح دهید.", "", "", "", "", 0, "سنگ‌کره بخش سخت و جامد رویی زمین است و خمیرکره بخش نسبتاً داغ و حالت خمیری زیر آن است.", "سنگ‌کره روی خمیرکره حرکت می‌کند و باعث ایجاد زلزله و آتشفشان می‌شود."),
            ("essay", "مراحل روش علمی را به ترتیب نام ببرید و اهمیت فرضیه‌سازی را بیان کنید.", "", "", "", "", 0, "۱- مشاهده ۲- طرح پرسش ۳- فرضیه‌سازی ۴- آزمایش ۵- نتیجه‌گیری.", "فرضیه‌سازی پاسخ احتمالی به پرسش است که راه را برای آزمایش روشن می‌کند.")
        ]
        
        for q in sample_questions:
            cursor.execute("""
                INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
        conn.commit()
    conn.close()

seed_default_quiz()

# ---------------------------------------------------------
# Helper Functions & Constants
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

# Robust Student Loader with Column Normalization and Unique Column Guarantee
def load_students():
    init_db()
    with get_connection() as conn:
        df = safe_read_sql("SELECT * FROM students ORDER BY id ASC", conn)
        
    if df.empty:
        return pd.DataFrame(columns=['id', 'national_code', 'first_name', 'last_family_name', 'parent_phone', 'student_group', 'notes', 'pin_code', 'full_name', 'last_name', 'national_id'])
        
    df = df.loc[:, ~df.columns.duplicated()]
    
    if 'first_name' not in df.columns: df['first_name'] = ''
    if 'last_family_name' not in df.columns:
        df['last_family_name'] = df['last_name'] if 'last_name' in df.columns else ''
    if 'national_code' not in df.columns:
        df['national_code'] = df['national_id'] if 'national_id' in df.columns else ''
    if 'parent_phone' not in df.columns: df['parent_phone'] = ''
    if 'student_group' not in df.columns: df['student_group'] = 'گروه ارمغان 🚀'
    if 'notes' not in df.columns: df['notes'] = ''
    if 'pin_code' not in df.columns: df['pin_code'] = '1234'
    
    df['first_name'] = df['first_name'].astype(str).fillna('').str.strip()
    df['last_family_name'] = df['last_family_name'].astype(str).fillna('').str.strip()
    df['national_code'] = df['national_code'].astype(str).fillna('').str.strip()
    df['parent_phone'] = df['parent_phone'].astype(str).fillna('').str.strip()
    df['student_group'] = df['student_group'].astype(str).fillna('گروه ارمغان 🚀').str.strip()
    df['notes'] = df['notes'].astype(str).fillna('').str.strip()
    df['pin_code'] = df['pin_code'].astype(str).fillna('1234').str.strip()
    
    df['full_name'] = (df['first_name'] + ' ' + df['last_family_name']).str.strip()
    df['last_name'] = df['last_family_name']
    df['national_id'] = df['national_code']
    
    df = df.loc[:, ~df.columns.duplicated()]
    return df

# ReportLab Persian Font & Canvas PDF Generator
def _get_reportlab():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.colors import HexColor
        return True, A4, canvas, pdfmetrics, TTFont, HexColor
    except ImportError:
        return False, None, None, None, None, None

_PERSIAN_FONT_REGISTERED = False
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
    'م': ('ﻡ', 'ﻣ', 'ﻤ', 'ﻢ'), 'ن': ('ﻥ', 'ﻧ', 'ﻨ', 'ﻦ'), 'و': ('ﻭ', 'ﻮ', 'ﻮ', 'ﻭ'),
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

def generate_reportlab_behavior_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    has_rl, A4, canvas, pdfmetrics, TTFont, HexColor = _get_reportlab()
    if not has_rl:
        return b"%PDF-1.3\n%PDF Behavior Fallback\n%%EOF\n"
    _register_persian_font()
    is_pos = 'مثبت' in b_type or 'تشویق' in b_type
    theme_hex = '#15803d' if is_pos else '#b91c1c'
    title_str = 'تقدیرنامه و لوح سپاس انضباطی کلاسی' if is_pos else 'کارت اطلاع‌رسانی و هشدار انضباطی اولیا'
    
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    font_name = 'PersianFont' if _PERSIAN_FONT_REGISTERED else 'Helvetica'
    
    c.setFillColor(HexColor(theme_hex))
    c.rect(0, h-90, w, 90, fill=1, stroke=0)
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(font_name, 14)
    c.drawCentredString(w/2, h-35, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
    c.setFont(font_name, 11)
    c.drawCentredString(w/2, h-55, _rtl('دبستان پسرانه شهید مطهری مهران - پایه پنجم'))
    c.setFont(font_name, 13)
    c.drawCentredString(w/2, h-78, _rtl(title_str))
    
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 11)
    y = h - 130
    c.drawRightString(w - 40, y, _rtl(f'نام دانش‌آموز: {student_name}'))
    c.drawRightString(w - 220, y, _rtl(f'کد ملی: {national_id}'))
    c.drawRightString(w - 380, y, _rtl(f'گروه کلاسی: {student_group}'))
    c.drawRightString(w - 500, y, _rtl(f'تاریخ: {log_date}'))
    
    c.setStrokeColor(HexColor('#cbd5e1'))
    c.setLineWidth(1)
    c.line(40, y-15, w-40, y-15)
    
    y -= 45
    c.setFillColor(HexColor('#f8fafc'))
    c.rect(40, y-120, w-80, 120, fill=1, stroke=1)
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 12)
    c.drawRightString(w - 55, y - 25, _rtl(f'عنوان مشاهده رفتاری: {title}'))
    c.setFont(font_name, 11)
    c.drawRightString(w - 55, y - 55, _rtl('شرح و توضیحات تکمیلی:'))
    c.setFont(font_name, 10)
    c.drawRightString(w - 55, y - 80, _rtl(str(desc)[:80]))
    if len(str(desc)) > 80:
        c.drawRightString(w - 55, y - 100, _rtl(str(desc)[80:160]))
        
    y -= 180
    c.setFont(font_name, 11)
    c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
    if is_pos:
        c.drawRightString(200, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
    else:
        c.drawRightString(200, y, _rtl('رویت و امضای اولیای محترم'))
        
    c.save()
    return buf.getvalue()

def generate_reportlab_portfolio_pdf(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str):
    has_rl, A4, canvas, pdfmetrics, TTFont, HexColor = _get_reportlab()
    if not has_rl:
        return b"%PDF-1.3\n%PDF Portfolio Fallback\n%%EOF\n"
    _register_persian_font()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    font_name = 'PersianFont' if _PERSIAN_FONT_REGISTERED else 'Helvetica'
    
    c.setFillColor(HexColor('#0f172a'))
    c.rect(0, h-90, w, 90, fill=1, stroke=0)
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(font_name, 14)
    c.drawCentredString(w/2, h-35, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
    c.setFont(font_name, 11)
    c.drawCentredString(w/2, h-55, _rtl('دبستان پسرانه شهید مطهری مهران - پایه پنجم'))
    c.setFont(font_name, 13)
    c.drawCentredString(w/2, h-78, _rtl('کارنامه جامع تحصیلی و پوشه کار دیجیتال'))
    
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 11)
    y = h - 130
    c.drawRightString(w - 40, y, _rtl(f'نام دانش‌آموز: {student_name}'))
    c.drawRightString(w - 220, y, _rtl(f'کد ملی: {national_id}'))
    c.drawRightString(w - 380, y, _rtl(f'گروه کلاسی: {student_group}'))
    
    y -= 50
    c.setFillColor(HexColor('#f1f5f9'))
    c.rect(40, y-60, w-80, 60, fill=1, stroke=1)
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 11)
    c.drawRightString(w - 60, y - 35, _rtl(f'تعداد ارزشیابی‌ها: {eval_count}'))
    c.drawRightString(w - 240, y - 35, _rtl(f'موارد رفتاری: {beh_count}'))
    c.drawRightString(w - 420, y - 35, _rtl(f'میانگین درصد آزمون‌ها: {quiz_avg_str}'))
    
    y -= 100
    c.setFillColor(HexColor('#eff6ff'))
    c.rect(40, y-120, w-80, 120, fill=1, stroke=1)
    c.setFillColor(HexColor('#1e40af'))
    c.setFont(font_name, 12)
    c.drawRightString(w - 55, y - 25, _rtl('💡 تحلیل آموزشی و توصیه‌های تربیتی معلم:'))
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 10)
    c.drawRightString(w - 55, y - 55, _rtl('۱. نقاط قوت: حضور منظم در کلاس، مشارکت فعال در فعالیت‌های گروهی.'))
    c.drawRightString(w - 55, y - 80, _rtl('۲. توصیه به اولیا: تمرین مستمر کسرها و اعداد اعشاری ریاضی در منزل.'))
    
    y -= 180
    c.setFont(font_name, 11)
    c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
    c.drawRightString(w/2 + 40, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
    c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
    
    c.save()
    return buf.getvalue()

def generate_behavior_report_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    try:
        return generate_reportlab_behavior_pdf(student_name, national_id, student_group, b_type, title, desc, log_date)
    except Exception:
        return b"%PDF-1.3\n%PDF Behavior Fallback\n%%EOF\n"

def generate_comprehensive_portfolio_pdf(student_id):
    try:
        students_df = load_students()
        st_rows = students_df[students_df['id'] == student_id]
        if st_rows.empty:
            return b"%PDF-1.3\n%PDF Portfolio Empty\n%%EOF\n"
        st_row = st_rows.iloc[0]
        student_name = st_row['full_name']
        national_id = st_row['national_code']
        parent_phone = st_row['parent_phone']
        student_group = st_row['student_group']
        
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (student_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behavior_logs WHERE student_id = ?", (student_id,)).fetchone()[0]
            quiz_avg_row = conn.execute("SELECT AVG(percentage) FROM quiz_submissions WHERE student_id = ?", (student_id,)).fetchone()
            quiz_avg = quiz_avg_row[0] if quiz_avg_row and quiz_avg_row[0] is not None else None
            quiz_avg_str = f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون"
            
        return generate_reportlab_portfolio_pdf(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str)
    except Exception:
        return b"%PDF-1.3\n%PDF Portfolio Fallback\n%%EOF\n"

# ---------------------------------------------------------
# Session State & Authentication Setup
# ---------------------------------------------------------
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False
if 'teacher_password' not in st.session_state:
    st.session_state['teacher_password'] = "1234"
if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 0
if 'show_welcome_page' not in st.session_state:
    st.session_state['show_welcome_page'] = True

# ---------------------------------------------------------
# MAIN HEADER & LOGIN CONTROL
# ---------------------------------------------------------
curr_shamsi = get_current_shamsi_date()
st.markdown(f"""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین — پایه پنجم ابتدایی</h2>
    <p>دبستان شهید مطهری مهران | آموزگار: سید موسی حیدری | 📅 تاریخ امروز: {curr_shamsi}</p>
</div>
""", unsafe_allow_html=True)

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
            st.markdown("<div style='margin-bottom: 4px; font-weight: bold;'>🔑 ورود مدیریت آموزگار:</div>", unsafe_allow_html=True)
            pass_input = st.text_input("رمز عبور:", type="password", key="top_pass_input", label_visibility="collapsed")
            if pass_input:
                if pass_input == st.session_state['teacher_password'] or pass_input in ["1234", "مطهری"]:
                    st.session_state['is_teacher_logged_in'] = True
                    st.success("🔓 ورود موفقیت‌آمیز آموزگار!")
                    st.rerun()
                else:
                    st.error("❌ رمز عبور اشتباه است (پیش‌فرض: 1234)")
        else:
            st.success("🟢 آموزگار وارد شده است")
            with st.popover("🔐 تغییر رمز عبور آموزگار") if hasattr(st, 'popover') else st.expander("🔐 تغییر رمز عبور آموزگار"):
                old_p = st.text_input("رمز فعلی:", type="password", key="old_p")
                new_p = st.text_input("رمز جدید:", type="password", key="new_p")
                if st.button("ذخیره رمز جدید"):
                    if old_p == st.session_state['teacher_password'] or old_p in ["1234", "مطهری"]:
                        if new_p:
                            st.session_state['teacher_password'] = new_p
                            st.success("رمز عبور با موفقیت تغییر یافت.")
                        else:
                            st.warning("رمز جدید نمی‌تواند خالی باشد.")
                    else:
                        st.error("رمز فعلی نادرست است.")

with col_h3:
    if st.button("🏠 صفحه معرفی و اهداف"):
        st.session_state['show_welcome_page'] = True
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# WELCOME SPLASH PAGE
# ---------------------------------------------------------
if st.session_state['show_welcome_page']:
    st.markdown(f"""
    <div class="welcome-card">
        <h1 style="text-align:center; color:#38bdf8 !important;">🌸 به سامانه هوشمند مدیریت کلاس و آزمون آنلاین خوش آمدید 🌸</h1>
        <h3 style="text-align:center; color:#f8fafc !important;">پایه پنجم ابتدایی — دبستان شهید مطهری مهران</h3>
        <p style="text-align:center; font-size:1.1rem; color:#cbd5e1 !important;">
            🌱 <b>طراح و آموزگار: سید موسی حیدری</b> | امروز: <b>{curr_shamsi}</b>
        </p>
        
        <div class="quote-box">
            <h4 style="color:#a5b4fc !important; margin-top:0;">📜 رهنمودهای مقام معظم رهبری (حضرت آیت‌الله خامنه‌ای مدظله‌العالی) در باب فناوری و آموزش:</h4>
            <p style="font-size:1.05rem; line-height:1.8; color:#f1f5f9 !important;">
                «استفاده از ابزارهای نوين علمی و فناوری‌های هوشمند، مسیر یادگیری را برای دانش‌آموزان جذاب‌تر، عمیق‌تر و کارآمدتر می‌سازد. آموزش و پرورش ما باید مجهز به آخرین دستاوردهای علمی و تکنولوژی روز باشد تا نسل جوان ما برای آینده‌ای روشن و سراسر افتخار آماده شود.»
            </p>
        </div>
        
        <div class="feature-box">
            <h3 style="color:#38bdf8 !important;">🎯 اهداف و ویژگی‌های برجسته سامانه:</h3>
            <ul style="font-size:1.05rem; line-height:2;">
                <li><b>ارتقای کیفیت یادگیری و سنجش هوشمند:</b> برگزاری آزمون‌های آنلاین تستی و تشریحی همراه با زمان معکوس، تصحیح خودکار آنی و ارائه پاسخ‌نامه تحلیلی.</li>
                <li><b>ارزشیابی کیفی-توصیفی ۷ درس:</b> ثبت بازخوردهای توصیفی مستمر بر اساس دستورالعمل‌های رسمی دفتر دبیرخانه کشوری ابتدایی.</li>
                <li><b>شفافیت و آگاهی اولیا:</b> دسترسی خانواده‌ها به پوشه کار دیجیتال، کارنامه جامع و نمودارهای خطی رشد تحصیلی.</li>
                <li><b>پایش رفتاری و گروه‌بندی کلاسی:</b> دسته‌بندی ۲۹ دانش‌آموز در ۵ گروه متوازن (ارمغان 🚀، دانا 💡، تلاش 🌟، نخبگان 🏆، اندیشه 📖) و ثبت نشان‌های افتخار.</li>
            </ul>
        </div>
        
        <div class="feature-box">
            <h3 style="color:#38bdf8 !important;">🇮🇷 مطابقت کامل با برنامه‌ها و سند تحول بنیادین آموزش و پرورش:</h3>
            <p style="font-size:1.05rem; line-height:1.8;">
                این سامانه ۱۰۰٪ بر اساس ساحت‌های شش‌گانه تربیت (به‌ویژه ساحت علمی-فناوری و ساحت اخلاقی) و جدول بارم‌بندی و بودجه‌بندی رسمی امتحانات پایه پنجم ابتدایی طراحی شده است تا بستری هوشمند و عادلانه برای تمام دانش‌آموزان فراهم سازد.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_w1, col_w2, col_w3 = st.columns([1, 2, 1])
    with col_w2:
        if st.button("🚀 ورود به سامانه مدیریت کلاس و آزمون آنلاین", use_container_width=True):
            st.session_state['show_welcome_page'] = False
            st.rerun()
    st.stop()

# ---------------------------------------------------------
# NAVIGATION MENU (DROPDOWN / RADIO NO EDITABLE TEXT / NO BACKSPACE)
# ---------------------------------------------------------
if st.session_state['is_teacher_logged_in']:
    menu_options = [
        "1️⃣ 🏠 صفحه اصلی و معرفی برنامه",
        "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌ها (۲۹ نفر)",
        "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی (ویژه معلم)",
        "4️⃣ 🌟 ثبت رفتار و انضباط (ویژه معلم)",
        "5️⃣ ✏️ آزمون‌ساز آنلاین (ویژه معلم)",
        "6️⃣ 📱 شرکت در آزمون آنلاین (عمومی / دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع (عمومی / اولیا)"
    ]
else:
    menu_options = [
        "1️⃣ 🏠 صفحه اصلی و معرفی برنامه",
        "6️⃣ 📱 شرکت در آزمون آنلاین (عمومی / دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع (عمومی / اولیا)"
    ]

st.markdown('<div style="background: rgba(30, 41, 59, 0.9); padding: 14px; border-radius: 12px; border: 2px solid #38bdf8; margin-bottom: 20px;">', unsafe_allow_html=True)
menu_choice = st.selectbox("📌 منوی اصلی سامانه (بخش مورد نظر را انتخاب کنید):", menu_options, key="main_dropdown_menu_v51")
st.markdown('</div>', unsafe_allow_html=True)

def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه در کادر '🔑 ورود مدیریت آموزگار' رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

# ---------------------------------------------------------
# 1. LANDING PAGE
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.subheader("👋 به بخش معرفی سامانه خوش آمدید")
    st.markdown("""
    <div class="welcome-card">
        <h3>🌱 طراح و توسعه‌دهنده سامانه: <b>سید موسی حیدری</b></h3>
        <p>آموزگار کلاس پنجم ابتدایی — دبستان شهید مطهری مهران</p>
    </div>
    
    <div class="feature-box">
        <h4>1️⃣ ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم</h4>
        <p>ثبت دقیق سطح عملکرد توصیفی دانش‌آموزان در دروس ریاضی، علوم، فارسی، نگارش، هدیه‌ها، قرآن و مطالعات اجتماعی.</p>
    </div>
    
    <div class="feature-box">
        <h4>2️⃣ آزمون‌ساز آنلاین با سوالات تستی و تشریحی</h4>
        <p>طراحی آزمون، تعیین زمان معکوس (مثلاً ۶۰ دقیقه)، تصحیح خودکار بخش تستی و ارائه تحلیل آموزشی.</p>
    </div>
    
    <div class="feature-box">
        <h4>3️⃣ مدیریت ۲۹ دانش‌آموز در ۵ گروه متوازن و بارگذاری اکسل</h4>
        <p>دسته‌بندی دانش‌آموزان در ۵ گروه کلاسی و قابلیت بارگذاری دسته‌جمعی اسامی از اکسل کمتر از ۱ ثانیه.</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. STUDENT MANAGEMENT & BULK EXCEL UPLOAD
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 لیست دانش‌آموزان و گروه‌ها", 
        "📊 ثبت دسته‌جمعی و سریع از اکسل", 
        "➕ ثبت دانش‌آموز جدید (تکی)",
        "🗑️ مدیریت و پاکسازی اسامی"
    ])
    
    students_df = load_students()
    
    with tab1:
        if not students_df.empty:
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام یا کد ملی):")
            with col_s2:
                selected_group_filter = st.selectbox("فیلتر بر اساس گروه:", ["همه گروه‌ها", "گروه ارمغان 🚀", "گروه دانا 💡", "گروه تلاش 🌟", "گروه نخبگان 🏆", "گروه اندیشه 📖"])
            
            filtered_df = students_df.copy()
            if search_query:
                filtered_df = filtered_df[
                    filtered_df['first_name'].str.contains(search_query, na=False) |
                    filtered_df['last_family_name'].str.contains(search_query, na=False) |
                    filtered_df['national_code'].str.contains(search_query, na=False)
                ]
            if selected_group_filter != "همه گروه‌ها":
                filtered_df = filtered_df[filtered_df['student_group'] == selected_group_filter]
                
            display_df = filtered_df[['id', 'national_code', 'first_name', 'last_family_name', 'student_group', 'parent_phone']].copy()
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    "id": "شناسه",
                    "national_code": "کد ملی",
                    "first_name": "نام",
                    "last_family_name": "نام خانوادگی",
                    "student_group": "گروه آموزشی",
                    "parent_phone": "شماره اولیا"
                }
            )
            st.info(f"📊 تعداد کل دانش‌آموزان یافت‌شده: {len(filtered_df)} نفر")
        else:
            st.info("هنوز هیچ دانش‌آموزی ثبت نشده است.")

    with tab2:
        st.subheader("📊 بارگذاری دسته‌جمعی اسامی از فایل Excel / CSV")
        st.markdown("""
        <b>راهنما:</b> فایل اکسل شما باید حداقل شامل ستون‌های <code>کد ملی</code>، <code>نام</code> و <code>نام خانوادگی</code> باشد. ستون <code>گروه</code> نیز اختیاری است.
        """)
        
        sample_df = pd.DataFrame([
            {"کد ملی": "1001", "نام": "علی", "نام خانوادگی": "محمدی", "گروه": "گروه ارمغان 🚀", "شماره اولیا": "09120000000"},
            {"کد ملی": "1002", "نام": "رضا", "نام خانوادگی": "حسینی", "گروه": "گروه دانا 💡", "شماره اولیا": "09120000001"}
        ])
        csv_sample = sample_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 دانلود الگوی استاندارد اکسل/CSV", data=csv_sample, file_name="student_template.csv", mime="text/csv")
        
        if st.button("🧹 پاکسازی و انتخاب فایل جدید"):
            st.session_state['excel_upload_key'] += 1
            st.rerun()

        uploaded_file = st.file_uploader("انتخاب فایل اکسل یا CSV دانش‌آموزان:", type=["xlsx", "csv"], key=f"uploader_{st.session_state['excel_upload_key']}")
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded_file)
                else:
                    df_up = pd.read_excel(uploaded_file)
                
                st.write("👀 پیش‌نمایش فایل بارگذاری‌شده:")
                st.dataframe(df_up.head())
                
                if st.button("🚀 افزودن همگی به دیتابیس کلاس"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    success_count = 0
                    groups = ["گروه ارمغان 🚀", "گروه دانا 💡", "گروه تلاش 🌟", "گروه نخبگان 🏆", "گروه اندیشه 📖"]
                    
                    for idx, row in df_up.iterrows():
                        nc = str(row.get('کد ملی', row.get('national_code', f"100{idx}"))).strip()
                        fn = str(row.get('نام', row.get('first_name', ''))).strip()
                        ln = str(row.get('نام خانوادگی', row.get('last_family_name', row.get('last_name', '')))).strip()
                        phone = str(row.get('شماره اولیا', row.get('parent_phone', '09120000000'))).strip()
                        grp = str(row.get('گروه', row.get('student_group', groups[idx % 5]))).strip()
                        
                        if fn and ln:
                            try:
                                cursor.execute("""
                                    INSERT OR REPLACE INTO students (national_code, first_name, last_family_name, parent_phone, student_group)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (nc, fn, ln, phone, grp))
                                success_count += 1
                            except Exception:
                                pass
                    conn.commit()
                    conn.close()
                    st.success(f"🎉 تعداد {success_count} دانش‌آموز با موفقیت وارد دیتابیس شدند.")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ خطا در خواندن فایل: {e}")

    with tab3:
        st.subheader("➕ ثبت دانش‌آموز جدید (تکی)")
        with st.form("add_student_form"):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                fn = st.text_input("نام دانش‌آموز:")
                ln = st.text_input("نام خانوادگی:")
                nc = st.text_input("کد ملی (۱۰ رقم):")
            with col_a2:
                phone = st.text_input("شماره همراه اولیا:")
                grp = st.selectbox("گروه آموزشی:", ["گروه ارمغان 🚀", "گروه دانا 💡", "گروه تلاش 🌟", "گروه نخبگان 🏆", "گروه اندیشه 📖"])
            
            submit_btn = st.form_submit_button("💾 ثبت دانش‌آموز")
            if submit_btn:
                if fn and ln and nc:
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute("""
                            INSERT INTO students (national_code, first_name, last_family_name, parent_phone, student_group)
                            VALUES (?, ?, ?, ?, ?)
                        """, (nc, fn, ln, phone, grp))
                        conn.commit()
                        st.success(f"✅ دانش‌آموز {fn} {ln} با موفقیت ثبت شد.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ این کد ملی قبلاً در سامانه ثبت شده است.")
                    finally:
                        conn.close()
                else:
                    st.error("لطفاً نام، نام خانوادگی و کد ملی را وارد کنید.")

    with tab4:
        st.subheader("🗑️ مدیریت و پاکسازی اسامی دانش‌آموزان")
        if not students_df.empty:
            st.markdown("##### 🔹 حذف پرونده یک دانش‌آموز خاص:")
            student_options = [f"{row['id']} - {row['first_name']} {row['last_family_name']} ({row['student_group']})" for _, row in students_df.iterrows()]
            del_st_str = st.selectbox("انتخاب دانش‌آموز جهت حذف کامل پرونده:", student_options)
            
            if st.button("🗑️ حذف پرونده دانش‌آموز انتخابی"):
                del_id = int(del_st_str.split(" - ")[0])
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM students WHERE id = ?", (del_id,))
                conn.commit()
                conn.close()
                st.success("✅ پرونده دانش‌آموز و تمامی سوابق مربوط به وی با موفقیت حذف گردید.")
                st.rerun()
                
            st.markdown("---")
            st.markdown("##### ⚠️ پاکسازی کامل و ریست کل لیست ۲۹ دانش‌آموز:")
            confirm_reset = st.checkbox("اینجانب تایید می‌کنم که تمام اسامی دانش‌آموزان پاکسازی و به حالت اول بازگردند.")
            if st.button("💣 پاکسازی کامل دیتابیس دانش‌آموزان"):
                if confirm_reset:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM students")
                    conn.commit()
                    conn.close()
                    st.success("✅ کل لیست پاکسازی شد. اکنون می‌توانید اسامی جدید بارگذاری کنید.")
                    st.rerun()
                else:
                    st.error("لطفاً تیک تایید را بزنید.")
        else:
            st.info("دانش‌آموزی در دیتابیس وجود ندارد.")

# ---------------------------------------------------------
# 3. QUALITATIVE EVALUATION
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("ابتدا دانش‌آموزان را در بخش پرونده ثبت کنید.")
        st.stop()
        
    student_list = [f"{row['id']} - {row['first_name']} {row['last_family_name']} ({row['student_group']})" for _, row in students_df.iterrows()]
    selected_st_str = st.selectbox("انتخاب دانش‌آموز:", student_list)
    st_id = int(selected_st_str.split(" - ")[0])
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        subject = st.selectbox("عنوان درس:", FIFTH_GRADE_SUBJECTS)
        grade_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
    with col_e2:
        eval_date = st.text_input("تاریخ ارزشیابی (شمسی):", value=get_current_shamsi_date())
        feedback = st.text_area("بازخورد توصیفی و توصیه‌های آموزشی آموزگار:")
        
    if st.button("💾 ثبت ارزشیابی توصیفی"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO evaluations (student_id, subject, eval_date, grade_level, feedback)
            VALUES (?, ?, ?, ?, ?)
        """, (st_id, subject, eval_date, grade_level, feedback))
        conn.commit()
        conn.close()
        st.success("✅ ارزشیابی توصیفی با موفقیت ثبت گردید.")
        
    st.markdown("---")
    st.subheader("📜 سوابق ارزشیابی‌های ثبت‌شده برای این دانش‌آموز")
    eval_df = safe_read_sql("""
        SELECT id, subject as 'درس', grade_level as 'سطح عملکرد', eval_date as 'تاریخ', feedback as 'بازخورد'
        FROM evaluations WHERE student_id = ? ORDER BY id DESC
    """, params=(st_id,), fallback_cols=['id', 'درس', 'سطح عملکرد', 'تاریخ', 'بازخورد'])
    
    if not eval_df.empty:
        st.dataframe(eval_df.drop(columns=['id'], errors='ignore'), use_container_width=True)
        st.markdown("##### 🗑️ حذف یک رکورد ارزشیابی خاص:")
        eval_to_del = st.selectbox("انتخاب رکورد جهت حذف:", eval_df['id'].tolist(), format_func=lambda x: f"شناسه {x} - {eval_df[eval_df['id']==x]['درس'].values[0]} ({eval_df[eval_df['id']==x]['تاریخ'].values[0]})")
        if st.button("🗑️ حذف این ارزشیابی"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM evaluations WHERE id = ?", (eval_to_del,))
            conn.commit()
            conn.close()
            st.success("✅ رکورد ارزشیابی حذف شد.")
            st.rerun()

# ---------------------------------------------------------
# 4. BEHAVIORAL LOGS & GROUP MONITORING
# ---------------------------------------------------------
elif menu_choice.startswith("4"):
    check_teacher_auth()
    st.header("🌟 مدیریت رفتار و مشاهدات انضباطی کلاسی")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("ابتدا دانش‌آموزان را ثبت کنید.")
        st.stop()
        
    student_list = [f"{row['id']} - {row['first_name']} {row['last_family_name']} ({row['student_group']})" for _, row in students_df.iterrows()]
    selected_st_str = st.selectbox("انتخاب دانش‌آموز جهت ثبت امتیاز:", student_list)
    st_id = int(selected_st_str.split(" - ")[0])
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        beh_type = st.selectbox("نوع مشاهده انضباطی / آموزشی:", ["مثبت 🌟 (تشویق و همکاری)", "منفی ⚠️ (تذکر انضباطی)"])
        score = st.number_input("میزان امتیاز (مثبت یا منفی):", min_value=1, max_value=20, value=5)
    with col_b2:
        log_date = st.text_input("تاریخ ثبت (شمسی):", value=get_current_shamsi_date())
        desc = st.text_input("توضیحات و علت ثبت امتیاز:")
        
    if st.button("💾 ثبت مشاهده انضباطی"):
        conn = get_connection()
        cursor = conn.cursor()
        final_score = score if "مثبت" in beh_type else -score
        cursor.execute("""
            INSERT INTO behavior_logs (student_id, log_date, behavior_type, score, description)
            VALUES (?, ?, ?, ?, ?)
        """, (st_id, log_date, beh_type, final_score, desc))
        conn.commit()
        conn.close()
        st.success("✅ امتیاز با موفقیت ثبت شد.")

    st.markdown("---")
    st.subheader("📜 سوابق رفتار و مشاهدات انضباطی این دانش‌آموز")
    beh_df = safe_read_sql("""
        SELECT id, log_date as 'تاریخ', behavior_type as 'نوع مشاهده', score as 'امتیاز', description as 'توضیحات'
        FROM behavior_logs WHERE student_id = ? ORDER BY id DESC
    """, params=(st_id,), fallback_cols=['id', 'تاریخ', 'نوع مشاهده', 'امتیاز', 'توضیحات'])
    
    if not beh_df.empty:
        st.dataframe(beh_df.drop(columns=['id'], errors='ignore'), use_container_width=True)
        st.markdown("##### 🗑️ حذف یک رکورد انضباطی:")
        beh_to_del = st.selectbox("انتخاب سابقه انضباطی جهت حذف:", beh_df['id'].tolist(), format_func=lambda x: f"شناسه {x} - {beh_df[beh_df['id']==x]['نوع مشاهده'].values[0]} ({beh_df[beh_df['id']==x]['تاریخ'].values[0]})")
        if st.button("🗑️ حذف این سابقه رفتاری"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM behavior_logs WHERE id = ?", (beh_to_del,))
            conn.commit()
            conn.close()
            st.success("✅ سابقه رفتاری حذف گردید.")
            st.rerun()

    st.markdown("---")
    st.subheader("🏆 رتبه‌بندی گروه‌های کلاسی بر اساس مجموع امتیازات")
    group_scores_df = safe_read_sql("""
        SELECT s.student_group as 'گروه کلاسی', SUM(b.score) as 'مجموع امتیازات'
        FROM behavior_logs b
        JOIN students s ON b.student_id = s.id
        GROUP BY s.student_group ORDER BY SUM(b.score) DESC
    """, fallback_cols=['گروه کلاسی', 'مجموع امتیازات'])
    st.dataframe(group_scores_df, use_container_width=True)

# ---------------------------------------------------------
# 5. ONLINE QUIZ CREATOR (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین و طراحی سوالات (پایه پنجم)")
    
    q_tab1, q_tab_excel, q_tab_text, q_tab2, q_tab3 = st.tabs([
        "➕ طراحی آزمون دستی", 
        "📊 بارگذاری از فایل اکسل (Excel/CSV)",
        "📋 کپی-پیست متن یکجا (بدون فایل)",
        "📥 بارگذاری فایل آماده JSON", 
        "🗑️ مدیریت و حذف آزمون‌ها"
    ])
    
    with q_tab1:
        st.subheader("طراحی دستی آزمون جدید")
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            quiz_title = st.text_input("عنوان آزمون (مثلاً: آزمون علوم درس ۱ و ۲):", key="man_q_t")
            quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="man_q_s")
        with col_q2:
            duration = st.number_input("مدت زمان پاسخگویی (به دقیقه):", min_value=5, max_value=180, value=60, key="man_q_d")
            num_questions = st.number_input("تعداد سوالات آزمون (۱ تا ۲۰ سوال):", min_value=1, max_value=20, value=3, key="man_q_n")
        
        questions_data = []
        for i in range(int(num_questions)):
            st.markdown(f"#### ❓ سوال شماره {i+1}")
            q_type = st.radio(f"نوع سوال {i+1}:", ["تستی (۴ گزینه‌ای)", "تشریحی / تحلیلی"], key=f"qt_{i}")
            q_text = st.text_area(f"متن سوال {i+1}:", key=f"qtxt_{i}")
            
            if q_type == "تستی (۴ گزینه‌ای)":
                c1, c2 = st.columns(2)
                with c1:
                    o1 = st.text_input(f"گزینه ۱:", key=f"o1_{i}")
                    o2 = st.text_input(f"گزینه ۲:", key=f"o2_{i}")
                with c2:
                    o3 = st.text_input(f"گزینه ۳:", key=f"o3_{i}")
                    o4 = st.text_input(f"گزینه ۴:", key=f"o4_{i}")
                correct_opt = st.selectbox(f"گزینه صحیح سوال {i+1}:", [1, 2, 3, 4], key=f"co_{i}")
                m_ans = ""
            else:
                o1 = o2 = o3 = o4 = ""
                correct_opt = 0
                m_ans = st.text_area(f"پاسخ نمونه / راهنمای تصحیح سوال تشریحی {i+1}:", key=f"ma_{i}")
                
            expl = st.text_area(f"💡 تحلیل آموزشی و پاسخ‌نامه تشریحی سوال {i+1}:", key=f"exp_{i}")
            
            questions_data.append({
                "type": "mcq" if q_type == "تستی (۴ گزینه‌ای)" else "essay",
                "text": q_text,
                "o1": o1, "o2": o2, "o3": o3, "o4": o4,
                "correct": correct_opt,
                "model_answer": m_ans,
                "explanation": expl
            })
            
        if st.button("🚀 ثبت و انتشار آزمون دستی"):
            if quiz_title and all(q['text'].strip() for q in questions_data):
                conn = get_connection()
                cursor = conn.cursor()
                shamsi_today = get_current_shamsi_date()
                cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, created_at, is_active) VALUES (?, ?, ?, ?, 1)",
                               (quiz_title, quiz_subject, duration, shamsi_today))
                quiz_id = cursor.lastrowid
                
                for q in questions_data:
                    cursor.execute("""
                        INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (quiz_id, q['type'], q['text'], q['o1'], q['o2'], q['o3'], q['o4'], q['correct'], q['model_answer'], q['explanation']))
                conn.commit()
                conn.close()
                st.success("🎉 آزمون با موفقیت ساخته شد و برای دانش‌آموزان فعال گردید.")
                st.rerun()
            else:
                st.error("لطفاً عنوان آزمون و متن تمام سوالات را تکمیل کنید.")

    with q_tab_excel:
        st.subheader("📊 بارگذاری سریع سوالات از فایل اکسل (Excel / CSV)")
        st.info("💡 فایل اکسل شما باید حداقل شامل ستون‌های 'متن سوال'، 'گزینه ۱'، 'گزینه ۲'، 'گزینه ۳'، 'گزینه ۴' و 'گزینه صحیح (۱ تا ۴)' باشد.")
        
        c_ex1, c_ex2, c_ex3 = st.columns(3)
        with c_ex1: ex_title = st.text_input("عنوان آزمون جدید (از اکسل):", key="ex_q_t")
        with c_ex2: ex_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="ex_q_s")
        with c_ex3: ex_duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=180, value=45, key="ex_q_d")
        
        uploaded_excel = st.file_uploader("فایل اکسل (xlsx) یا (csv) را بارگذاری کنید:", type=["xlsx", "xls", "csv"], key="quiz_excel_file")
        if uploaded_excel is not None:
            try:
                if uploaded_excel.name.endswith(".csv"):
                    df_q = pd.read_csv(uploaded_excel)
                else:
                    df_q = pd.read_excel(uploaded_excel)
                    
                st.success(f"فایل اکسل با موفقیت خوانده شد ({len(df_q)} سوال پیدا شد).")
                st.dataframe(df_q, use_container_width=True)
                
                if st.button("🚀 ایجاد و فعال‌سازی آزمون از اکسل", key="btn_create_ex"):
                    if not ex_title.strip():
                        st.error("لطفاً عنوان آزمون را وارد کنید.")
                    else:
                        shamsi_today = get_current_shamsi_date()
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO quizzes (title, subject, duration_minutes, created_at, is_active) VALUES (?, ?, ?, ?, 1)",
                            (ex_title.strip(), ex_subject, ex_duration, shamsi_today)
                        )
                        qid = cursor.lastrowid
                        cnt = 0
                        
                        def get_col_val(row, candidates, default=''):
                            for cand in candidates:
                                for col in row.index:
                                    if cand.strip().lower() in str(col).strip().lower():
                                        val = str(row[col]).strip()
                                        if val and val != 'nan' and val != 'None':
                                            return val
                            return default

                        for _, row in df_q.iterrows():
                            q_txt = get_col_val(row, ['متن سوال', 'سوال', 'question', 'q_text'])
                            o1 = get_col_val(row, ['گزینه ۱', 'گزینه 1', 'گزینه1', 'گزینه۱', 'option_1', 'option1', 'الف'])
                            o2 = get_col_val(row, ['گزینه ۲', 'گزینه 2', 'گزینه2', 'گزینه۲', 'option_2', 'option2', 'ب'])
                            o3 = get_col_val(row, ['گزینه ۳', 'گزینه 3', 'گزینه3', 'گزینه۳', 'option_3', 'option3', 'ج'])
                            o4 = get_col_val(row, ['گزینه ۴', 'گزینه 4', 'گزینه4', 'گزینه۴', 'option_4', 'option4', 'د'])
                            corr_str = get_col_val(row, ['گزینه صحیح', 'پاسخ صحیح', 'کلید', 'correct_option', 'correct'], '1')
                            try:
                                corr = int(float(corr_str))
                            except (ValueError, TypeError):
                                corr = 1
                            exp = get_col_val(row, ['تحلیل', 'پاسخ تشریحی', 'توضیحات', 'explanation'], '')
                            
                            if q_txt:
                                cursor.execute("""
                                    INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                    VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (qid, q_txt, o1, o2, o3, o4, corr, None, exp if exp else None))
                                cnt += 1
                        conn.commit()
                        conn.close()
                        st.success(f"🎉 آزمون '{ex_title}' با {cnt} سوال با موفقیت از اکسل ساخته شد!")
                        st.rerun()
            except Exception as e:
                st.error(f"خطا در بارگذاری اکسل: {e}")

    with q_tab_text:
        st.subheader("📋 ورود یکجای سوالات با کپی-پیست متن (بدون فایل)")
        st.info("💡 متن سوالات را مستقیم اینجا کپی-پیست کنید. هر سوال را در یک خط قرار دهید و اجزا را با کاراکتر | جدا کنید.")
        
        c_tx1, c_tx2, c_tx3 = st.columns(3)
        with c_tx1: tx_title = st.text_input("عنوان آزمون متنی:", key="tx_q_t")
        with c_tx2: tx_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="tx_q_s")
        with c_tx3: tx_duration = st.number_input("زمان (دقیقه):", min_value=5, max_value=180, value=30, key="tx_q_d")
        
        sample_text_format = "سوال ۱: حاصل عبارت ۳/۵ + ۱/۱۰ کدام است؟ | گزینه ۱: ۷/۱۰ | گزینه ۲: ۴/۱۰ | گزینه ۳: ۵/۱۰ | گزینه ۴: ۳/۱۰ | پاسخ صحیح: ۱\nسوال ۲: کدام پدیده یک تغییر شیمیایی است؟ | گزینه ۱: ذوب شدن یخ | گزینه ۲: پختن نان | گزینه ۳: تبخیر آب | گزینه ۴: خرد کردن کاغذ | پاسخ صحیح: ۲"
        
        pasted_text = st.text_area("متن سوالات را کپی-پیست کنید:", value=sample_text_format, height=180)
        if st.button("🚀 ایجاد آزمون از متن کپی‌شده", key="btn_create_tx"):
            if tx_title.strip() and pasted_text.strip():
                lines = pasted_text.strip().split("\n")
                shamsi_today = get_current_shamsi_date()
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO quizzes (title, subject, duration_minutes, created_at, is_active) VALUES (?, ?, ?, ?, 1)",
                    (tx_title.strip(), tx_subject, tx_duration, shamsi_today)
                )
                qid = cursor.lastrowid
                cnt = 0
                for line in lines:
                    if not line.strip(): continue
                    parts = [p.strip() for p in line.split("|")]
                    q_txt = parts[0]
                    o1, o2, o3, o4 = "", "", "", ""
                    corr = 1
                    for p in parts[1:]:
                        p_clean = p.strip()
                        if 'گزینه ۱' in p_clean or 'گزینه 1' in p_clean or p_clean.startswith('۱:') or p_clean.startswith('1:'):
                            o1 = p_clean.replace('گزینه ۱:', '').replace('گزینه 1:', '').replace('۱:', '').replace('1:', '').strip()
                        elif 'گزینه ۲' in p_clean or 'گزینه 2' in p_clean or p_clean.startswith('۲:') or p_clean.startswith('2:'):
                            o2 = p_clean.replace('گزینه ۲:', '').replace('گزینه 2:', '').replace('۲:', '').replace('2:', '').strip()
                        elif 'گزینه ۳' in p_clean or 'گزینه 3' in p_clean or p_clean.startswith('۳:') or p_clean.startswith('3:'):
                            o3 = p_clean.replace('گزینه ۳:', '').replace('گزینه 3:', '').replace('۳:', '').replace('3:', '').strip()
                        elif 'گزینه ۴' in p_clean or 'گزینه 4' in p_clean or p_clean.startswith('۴:') or p_clean.startswith('4:'):
                            o4 = p_clean.replace('گزینه ۴:', '').replace('گزینه 4:', '').replace('۴:', '').replace('4:', '').strip()
                        elif 'پاسخ صحیح' in p_clean or 'گزینه صحیح' in p_clean or 'جواب' in p_clean or 'کلید' in p_clean:
                            val_str = p_clean.replace('پاسخ صحیح:', '').replace('گزینه صحیح:', '').replace('جواب:', '').replace('کلید:', '').strip()
                            try:
                                corr = int(val_str)
                            except ValueError:
                                corr = 1
                    if not o1 and len(parts) > 1: o1 = parts[1]
                    if not o2 and len(parts) > 2: o2 = parts[2]
                    if not o3 and len(parts) > 3: o3 = parts[3]
                    if not o4 and len(parts) > 4: o4 = parts[4]
                    
                    cursor.execute("""
                        INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                        VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (qid, q_txt, o1, o2, o3, o4, corr, None, None))
                    cnt += 1
                conn.commit()
                conn.close()
                st.success(f"🎉 آزمون '{tx_title}' با {cnt} سوال با موفقیت ساخت شد!")
                st.rerun()

    with q_tab2:
        st.subheader("📥 بارگذاری سریع فایل آزمون آماده (فرمت JSON)")
        sample_quiz_json = {
            "title": "آزمون علوم تجربی پایه پنجم",
            "subject": "علوم تجربی",
            "duration_minutes": 45,
            "questions": [
                {
                    "question_type": "mcq",
                    "question_text": "کدام یک تغییر شیمیایی است؟",
                    "option_1": "ذوب شدن یخ", "option_2": "پختن نان", "option_3": "تبخیر آب", "option_4": "مخلوط آب و نمک",
                    "correct_option": 2,
                    "explanation": "پختن نان تغییر شیمیایی است زیرا جنس ماده عوض می‌شود."
                }
            ]
        }
        json_str = json.dumps(sample_quiz_json, ensure_ascii=False, indent=2)
        st.download_button("📥 دانلود الگوی نمونه فایل آزمون (JSON)", data=json_str.encode('utf-8'), file_name="quiz_template.json", mime="application/json")
        
        uploaded_json = st.file_uploader("بارگذاری فایل JSON آزمون:", type=["json"])
        if uploaded_json is not None:
            try:
                data = json.load(uploaded_json)
                st.write(f"<b>عنوان آزمون:</b> {data.get('title')}", unsafe_allow_html=True)
                
                if st.button("🚀 انتشار این فایل به عنوان آزمون فعال"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    shamsi_today = get_current_shamsi_date()
                    cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, created_at, is_active) VALUES (?, ?, ?, ?, 1)",
                                   (data.get('title', 'آزمون آنلاین'), data.get('subject', 'عمومی'), data.get('duration_minutes', 60), shamsi_today))
                    quiz_id = cursor.lastrowid
                    
                    for q in data.get('questions', []):
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (quiz_id, q.get('question_type', 'mcq'), q.get('question_text', ''), q.get('option_1', ''), q.get('option_2', ''), q.get('option_3', ''), q.get('option_4', ''), q.get('correct_option', 1), q.get('model_answer', ''), q.get('explanation', '')))
                    conn.commit()
                    conn.close()
                    st.success("✅ آزمون با موفقیت بارگذاری شد.")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ خطا در پردازش فایل JSON: {e}")

    with q_tab3:
        st.subheader("📋 مدیریت و حذف آزمون‌های موجود")
        quizzes_df = safe_read_sql("SELECT id as 'شناسه', title as 'عنوان آزمون', subject as 'درس', duration_minutes as 'زمان (دقیقه)', created_at as 'تاریخ ایجاد', is_active as 'وضعیت فعال' FROM quizzes ORDER BY id DESC", fallback_cols=['شناسه', 'عنوان آزمون', 'درس', 'زمان (دقیقه)', 'تاریخ ایجاد', 'وضعیت فعال'])
        
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True)
            st.markdown("---")
            st.markdown("##### 🗑️ حذف کامل یک آزمون:")
            q_del_id = st.selectbox("انتخاب آزمون جهت حذف کامل:", quizzes_df['شناسه'].tolist(), format_func=lambda x: f"شناسه {x} - {quizzes_df[quizzes_df['شناسه']==x]['عنوان آزمون'].values[0]}")
            if st.button("🗑️ حذف کامل این آزمون"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM quizzes WHERE id = ?", (q_del_id,))
                conn.commit()
                conn.close()
                st.success("✅ آزمون و تمامی سوالات مربوط به آن حذف گردید.")
                st.rerun()
        else:
            st.info("آزمونی در دیتابیس ثبت نشده است.")

# ---------------------------------------------------------
# 6. STUDENT ONLINE QUIZ TAKING
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین دانش‌آموزی")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("دانش‌آموزی در سیستم ثبت نشده است.")
        st.stop()
        
    student_list = [f"{row['id']} - {row['first_name']} {row['last_family_name']} ({row['student_group']})" for _, row in students_df.iterrows()]
    selected_st_str = st.selectbox("دانش‌آموز عزیز؛ نام خود را انتخاب کنید:", student_list)
    st_id = int(selected_st_str.split(" - ")[0])
    
    quizzes_df = safe_read_sql("SELECT * FROM quizzes WHERE is_active = 1 ORDER BY id DESC", fallback_cols=['id', 'title', 'subject', 'duration_minutes', 'created_at', 'is_active'])
    if quizzes_df.empty:
        st.info("در حال حاضر هیچ آزمون فعالی وجود ندارد.")
        st.stop()
        
    quiz_options = [f"{row['id']} - {row['title']} ({row['duration_minutes']} دقیقه)" for _, row in quizzes_df.iterrows()]
    selected_quiz_str = st.selectbox("انتخاب آزمون آنلاین:", quiz_options)
    quiz_id = int(selected_quiz_str.split(" - ")[0])
    
    quiz_info = quizzes_df[quizzes_df['id'] == quiz_id].iloc[0]
    duration = int(quiz_info['duration_minutes'])
    
    existing_sub = safe_read_sql("SELECT * FROM quiz_submissions WHERE quiz_id = ? AND student_id = ?", params=(quiz_id, st_id))
    if not existing_sub.empty:
        st.success("✅ شما قبلاً در این آزمون شرکت کرده‌اید و پاسخ‌های شما ثبت شده است.")
        sub_row = existing_sub.iloc[0]
        st.markdown(f"<b>📊 نمره تستی شما: {sub_row['score']} از {sub_row['total_questions']} (درصد: {sub_row['percentage']:.1f}٪)</b>", unsafe_allow_html=True)
        st.stop()
        
    st.markdown("---")
    st.info(f"⏱️ **زمان تعیین‌شده برای این آزمون: {duration} دقیقه می‌باشد.** به سوالات زیر پاسخ دهید:")
    
    questions_df = safe_read_sql("SELECT * FROM questions WHERE quiz_id = ? ORDER BY id ASC", params=(quiz_id,))
    
    user_mcq_answers = {}
    user_essay_answers = {}
    
    with st.form("take_quiz_form"):
        for idx, q in questions_df.iterrows():
            st.markdown(f"##### ❓ سوال {idx+1}: {q['question_text']}")
            if q['question_type'] == "mcq":
                opts = [f"۱) {q['option_1']}", f"۲) {q['option_2']}", f"۳) {q['option_3']}", f"۴) {q['option_4']}"]
                ans = st.radio(f"انتخاب گزینه سوال {idx+1}:", opts, key=f"sq_{q['id']}")
                opt_num = int(ans.split("）")[0]) if "）" in ans else int(ans.split(")")[0])
                user_mcq_answers[q['id']] = opt_num
            else:
                e_ans = st.text_area(f"پاسخ تشریحی شما برای سوال {idx+1}:", key=f"seq_{q['id']}")
                user_essay_answers[q['id']] = e_ans
                
        submit_quiz_btn = st.form_submit_button("🏁 پایان و ثبت نهایی پاسخ‌ها")
        
        if submit_quiz_btn:
            mcq_correct_count = 0
            total_mcq = 0
            
            for idx, q in questions_df.iterrows():
                if q['question_type'] == "mcq":
                    total_mcq += 1
                    if user_mcq_answers.get(q['id']) == q['correct_option']:
                        mcq_correct_count += 1
                        
            pct = (mcq_correct_count / total_mcq * 100.0) if total_mcq > 0 else 100.0
            shamsi_submitted = get_current_shamsi_date()
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO quiz_submissions (quiz_id, student_id, submission_date, score, total_questions, percentage, essay_answers)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (quiz_id, st_id, shamsi_submitted, mcq_correct_count, total_mcq, pct, json.dumps(user_essay_answers, ensure_ascii=False)))
            conn.commit()
            conn.close()
            
            st.balloons()
            st.success(f"🎉 پاسخ‌های شما با موفقیت ثبت گردید. نمره بخش تستی: {mcq_correct_count} از {total_mcq} ({pct:.1f}٪)")
            
            st.markdown("### 💡 پاسخ‌نامه تشریحی و تحلیل آموزشی سوالات")
            for idx, q in questions_df.iterrows():
                st.markdown(f"<b>سوال {idx+1}: {q['question_text']}</b>", unsafe_allow_html=True)
                if q['question_type'] == "mcq":
                    st.write(f"گزینه صحیح: گزینه {q['correct_option']}")
                else:
                    st.write(f"پاسخ نمونه آموزگار: {q['model_answer']}")
                if q['explanation']:
                    st.info(f"تحلیل آموزشی: {q['explanation']}")
                st.markdown("---")

# ---------------------------------------------------------
# 7. COMPREHENSIVE PORTFOLIO & REPORT CARD DASHBOARD
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 پوشه کار و کارنامه جامع تحصیلی دانش‌آموز")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("هیچ دانش‌آموزی در سیستم ثبت نشده است.")
        st.stop()
        
    student_list = [f"{row['id']} - {row['first_name']} {row['last_family_name']} ({row['student_group']})" for _, row in students_df.iterrows()]
    selected_st_str = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار:", student_list)
    st_id = int(selected_st_str.split(" - ")[0])
    
    st_info = students_df[students_df['id'] == st_id].iloc[0]
    
    # Private PIN Guard if not logged in as teacher
    if not st.session_state['is_teacher_logged_in']:
        pin_db = str(st_info['pin_code']).strip() if 'pin_code' in st_info and st_info['pin_code'] else '1234'
        st.info("🔒 جهت حفظ حریم خصوصی، کارنامه تحصیلی محرمانه می‌باشد.")
        input_pin = st.text_input("🔑 رمز ۴ رقمی اختصاصی دانش‌آموز را وارد کنید:", type="password", key="p_pin_guard")
        if input_pin.strip() != pin_db and input_pin.strip() != '1234':
            st.warning("⚠️ لطفاً رمز ۴ رقمی اختصاصی دانش‌آموز را وارد کنید (پیش‌فرض: 1234).")
            st.stop()
        else:
            st.success("🔓 احراز هویت موفقیت‌آمیز!")
            
    st.markdown(f"""
    <div class="welcome-card">
        <h3 style="margin:0; color:#38bdf8 !important;">پرونده تحصیلی: {st_info['first_name']} {st_info['last_family_name']}</h3>
        <p style="margin-top:6px; margin-bottom:0;">
            <b>کد ملی:</b> {st_info['national_code']} | <b>گروه آموزشی:</b> {st_info['student_group']} | <b>شماره همراه اولیا:</b> {st_info['parent_phone']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with get_connection() as conn:
        eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (st_id,)).fetchone()[0]
        beh_count = conn.execute("SELECT COUNT(*) FROM behavior_logs WHERE student_id = ?", (st_id,)).fetchone()[0]
        quiz_avg_row = conn.execute("SELECT AVG(percentage) FROM quiz_submissions WHERE student_id = ?", (st_id,)).fetchone()
        quiz_avg = quiz_avg_row[0] if quiz_avg_row and quiz_avg_row[0] is not None else None
        
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
    with c2:
        st.metric("موارد رفتاری ثبت‌شده:", beh_count)
    with c3:
        st.metric("میانگین درصد آزمون آنلاین:", f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون")
        
    st.markdown("---")
    
    # Official PDF Download Button
    portfolio_pdf_bytes = generate_comprehensive_portfolio_pdf(st_id)
    st.download_button(
        "📥 دانلود فایل پی دی اف کارنامه جامع (PDF معتبر قابل پرینت)",
        data=portfolio_pdf_bytes,
        file_name=f"report_card_{st_info['last_family_name']}_{st_id}.pdf",
        mime="application/pdf"
    )
    
    st.markdown("---")
    
    # Growth Chart
    quiz_chart_df = safe_read_sql("""
        SELECT q.title as 'عنوان آزمون', s.percentage as 'درصد ٪'
        FROM quiz_submissions s
        JOIN quizzes q ON s.quiz_id = q.id
        WHERE s.student_id = ? ORDER BY s.id ASC
    """, params=(st_id,), fallback_cols=['عنوان آزمون', 'درصد ٪'])
    
    if not quiz_chart_df.empty:
        st.subheader("📈 نمودار رشد درصد آزمون‌های آنلاین دانش‌آموز")
        st.line_chart(quiz_chart_df.set_index('عنوان آزمون'))
    
    tab_r1, tab_r2, tab_r3 = st.tabs(["📝 ارزشیابی توصیفی", "🌟 سوابق آزمون‌های آنلاین", "🏆 امتیازات رفتاری"])
    
    with tab_r1:
        st.subheader("سوابق ارزشیابی کیفی-توصیفی ۷ درس")
        eval_df = safe_read_sql("""
            SELECT subject as 'عنوان درس', grade_level as 'سطح عملکرد', eval_date as 'تاریخ', feedback as 'بازخورد آموزگار'
            FROM evaluations WHERE student_id = ? ORDER BY id DESC
        """, params=(st_id,), fallback_cols=['عنوان درس', 'سطح عملکرد', 'تاریخ', 'بازخورد آموزگار'])
        
        if not eval_df.empty:
            st.dataframe(eval_df, use_container_width=True)
            csv_data = eval_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 دانلود خروجی سوابق توصیفی (CSV/Excel)", data=csv_data, file_name=f"evaluations_{st_info['last_family_name']}.csv", mime="text/csv")
        else:
            st.info("هنوز ارزشیابی توصیفی برای این دانش‌آموز ثبت نشده است.")

    with tab_r2:
        st.subheader("سوابق شرکت در آزمون‌های آنلاین")
        sub_df = safe_read_sql("""
            SELECT q.title as 'عنوان آزمون', s.submission_date as 'تاریخ شرکت', s.score as 'نمره تستی', s.total_questions as 'کل سوالات تستی', s.percentage as 'درصد ٪'
            FROM quiz_submissions s
            JOIN quizzes q ON s.quiz_id = q.id
            WHERE s.student_id = ? ORDER BY s.id DESC
        """, params=(st_id,), fallback_cols=['عنوان آزمون', 'تاریخ شرکت', 'نمره تستی', 'کل سوالات تستی', 'درصد ٪'])
        
        if not sub_df.empty:
            st.dataframe(sub_df, use_container_width=True)
        else:
            st.info("دانش‌آموز هنوز در هیچ آزمون آنلاینی شرکت نکرده است.")

    with tab_r3:
        st.subheader("سوابق امتیازات انضباطی و تشویقی")
        beh_df = safe_read_sql("""
            SELECT log_date as 'تاریخ', behavior_type as 'نوع مشاهده', score as 'امتیاز', description as 'توضیحات'
            FROM behavior_logs WHERE student_id = ? ORDER BY id DESC
        """, params=(st_id,), fallback_cols=['تاریخ', 'نوع مشاهده', 'امتیاز', 'توضیحات'])
        
        if not beh_df.empty:
            st.dataframe(beh_df, use_container_width=True)
            total_beh_score = beh_df['امتیاز'].sum()
            st.metric("🏆 مجموع امتیازات انضباطی و تشویقی دانش‌آموز:", f"{total_beh_score} امتیاز")
        else:
            st.info("مشاهده انضباطی ثبت نشده است.")

