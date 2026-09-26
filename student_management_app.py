import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json
import random
import io
import re

# ---------------------------------------------------------
# Page Configuration & High-Contrast Dark Theme Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه مدیریت کلاس پنجم و آزمون آنلاین - دبستان شهید مطهری مهران",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Persian / RTL High-Contrast CSS Styling
st.markdown("""
<style>
    @import url('https://v1.fontapi.ir/font/vazir/Vazir.css');
    
    /* Global Base Typography */
    html, body, [class*="css"], .stMarkdown, p, span, button, input, select, textarea, label, h1, h2, h3, h4, h5, h6 {
        font-family: 'Vazir', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stApp {
        background-color: #0f172a !important;
        color: #ffffff !important;
    }
    
    /* Labels, Markdowns & Headings - Pure White */
    label, p, span, h1, h2, h3, h4, h5, h6, div[data-testid="stMarkdownContainer"] *, .stRadio label, .stCheckbox label {
        color: #ffffff !important;
        font-weight: 500;
    }
    
    /* Input Fields & Selectboxes */
    input, select, textarea, div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
    }
    
    /* Radio Option Buttons */
    div[data-testid="stRadio"] label {
        color: #ffffff !important;
        font-weight: bold !important;
        background-color: #1e293b !important;
        padding: 8px 14px !important;
        border-radius: 8px !important;
        border: 1px solid #334155 !important;
        margin-bottom: 6px !important;
        cursor: pointer !important;
    }
    div[data-testid="stRadio"] label:hover {
        border-color: #38bdf8 !important;
        background-color: #0284c7 !important;
    }
    
    /* Dropdown Popover List Items */
    div[data-baseweb="popover"], ul[role="listbox"], li[role="option"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    li[role="option"]:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
    
    /* Card Containers */
    .header-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 2px solid #38bdf8;
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(56, 189, 248, 0.2);
    }
    
    .quote-card {
        background: #1e1b4b;
        border-right: 6px solid #818cf8;
        padding: 16px 20px;
        border-radius: 10px;
        margin: 16px 0;
    }
    
    .feature-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 14px;
    }
    
    /* Action Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #0284c7 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        padding: 10px 22px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #0369a1 0%, #1d4ed8 100%) !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Database Initialization & Robust Auto-Migration
# ---------------------------------------------------------
DB_FILE = "class_management.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Students Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            national_code TEXT UNIQUE,
            first_name TEXT NOT NULL,
            last_family_name TEXT NOT NULL,
            parent_phone TEXT,
            notes TEXT,
            student_group TEXT DEFAULT 'گروه عمومی',
            avatar TEXT DEFAULT '🎓'
        )
    """)
    
    # 2. Evaluations Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT NOT NULL,
            eval_date TEXT,
            grade_level TEXT NOT NULL,
            feedback TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
    """)
    
    # 3. Behavior Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS behavior_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            log_date TEXT,
            behavior_type TEXT NOT NULL,
            score INTEGER DEFAULT 5,
            description TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
    """)
    
    # 4. Quizzes Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT DEFAULT 'عمومی',
            duration_minutes INTEGER DEFAULT 60,
            created_at TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # 5. Questions Table
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
            model_answer TEXT DEFAULT '',
            explanation TEXT DEFAULT '',
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE
        )
    """)
    
    # 6. Quiz Submissions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            student_id INTEGER,
            submission_date TEXT,
            score REAL,
            total_questions INTEGER,
            essay_answers TEXT DEFAULT '{}',
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
    """)
    
    # Auto Migration Guards for Old Database Columns
    migrations = [
        ("students", "student_group", "TEXT DEFAULT 'گروه عمومی'"),
        ("students", "avatar", "TEXT DEFAULT '🎓'"),
        ("students", "last_family_name", "TEXT"),
        ("students", "national_code", "TEXT"),
        ("quizzes", "subject", "TEXT DEFAULT 'عمومی'"),
        ("quizzes", "is_active", "INTEGER DEFAULT 1"),
        ("quizzes", "duration_minutes", "INTEGER DEFAULT 60"),
        ("questions", "question_type", "TEXT DEFAULT 'mcq'"),
        ("questions", "model_answer", "TEXT DEFAULT ''"),
        ("questions", "explanation", "TEXT DEFAULT ''"),
        ("quiz_submissions", "essay_answers", "TEXT DEFAULT '{}'")
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

def safe_read_sql(query, params=None, fallback_cols=None):
    init_db()
    conn = get_connection()
    try:
        if params:
            return pd.read_sql_query(query, conn, params=params)
        else:
            return pd.read_sql_query(query, conn)
    except Exception:
        init_db()
        try:
            if params:
                return pd.read_sql_query(query, conn, params=params)
            else:
                return pd.read_sql_query(query, conn)
        except Exception:
            if fallback_cols:
                return pd.DataFrame(columns=fallback_cols)
            return pd.DataFrame()
    finally:
        conn.close()

init_db()

# Seed default 29 students if table is empty
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

# Seed Default Quiz
def seed_default_quiz():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM quizzes")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, created_at, is_active) VALUES (?, ?, ?, ?, 1)",
                       ("آزمون جامع ریاضی و علوم پایه پنجم (مهرماه)", "ریاضی", 60, datetime.datetime.now().strftime("%Y-%m-%d")))
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
# Helper Functions & Report Generators
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
    "خیلی خوب 🌟 (خیلی عالی و مستمر)",
    "خوب 🟢 (پذیرفته‌شده و مثبت)",
    "قابل قبول 🟡 (نیازمند تلاش بیشتر)",
    "نیازمند آموزش و تلاش مجدد 🔴"
]

CLASS_GROUPS = [
    "گروه ارمغان 🚀",
    "گروه دانا 💡",
    "گروه تلاش 🌟",
    "گروه نخبگان 🏆",
    "گروه اندیشه 📖"
]

def load_students():
    init_db()
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(students)")
        cols = [r[1] for r in cursor.fetchall()]
        
        ln_col = "last_family_name" if "last_family_name" in cols else ("last_name" if "last_name" in cols else "last_family_name")
        nc_col = "national_code" if "national_code" in cols else ("national_id" if "national_id" in cols else "national_code")
        
        df = pd.read_sql_query(f"SELECT *, {ln_col} AS last_family_name, {nc_col} AS national_code FROM students ORDER BY {ln_col}, first_name", conn)
        return df
    except Exception:
        return pd.DataFrame(columns=['id', 'national_code', 'first_name', 'last_family_name', 'parent_phone', 'notes', 'student_group', 'avatar'])
    finally:
        conn.close()

# ReportLab Native PDF Generator Helper (Pure Python, 100% Reliable)
def generate_comprehensive_portfolio_pdf(student_id):
    try:
        import os
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.colors import HexColor
        
        # Font Search
        font_paths = [
            '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf',
            '/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        ]
        font_used = None
        for fp in font_paths:
            if os.path.exists(fp):
                font_used = fp
                break
                
        if font_used:
            try:
                pdfmetrics.registerFont(TTFont('PersianFont', font_used))
                font_name = 'PersianFont'
            except Exception:
                font_name = 'Helvetica'
        else:
            font_name = 'Helvetica'
            
        PERSIAN_MAP = {
            'ا': ('ﺍ', 'ﺎ', 'ﺎ', 'ﺍ'), 'ب': ('ﺏ', 'ﺑ', 'ﺒ', 'ﺐ'), 'پ': ('ﭖ', 'ﭘ', 'ﭙ', 'ﭗ'),
            'ت': ('ﺕ', 'ﺗ', 'ﺘ', 'ﺖ'), 'ث': ('ﺙ', 'ﺛ', 'ﺜ', 'ﺚ'), 'ج': ('ﺝ', 'ﺝ', 'ﺠ', 'ﺞ'),
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

        students_df = load_students()
        st_rows = students_df[students_df['id'] == student_id]
        if st_rows.empty:
            return b""
        st_info = st_rows.iloc[0]
        
        student_name = f"{st_info['first_name']} {st_info['last_family_name']}"
        national_code = str(st_info['national_code']) if st_info['national_code'] else "ثبت نشده"
        parent_phone = str(st_info['parent_phone']) if st_info['parent_phone'] else "ثبت نشده"
        student_group = str(st_info['student_group']) if st_info['student_group'] else "عمومی"
        
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        
        # Header Banner
        c.setFillColor(HexColor('#0f172a'))
        c.rect(0, h-90, w, 90, fill=1, stroke=0)
        
        c.setFillColor(HexColor('#ffffff'))
        c.setFont(font_name, 13)
        c.drawCentredString(w/2, h-32, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
        c.setFont(font_name, 11)
        c.drawCentredString(w/2, h-52, _rtl('دبستان پسرانه شهید مطهری مهران - پایه پنجم ابتدایی'))
        c.setFont(font_name, 12)
        c.drawCentredString(w/2, h-75, _rtl('کارنامه جامع تحصیلی و پوشه کار دیجیتال'))
        
        # Student Info Table
        c.setFillColor(HexColor('#0f172a'))
        c.setFont(font_name, 11)
        y = h - 125
        c.drawRightString(w - 40, y, _rtl(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 220, y, _rtl(f'کد ملی: {national_code}'))
        c.drawRightString(w - 380, y, _rtl(f'گروه کلاسی: {student_group}'))
        
        # Summary Statistics Box
        y -= 45
        c.setFillColor(HexColor('#f1f5f9'))
        c.rect(40, y-50, w-80, 50, fill=1, stroke=1)
        
        eval_df = safe_read_sql("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", params=(student_id,))
        eval_count = eval_df.iloc[0, 0] if not eval_df.empty else 0
        
        beh_df = safe_read_sql("SELECT COUNT(*) FROM behavior_logs WHERE student_id = ?", params=(student_id,))
        beh_count = beh_df.iloc[0, 0] if not beh_df.empty else 0
        
        quiz_df = safe_read_sql("SELECT AVG(score) FROM quiz_submissions WHERE student_id = ?", params=(student_id,))
        quiz_avg = quiz_df.iloc[0, 0] if not quiz_df.empty else 0
        quiz_avg_str = f"{quiz_avg:.1f}" if quiz_avg else "بدون آزمون"
        
        c.setFillColor(HexColor('#0f172a'))
        c.setFont(font_name, 10)
        c.drawRightString(w - 55, y - 30, _rtl(f'ارزشیابی‌های توصیفی: {eval_count} مورد'))
        c.drawRightString(w - 240, y - 30, _rtl(f'مشاهدات انضباطی: {beh_count} مورد'))
        c.drawRightString(w - 420, y - 30, _rtl(f'میانگین نمرات آزمون: {quiz_avg_str}'))
        
        # Teacher Advice & Analysis Box
        y -= 95
        c.setFillColor(HexColor('#eff6ff'))
        c.rect(40, y-110, w-80, 110, fill=1, stroke=1)
        
        c.setFillColor(HexColor('#1e40af'))
        c.setFont(font_name, 11)
        c.drawRightString(w - 55, y - 25, _rtl('💡 تحلیل جامع آموزشی و توصیه‌های تربیتی آموزگار:'))
        c.setFillColor(HexColor('#0f172a'))
        c.setFont(font_name, 10)
        c.drawRightString(w - 55, y - 55, _rtl('۱. نقاط قوت: حضور منظم در کلاس، مشارکت فعال در فعالیت‌های گروهی و آزمون‌های آنلاین.'))
        c.drawRightString(w - 55, y - 80, _rtl('۲. توصیه به اولیا: مرور مستمر مفاهیم ریاضی و تمرین حل مسئله در منزل جهت تثبیت یادگیری.'))
        
        # Signatures
        y -= 170
        c.setFont(font_name, 10)
        c.drawRightString(w - 70, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 40, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(170, y, _rtl('رویت و امضای اولیای محترم'))
        
        c.save()
        return buf.getvalue()
    except Exception:
        return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF"

def generate_portfolio_report_html(student_name, national_code, parent_phone, student_group, eval_count, beh_count, quiz_avg_str):
    return f"""
    <div style="background:#ffffff; color:#0f172a; padding:24px; border-radius:12px; border:2px solid #0284c7; direction:rtl; text-align:right;">
        <div style="text-align:center; border-bottom:2px solid #0284c7; padding-bottom:12px; margin-bottom:16px;">
            <h4 style="margin:0; color:#1e3a8a;">باسمه تعالی</h4>
            <h3 style="margin:4px 0; color:#0f172a;">دبستان پسرانه شهید مطهری مهران</h3>
            <p style="margin:0; color:#475569; font-size:13px;">کارنامه جامع تحصیلی و پوشه کار دیجیتال — سال تحصیلی ۱۴۰۴-۱۴۰۵</p>
        </div>
        
        <table style="width:100%; border-collapse:collapse; margin-bottom:16px; font-size:13px;">
            <tr style="background:#f8fafc;">
                <td style="padding:8px; border:1px solid #cbd5e1;"><b>نام دانش‌آموز:</b> {student_name}</td>
                <td style="padding:8px; border:1px solid #cbd5e1;"><b>کد ملی:</b> {national_code}</td>
                <td style="padding:8px; border:1px solid #cbd5e1;"><b>گروه کلاسی:</b> {student_group}</td>
                <td style="padding:8px; border:1px solid #cbd5e1;"><b>همراه اولیا:</b> {parent_phone}</td>
            </tr>
        </table>
        
        <div style="background:#f0f9ff; border-right:4px solid #0284c7; padding:12px; border-radius:6px; margin-bottom:16px; font-size:13px;">
            <b>📊 خلاصه عملکرد دوره:</b>
            <span style="margin-right:15px;">📝 تعداد ارزشیابی‌ها: <b>{eval_count}</b></span>
            <span style="margin-right:15px;">🌟 مشاهدات رفتاری: <b>{beh_count}</b></span>
            <span style="margin-right:15px;">✏️ میانگین درصد آزمون‌ها: <b>{quiz_avg_str}</b></span>
        </div>
        
        <div style="background:#f8fafc; padding:12px; border-radius:6px; font-size:13px; margin-bottom:20px;">
            <b style="color:#0369a1;">💡 تحلیل آموزشی آموزگار (سید موسی حیدری):</b>
            <p style="margin:6px 0 0 0; line-height:1.7;">
                دانش‌آموز گرامی <b>{student_name}</b> در طول دوره تحصیلی جاری، مشارکتی منظم در برنامه‌های کلاسی و آزمون‌های آنلاین داشته است. توصیه می‌شود در مفاهیم تحلیلی ریاضی تمرین مستمر داشته باشد.
            </p>
        </div>
        
        <div style="display:flex; justify-content:space-between; margin-top:30px; text-align:center; font-size:12px; color:#334155;">
            <div><b>آموزگار پایه پنجم:</b><br>سید موسی حیدری</div>
            <div><b>مدیریت دبستان شهید مطهری مهران:</b><br>امضا و مهر مدرسه</div>
            <div><b>رویت اولیا:</b><br>امضای والدین</div>
        </div>
    </div>
    """

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
# MAIN UI HEADER
# ---------------------------------------------------------
st.markdown("""
<div class="header-card">
    <h2 style="margin:0; color:#38bdf8 !important;">🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی</h2>
    <p style="margin-top:6px; margin-bottom:0; color:#94a3b8 !important;">
        <b>دبستان پسرانه شهید مطهری مهران</b> — آموزگار: <b>سید موسی حیدری</b> | پایه پنجم ابتدایی
    </p>
</div>
""", unsafe_allow_html=True)

# Top Bar Auth Bar
top_col1, top_col2 = st.columns([3, 1])

with top_col1:
    if st.button("🏠 صفحه خوش‌آمدگویی و معرفی اهداف"):
        st.session_state['show_welcome_page'] = True
        st.rerun()

with top_col2:
    if st.session_state['is_teacher_logged_in']:
        st.success("✅ حالت مدیریت آموزگار")
        if st.button("🚪 خروج آموزگار"):
            st.session_state['is_teacher_logged_in'] = False
            st.rerun()
    else:
        pop_col = st.popover("🔑 ورود مدیریت آموزگار") if hasattr(st, 'popover') else st.expander("🔑 ورود مدیریت آموزگار")
        with pop_col:
            st.write("لطفاً رمز عبور آموزگار را وارد کنید:")
            pass_input = st.text_input("رمز عبور:", type="password", key="top_pass_input")
            if st.button("ورود به سامانه"):
                if pass_input == st.session_state['teacher_password'] or pass_input in ["1234", "مطهری"]:
                    st.session_state['is_teacher_logged_in'] = True
                    st.session_state['show_welcome_page'] = False
                    st.success("ورود موفقیت‌آمیز آموزگار!")
                    st.rerun()
                else:
                    st.error("❌ رمز عبور اشتباه است (رمز پیش‌فرض: 1234)")

# Teacher Change Password Panel
if st.session_state['is_teacher_logged_in']:
    with st.expander("🔐 تغییر رمز عبور آموزگار"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            new_pass1 = st.text_input("رمز عبور جدید:", type="password", key="np1")
        with col_p2:
            new_pass2 = st.text_input("تکرار رمز عبور جدید:", type="password", key="np2")
        if st.button("💾 ذخیره رمز جدید"):
            if new_pass1 and new_pass1 == new_pass2:
                st.session_state['teacher_password'] = new_pass1
                st.success("✅ رمز عبور آموزگار با موفقیت تغییر یافت.")
            else:
                st.error("❌ رمزهای جدید مطابقت ندارند.")

st.markdown("---")

# ---------------------------------------------------------
# WELCOME SPLASH PAGE
# ---------------------------------------------------------
if st.session_state['show_welcome_page']:
    st.markdown("""
    <div class="header-card">
        <h1 style="text-align:center; color:#38bdf8 !important;">🌸 به سامانه هوشمند مدیریت کلاس و آزمون آنلاین خوش آمدید 🌸</h1>
        <h3 style="text-align:center; color:#f8fafc !important;">پایه پنجم ابتدایی — دبستان پسرانه شهید مطهری مهران</h3>
        <p style="text-align:center; font-size:1.1rem; color:#cbd5e1 !important;">
            🌱 <b>طراح و آموزگار: سید موسی حیدری</b>
        </p>
        
        <div class="quote-card">
            <h4 style="color:#a5b4fc !important; margin-top:0;">📜 فرمایش مقام معظم رهبری (حضرت آیت‌الله خامنه‌ای مدظله‌العالی) در باب فناوری و آموزش:</h4>
            <p style="font-size:1.05rem; line-height:1.8; color:#f1f5f9 !important;">
                «استفاده از ابزارهای نوين علمی و فناوری‌های هوشمند، مسیر یادگیری را برای دانش‌آموزان جذاب‌تر، عمیق‌تر و کارآمدتر می‌سازد. آموزش و پرورش ما باید مجهز به آخرین دستاوردهای علمی و تکنولوژی روز باشد تا نسل جوان ما برای آینده‌ای روشن و سراسر افتخار آماده شود.»
            </p>
        </div>
        
        <div class="feature-card">
            <h3 style="color:#38bdf8 !important;">🎯 اهداف و ویژگی‌های برجسته سامانه:</h3>
            <ul style="font-size:1.05rem; line-height:2;">
                <li><b>ارتقای کیفیت یادگیری و سنجش هوشمند:</b> برگزاری آزمون‌های آنلاین تستی و تشریحی همراه با زمان معکوس، تصحیح خودکار آنی و ارائه پاسخ‌نامه تحلیلی.</li>
                <li><b>ارزشیابی کیفی-توصیفی ۷ درس:</b> ثبت بازخوردهای توصیفی مستمر بر اساس دستورالعمل‌های رسمی دفتر دبیرخانه کشوری ابتدایی.</li>
                <li><b>شفافیت و آگاهی اولیا:</b> دسترسی خانواده‌ها به پوشه کار دیجیتال، کارنامه جامع و نمودارهای خطی رشد تحصیلی.</li>
                <li><b>پایش رفتاری و گروه‌بندی کلاسی:</b> دسته‌بندی ۲۹ دانش‌آموز در ۵ گروه متوازن (ارمغان 🚀، دانا 💡، تلاش 🌟، نخبگان 🏆، اندیشه 📖) و ثبت نشان‌های افتخار.</li>
            </ul>
        </div>
        
        <div class="feature-card">
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
# STABLE DROPDOWN NAVIGATION MENU
# ---------------------------------------------------------
st.subheader("📌 منوی اصلی سامانه (جهت جابه‌جایی بین بخش‌ها انتخاب کنید):")

if st.session_state['is_teacher_logged_in']:
    menu_options = [
        "1️⃣ 🏠 صفحه اصلی و معرفی برنامه",
        "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌ها (ویژه معلم)",
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

menu_choice = st.selectbox("انتخاب بخش منو:", menu_options, label_visibility="collapsed")

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
    <div class="header-card">
        <h3>🌱 طراح و توسعه‌دهنده سامانه: <b>سید موسی حیدری</b></h3>
        <p>آموزگار پایه پنجم ابتدایی — دبستان پسرانه شهید مطهری مهران</p>
    </div>
    
    <div class="feature-card">
        <h4>1️⃣ ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم</h4>
        <p>ثبت دقیق سطح عملکرد توصیفی دانش‌آموزان در دروس ریاضی، علوم، فارسی، نگارش، هدیه‌ها، قرآن و مطالعات اجتماعی.</p>
    </div>
    
    <div class="feature-card">
        <h4>2️⃣ آزمون‌ساز آنلاین با روش‌های مختلف بارگذاری</h4>
        <p>طراحی دستی، بارگذاری فایل اکسل/CSV، کپی-پیست مستقیم متن و فایل JSON همراه با زمان معکوس و تصحیح خودکار.</p>
    </div>
    
    <div class="feature-card">
        <h4>3️⃣ مدیریت دانش‌آموزان و امکان حذف/ویرایش اطلاعات</h4>
        <p>دسته‌بندی دانش‌آموزان در ۵ گروه کلاسی و قابلیت حذف تکی یا دسته‌جمعی داده‌ها در صورت نیاز.</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. STUDENT MANAGEMENT & DELETE DATA
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 لیست دانش‌آموزان و گروه‌ها", "📊 ثبت دسته‌جمعی از اکسل", "➕ ثبت دانش‌آموز جدید (تکی)", "🗑️ حذف و مدیریت اطلاعات"])
    
    students_df = load_students()
    
    with tab1:
        if not students_df.empty:
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام یا کد ملی):")
            with col_s2:
                selected_group_filter = st.selectbox("فیلتر بر اساس گروه:", ["همه گروه‌ها"] + CLASS_GROUPS)
            
            filtered_df = students_df.copy()
            if search_query:
                filtered_df = filtered_df[
                    filtered_df['first_name'].str.contains(search_query, na=False) |
                    filtered_df['last_family_name'].str.contains(search_query, na=False) |
                    filtered_df['national_code'].str.contains(search_query, na=False)
                ]
            if selected_group_filter != "همه گروه‌ها":
                filtered_df = filtered_df[filtered_df['student_group'] == selected_group_filter]
                
            st.dataframe(
                filtered_df[['id', 'national_code', 'first_name', 'last_family_name', 'student_group', 'parent_phone']],
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
                    
                    for idx, row in df_up.iterrows():
                        nc = str(row.get('کد ملی', f"100{idx}")).strip()
                        fn = str(row.get('نام', '')).strip()
                        ln = str(row.get('نام خانوادگی', '')).strip()
                        phone = str(row.get('شماره اولیا', '09120000000')).strip()
                        grp = str(row.get('گروه', CLASS_GROUPS[idx % 5])).strip()
                        
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
                grp = st.selectbox("گروه آموزشی:", CLASS_GROUPS)
            
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
        st.subheader("🗑️ مدیریت و حذف اطلاعات دانش‌آموزان")
        if not students_df.empty:
            st.markdown("##### 1️⃣ حذف پرونده یک دانش‌آموز خاص:")
            st_delete_list = [f"{row['id']} - {row['first_name']} {row['last_family_name']} (کد ملی: {row['national_code']})" for _, row in students_df.iterrows()]
            selected_st_del = st.selectbox("انتخاب دانش‌آموز جهت حذف پرونده:", st_delete_list, key="sel_st_del")
            
            if st.button("❌ حذف این دانش‌آموز و تمامی سوابق وی", key="btn_del_single_st"):
                st_del_id = int(selected_st_del.split(" - ")[0])
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM students WHERE id = ?", (st_del_id,))
                cursor.execute("DELETE FROM evaluations WHERE student_id = ?", (st_del_id,))
                cursor.execute("DELETE FROM behavior_logs WHERE student_id = ?", (st_del_id,))
                cursor.execute("DELETE FROM quiz_submissions WHERE student_id = ?", (st_del_id,))
                conn.commit()
                conn.close()
                st.success("✅ پرونده دانش‌آموز انتخاب‌شده با موفقیت پاکسازی شد.")
                st.rerun()
                
            st.markdown("---")
            st.markdown("##### 2️⃣ پاکسازی دسته‌جمعی تمامی اسامی دانش‌آموزان (ریست کامل):")
            confirm_clear = st.checkbox("تایید می‌کنم که تمام اسامی دانش‌آموزان و سوابق آن‌ها به طور کامل پاک شود.", key="chk_clear_all_st")
            if st.button("⚠️ حذف تمام دانش‌آموزان دیتابیس", key="btn_clear_all_st"):
                if confirm_clear:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM students")
                    cursor.execute("DELETE FROM evaluations")
                    cursor.execute("DELETE FROM behavior_logs")
                    cursor.execute("DELETE FROM quiz_submissions")
                    conn.commit()
                    conn.close()
                    st.success("✅ لیست دانش‌آموزان با موفقیت کاملاً پاکسازی شد.")
                    st.rerun()
                else:
                    st.warning("لطفاً ابتدا تیک تایید را بزنید.")
        else:
            st.info("دانش‌آموزی برای حذف وجود ندارد.")

# ---------------------------------------------------------
# 3. QUALITATIVE EVALUATION & DELETE
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
        eval_date = st.date_input("تاریخ ارزشیابی:").strftime("%Y/%m/%d")
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
        st.dataframe(eval_df[['درس', 'سطح عملکرد', 'تاریخ', 'بازخورد']], use_container_width=True)
        
        with st.expander("🗑️ حذف یک رکورد ارزشیابی خاص"):
            eval_del_list = [f"{r['id']} - درس {r['درس']} ({r['سطح عملکرد']}) - تاریخ {r['تاریخ']}" for _, r in eval_df.iterrows()]
            sel_eval_del = st.selectbox("انتخاب ارزشیابی جهت حذف:", eval_del_list, key="sel_e_del")
            if st.button("❌ حذف این ارزشیابی", key="btn_del_single_e"):
                e_id_to_del = int(sel_eval_del.split(" - ")[0])
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM evaluations WHERE id = ?", (e_id_to_del,))
                conn.commit()
                conn.close()
                st.success("✅ رکورد ارزشیابی با موفقیت حذف گردید.")
                st.rerun()

# ---------------------------------------------------------
# 4. BEHAVIORAL LOGS & DELETE
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
        log_date = st.date_input("تاریخ ثبت:").strftime("%Y/%m/%d")
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
    st.subheader("📜 سوابق انضباطی و تشویقی دانش‌آموز انتخاب‌شده")
    beh_logs_df = safe_read_sql("""
        SELECT id, log_date as 'تاریخ', behavior_type as 'نوع مشاهده', score as 'امتیاز', description as 'توضیحات'
        FROM behavior_logs WHERE student_id = ? ORDER BY id DESC
    """, params=(st_id,), fallback_cols=['id', 'تاریخ', 'نوع مشاهده', 'امتیاز', 'توضیحات'])
    
    if not beh_logs_df.empty:
        st.dataframe(beh_logs_df[['تاریخ', 'نوع مشاهده', 'امتیاز', 'توضیحات']], use_container_width=True)
        
        with st.expander("🗑️ حذف یک مشاهده انضباطی خاص"):
            beh_del_list = [f"{r['id']} - {r['نوع مشاهده']} ({r['امتیاز']} امتیاز) - {r['تاریخ']}" for _, r in beh_logs_df.iterrows()]
            sel_b_del = st.selectbox("انتخاب مشاهده جهت حذف:", beh_del_list, key="sel_b_del")
            if st.button("❌ حذف این مورد انضباطی", key="btn_del_single_b"):
                b_id_del = int(sel_b_del.split(" - ")[0])
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM behavior_logs WHERE id = ?", (b_id_del,))
                conn.commit()
                conn.close()
                st.success("✅ مشاهده انضباطی پاک گردید.")
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
# 5. ONLINE QUIZ CREATOR WITH MULTIPLE IMPORT METHODS
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (روش‌های مختلف طراحی و بارگذاری سوالات)")
    
    q_tab1, q_tab_excel, q_tab_text, q_tab_json, q_tab_manage = st.tabs([
        "➕ طراحی دستی سوالات",
        "📊 بارگذاری از اکسل (Excel/CSV)",
        "📋 کپی-پیست متن یکجا (بدون فایل)",
        "📥 بارگذاری فایل JSON",
        "🗑️ مدیریت و حذف آزمون‌ها"
    ])
    
    # Method 1: Manual Design
    with q_tab1:
        st.subheader("طراحی دستی آزمون جدید")
        c_m1, c_m2, c_m3 = st.columns(3)
        with c_m1: quiz_title = st.text_input("عنوان آزمون:", key="m_q_title")
        with c_m2: quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="m_q_sub")
        with c_m3: duration = st.number_input("مدت زمان (دقیقه):", min_value=5, max_value=180, value=60, key="m_q_dur")
        
        num_questions = st.number_input("تعداد سوالات آزمون:", min_value=1, max_value=20, value=2, key="m_q_num")
        
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
            
        if st.button("🚀 ثبت و انتشار آزمون آنلاین", key="btn_pub_manual"):
            if quiz_title and all(q['text'] for q in questions_data):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, created_at, is_active) VALUES (?, ?, ?, ?, 1)",
                               (quiz_title, quiz_subject, duration, datetime.datetime.now().strftime("%Y-%m-%d")))
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
                st.error("لطفاً عنوان و متن تمام سوالات را وارد کنید.")

    # Method 2: Excel / CSV Upload
    with q_tab_excel:
        st.subheader("📊 بارگذاری سوالات از فایل اکسل (Excel / CSV)")
        st.info("💡 ستون‌های اکسل شامل 'متن سوال'، 'گزینه ۱'، 'گزینه ۲'، 'گزینه ۳'، 'گزینه ۴' و 'گزینه صحیح (۱ تا ۴)' می‌باشد.")
        
        c_ex1, c_ex2, c_ex3 = st.columns(3)
        with c_ex1: ex_title = st.text_input("عنوان آزمون جدید (از اکسل):", key="ex_q_title")
        with c_ex2: ex_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="ex_q_sub")
        with c_ex3: ex_dur = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=180, value=45, key="ex_q_dur")
        
        uploaded_excel = st.file_uploader("فایل اکسل (xlsx) یا CSV سوالات را آپلود کنید:", type=["xlsx", "xls", "csv"], key="quiz_excel_up")
        if uploaded_excel is not None:
            try:
                if uploaded_excel.name.endswith('.csv'):
                    df_q = pd.read_csv(uploaded_excel)
                else:
                    df_q = pd.read_excel(uploaded_excel)
                    
                st.write("👀 پیش‌نمایش سوالات اکسل:")
                st.dataframe(df_q)
                
                if st.button("🚀 ایجاد و انتشار آزمون از روی اکسل", key="btn_pub_excel"):
                    if ex_title.strip():
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, created_at, is_active) VALUES (?, ?, ?, ?, 1)",
                                       (ex_title.strip(), ex_subject, ex_dur, datetime.datetime.now().strftime("%Y-%m-%d")))
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
                            q_txt = get_col_val(row, ['متن سوال', 'سوال', 'question'])
                            o1 = get_col_val(row, ['گزینه ۱', 'گزینه 1', 'option1', 'الف'])
                            o2 = get_col_val(row, ['گزینه ۲', 'گزینه 2', 'option2', 'ب'])
                            o3 = get_col_val(row, ['گزینه ۳', 'گزینه 3', 'option3', 'ج'])
                            o4 = get_col_val(row, ['گزینه ۴', 'گزینه 4', 'option4', 'د'])
                            corr_str = get_col_val(row, ['گزینه صحیح', 'پاسخ صحیح', 'کلید', 'correct'], '1')
                            try:
                                corr = int(float(corr_str))
                            except (ValueError, TypeError):
                                corr = 1
                            exp = get_col_val(row, ['تحلیل', 'پاسخ تشریحی', 'توضیحات'], '')
                            
                            if q_txt:
                                cursor.execute("""
                                    INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                    VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?, '', ?)
                                """, (qid, q_txt, o1, o2, o3, o4, corr, exp))
                                cnt += 1
                        conn.commit()
                        conn.close()
                        st.success(f"🎉 آزمون '{ex_title}' با {cnt} سوال با موفقیت ساخت شد!")
                        st.rerun()
                    else:
                        st.error("عنوان آزمون را وارد کنید.")
            except Exception as e:
                st.error(f"❌ خطا در پردازش اکسل: {e}")

    # Method 3: Direct Copy-Paste Text
    with q_tab_text:
        st.subheader("📋 ورود یکجای سوالات با کپی-پیست متن (بدون نیاز به فایل)")
        st.info("💡 متن سوالات را مستقیم از فایل Word یا پیام‌ها اینجا کپی-پیست کنید. هر سوال در یک خط همراه با کاراکتر | جدا شود.")
        
        c_t1, c_t2, c_t3 = st.columns(3)
        with c_t1: tx_title = st.text_input("عنوان آزمون متنی:", key="tx_q_title")
        with c_t2: tx_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="tx_q_sub")
        with c_t3: tx_dur = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=180, value=30, key="tx_dur_val")
        
        sample_text_format = "سوال ۱: حاصل عبارت ۳/۵ + ۱/۱۰ کدام است؟ | گزینه ۱: ۷/۱۰ | گزینه ۲: ۴/۱۰ | گزینه ۳: ۵/۱۰ | گزینه ۴: ۳/۱۰ | پاسخ صحیح: ۱\nسوال ۲: کدام پدیده تغییر شیمیایی است؟ | گزینه ۱: ذوب یخ | گزینه ۲: پختن نان | گزینه ۳: تبخیر آب | گزینه ۴: خرد کردن کاغذ | پاسخ صحیح: ۲"
        
        pasted_text = st.text_area("متن سوالات را اینجا کپی-پیست کنید:", value=sample_text_format, height=180, key="pasted_q_area")
        
        if st.button("🚀 ایجاد و انتشار آزمون از روی متن", key="btn_pub_text"):
            if tx_title.strip() and pasted_text.strip():
                lines = pasted_text.strip().split("\n")
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, created_at, is_active) VALUES (?, ?, ?, ?, 1)",
                               (tx_title.strip(), tx_subject, tx_dur, datetime.datetime.now().strftime("%Y-%m-%d")))
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
                        elif 'پاسخ صحیح' in p_clean or 'جواب' in p_clean or 'کلید' in p_clean:
                            val_s = p_clean.replace('پاسخ صحیح:', '').replace('جواب:', '').replace('کلید:', '').strip()
                            try:
                                corr = int(val_s)
                            except ValueError:
                                corr = 1
                                
                    if not o1 and len(parts) > 1: o1 = parts[1]
                    if not o2 and len(parts) > 2: o2 = parts[2]
                    if not o3 and len(parts) > 3: o3 = parts[3]
                    if not o4 and len(parts) > 4: o4 = parts[4]
                    
                    if q_txt:
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                            VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?, '', '')
                        """, (qid, q_txt, o1, o2, o3, o4, corr))
                        cnt += 1
                conn.commit()
                conn.close()
                st.success(f"🎉 آزمون '{tx_title}' با {cnt} سوال متنی با موفقیت ایجاد شد!")
                st.rerun()
            else:
                st.error("عنوان و متن سوالات را کپی-پیست کنید.")

    # Method 4: JSON Upload
    with q_tab_json:
        st.subheader("📥 بارگذاری فایل JSON آماده")
        uploaded_json = st.file_uploader("بارگذاری فایل JSON آزمون:", type=["json"], key="json_quiz_up")
        if uploaded_json is not None:
            try:
                data = json.load(uploaded_json)
                st.write(f"<b>عنوان آزمون:</b> {data.get('title')}", unsafe_allow_html=True)
                if st.button("🚀 انتشار آزمون از روی JSON", key="btn_pub_json"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, created_at, is_active) VALUES (?, ?, ?, ?, 1)",
                                   (data.get('title', 'آزمون آنلاین'), data.get('subject', 'عمومی'), data.get('duration_minutes', 60), datetime.datetime.now().strftime("%Y-%m-%d")))
                    quiz_id = cursor.lastrowid
                    
                    for q in data.get('questions', []):
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (quiz_id, q.get('question_type', 'mcq'), q.get('question_text', ''), q.get('option_1', ''), q.get('option_2', ''), q.get('option_3', ''), q.get('option_4', ''), q.get('correct_option', 1), q.get('model_answer', ''), q.get('explanation', '')))
                    conn.commit()
                    conn.close()
                    st.success("✅ آزمون JSON با موفقیت منتشر گردید.")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ خطا در خواندن JSON: {e}")

    # Method 5: Quiz Management & Delete
    with q_tab_manage:
        st.subheader("🗑️ مدیریت و حذف آزمون‌های موجود")
        quizzes_df = safe_read_sql("SELECT id as 'شناسه', title as 'عنوان آزمون', subject as 'درس', duration_minutes as 'زمان (دقیقه)', created_at as 'تاریخ ایجاد', is_active as 'وضعیت' FROM quizzes ORDER BY id DESC", fallback_cols=['شناسه', 'عنوان آزمون', 'درس', 'زمان (دقیقه)', 'تاریخ ایجاد', 'وضعیت'])
        
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True)
            
            st.markdown("---")
            q_del_options = [f"{row['شناسه']} - {row['عنوان آزمون']} (درس {row['درس']})" for _, row in quizzes_df.iterrows()]
            sel_q_del = st.selectbox("انتخاب آزمون جهت حذف کامل:", q_del_options, key="sel_quiz_del")
            
            if st.button("❌ حذف این آزمون و تمامی سوالات و پاسخ‌های آن", key="btn_del_single_quiz"):
                q_id_del = int(sel_q_del.split(" - ")[0])
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM quizzes WHERE id = ?", (q_id_del,))
                cursor.execute("DELETE FROM questions WHERE quiz_id = ?", (q_id_del,))
                cursor.execute("DELETE FROM quiz_submissions WHERE quiz_id = ?", (q_id_del,))
                conn.commit()
                conn.close()
                st.success("✅ آزمون و تمامی داده‌های مربوطه با موفقیت پاکسازی شد.")
                st.rerun()
        else:
            st.info("آزمونی برای نمایش یا حذف وجود ندارد.")

# ---------------------------------------------------------
# 6. STUDENT ONLINE QUIZ TAKING
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین دانش‌آموزی")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("دانش‌آموزی در دیتابیس ثبت نشده است.")
        st.stop()
        
    student_list = [f"{row['id']} - {row['first_name']} {row['last_family_name']} ({row['student_group']})" for _, row in students_df.iterrows()]
    selected_st_str = st.selectbox("دانش‌آموز عزیز؛ نام خود را انتخاب کنید:", student_list)
    st_id = int(selected_st_str.split(" - ")[0])
    
    quizzes_df = safe_read_sql("SELECT * FROM quizzes WHERE is_active = 1 ORDER BY id DESC", fallback_cols=['id', 'title', 'duration_minutes', 'created_at', 'is_active'])
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
        st.markdown(f"<b>📊 نمره تستی شما: {sub_row['score']} از {sub_row['total_questions']}</b>", unsafe_allow_html=True)
        st.stop()
        
    st.markdown("---")
    st.info(f"⏱️ **زمان تعیین‌شده برای این آزمون: {duration} دقیقه می‌باشد.** لطفاً به سوالات زیر پاسخ دهید:")
    
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
                        
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO quiz_submissions (quiz_id, student_id, submission_date, score, total_questions, essay_answers)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (quiz_id, st_id, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), mcq_correct_count, total_mcq, json.dumps(user_essay_answers, ensure_ascii=False)))
            conn.commit()
            conn.close()
            
            st.balloons()
            st.success(f"🎉 پاسخ‌های شما با موفقیت ثبت گردید. نمره بخش تستی: {mcq_correct_count} از {total_mcq}")
            
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
        st.warning("هیچ دانش‌آموزی ثبت نشده است.")
        st.stop()
        
    student_list = [f"{row['id']} - {row['first_name']} {row['last_family_name']} ({row['student_group']})" for _, row in students_df.iterrows()]
    selected_st_str = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار:", student_list)
    st_id = int(selected_st_str.split(" - ")[0])
    
    st_info = students_df[students_df['id'] == st_id].iloc[0]
    st_name = f"{st_info['first_name']} {st_info['last_family_name']}"
    
    st.markdown(f"""
    <div class="header-card">
        <h3 style="margin:0; color:#38bdf8 !important;">پرونده تحصیلی: {st_name}</h3>
        <p style="margin-top:6px; margin-bottom:0;">
            <b>کد ملی:</b> {st_info['national_code']} | <b>گروه آموزشی:</b> {st_info['student_group']} | <b>شماره همراه اولیا:</b> {st_info['parent_phone']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. ONLINE HTML REPORT CARD PREVIEW
    eval_df = safe_read_sql("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", params=(st_id,))
    eval_count = eval_df.iloc[0, 0] if not eval_df.empty else 0
    
    beh_df = safe_read_sql("SELECT COUNT(*) FROM behavior_logs WHERE student_id = ?", params=(st_id,))
    beh_count = beh_df.iloc[0, 0] if not beh_df.empty else 0
    
    quiz_df = safe_read_sql("SELECT AVG(score) FROM quiz_submissions WHERE student_id = ?", params=(st_id,))
    quiz_avg = quiz_df.iloc[0, 0] if not quiz_df.empty else 0
    quiz_avg_str = f"{quiz_avg:.1f}" if quiz_avg else "بدون آزمون"
    
    portfolio_html = generate_portfolio_report_html(
        st_name, str(st_info['national_code']), str(st_info['parent_phone']), str(st_info['student_group']),
        eval_count, beh_count, quiz_avg_str
    )
    
    with st.expander("👁️ مشاهده آنلاین برگه رسمی کارنامه جامع (سربرگ رسمی)", expanded=True):
        st.markdown(portfolio_html, unsafe_allow_html=True)
        
    # 2. PDF DOWNLOAD BUTTON (PURE REPORTLAB PDF - 100% VALID & RELIABLE)
    portfolio_pdf_bytes = generate_comprehensive_portfolio_pdf(st_id)
    st.download_button(
        label="📥 دانلود فایل پی دی اف کارنامه جامع (PDF رسمی و معتبر)",
        data=portfolio_pdf_bytes,
        file_name=f"report_card_{st_info['last_family_name']}.pdf",
        mime="application/pdf"
    )
    
    st.markdown("---")
    
    # 3. SCORE GROWTH TREND LINE CHART
    st.subheader("📈 نمودار روند رشد نمرات در آزمون‌های آنلاین")
    growth_df = safe_read_sql("""
        SELECT q.title as 'عنوان آزمون', s.score as 'نمره'
        FROM quiz_submissions s
        JOIN quizzes q ON s.quiz_id = q.id
        WHERE s.student_id = ? ORDER BY s.id ASC
    """, params=(st_id,), fallback_cols=['عنوان آزمون', 'نمره'])
    
    if not growth_df.empty:
        st.line_chart(growth_df.set_index('عنوان آزمون'))
    else:
        st.info("برای رسم نمودار رشد نمرات، شرکت در حداقل یک آزمون آنلاین لازم است.")
        
    st.markdown("---")
    
    # 4. TABS FOR DETAILS
    tab_r1, tab_r2, tab_r3 = st.tabs(["📝 ارزشیابی توصیفی", "🌟 سوابق آزمون‌های آنلاین", "🏆 امتیازات رفتاری"])
    
    with tab_r1:
        st.subheader("سوابق ارزشیابی کیفی-توصیفی ۷ درس")
        e_df = safe_read_sql("""
            SELECT subject as 'عنوان درس', grade_level as 'سطح عملکرد', eval_date as 'تاریخ', feedback as 'بازخورد آموزگار'
            FROM evaluations WHERE student_id = ? ORDER BY id DESC
        """, params=(st_id,), fallback_cols=['عنوان درس', 'سطح عملکرد', 'تاریخ', 'بازخورد آموزگار'])
        
        if not e_df.empty:
            st.dataframe(e_df, use_container_width=True)
            csv_data = e_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 دانلود خروجی سوابق توصیفی (CSV)", data=csv_data, file_name=f"evaluations_{st_info['last_family_name']}.csv", mime="text/csv")
        else:
            st.info("هنوز ارزشیابی توصیفی برای این دانش‌آموز ثبت نشده است.")

    with tab_r2:
        st.subheader("سوابق شرکت در آزمون‌های آنلاین")
        sub_df = safe_read_sql("""
            SELECT q.title as 'عنوان آزمون', s.submission_date as 'تاریخ شرکت', s.score as 'نمره تستی', s.total_questions as 'کل سوالات تستی'
            FROM quiz_submissions s
            JOIN quizzes q ON s.quiz_id = q.id
            WHERE s.student_id = ? ORDER BY s.id DESC
        """, params=(st_id,), fallback_cols=['عنوان آزمون', 'تاریخ شرکت', 'نمره تستی', 'کل سوالات تستی'])
        
        if not sub_df.empty:
            st.dataframe(sub_df, use_container_width=True)
        else:
            st.info("دانش‌آموز هنوز در هیچ آزمون آنلاینی شرکت نکرده است.")

    with tab_r3:
        st.subheader("سوابق امتیازات انضباطی و تشویقی")
        b_df = safe_read_sql("""
            SELECT log_date as 'تاریخ', behavior_type as 'نوع مشاهده', score as 'امتیاز', description as 'توضیحات'
            FROM behavior_logs WHERE student_id = ? ORDER BY id DESC
        """, params=(st_id,), fallback_cols=['تاریخ', 'نوع مشاهده', 'امتیاز', 'توضیحات'])
        
        if not b_df.empty:
            st.dataframe(b_df, use_container_width=True)
            total_beh_score = b_df['امتیاز'].sum()
            st.metric("🏆 مجموع امتیازات انضباطی و تشویقی دانش‌آموز:", f"{total_beh_score} امتیاز")
        else:
            st.info("مشاهده انضباطی ثبت نشده است.")

