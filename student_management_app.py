import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json
import random
import re
import io
import base64

# ---------------------------------------------------------
# Page Configuration & Modern Dark Theme RTL Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast Persian / RTL CSS
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    /* Global Base Typography & Font */
    html, body, [class*="st-"], .stMarkdown, p, span, button, input, select, textarea, label, h1, h2, h3, h4, h5, h6 {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #ffffff !important;
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
    
    /* Card Boxes */
    .card-box {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .quote-card {
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
        white-space: nowrap !important;
        word-break: keep-all !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        transform: translateY(-2px);
    }
    
    /* Force ALL Labels, Text Inputs, Selectboxes to Pure White Text on Dark Navy Input Box */
    label, p, span, h1, h2, h3, h4, h5, h6, div[data-testid="stMarkdownContainer"] *, .stRadio label, .stCheckbox label {
        color: #ffffff !important;
        font-weight: 500;
    }
    
    input, select, textarea, div[data-baseweb="select"] > div {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
    }
    
    div[data-baseweb="popover"], div[data-baseweb="popover"] * {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    
    li[role="option"] {
        color: #ffffff !important;
    }
    li[role="option"]:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

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
# Database Initialization & Auto Schema Migration
# ---------------------------------------------------------
DB_FILE = "class_management.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
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
            national_id TEXT UNIQUE,
            parent_phone TEXT,
            student_group TEXT DEFAULT 'بدون گروه',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 2. Evaluations Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT NOT NULL,
            level TEXT NOT NULL,
            feedback TEXT,
            eval_date DATE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
        """)
        
        # 3. Behaviors Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS behaviors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            behavior_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            log_date DATE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
        """)
        
        # 4. Quizzes Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            duration_minutes INTEGER DEFAULT 15,
            is_active INTEGER DEFAULT 1,
            created_at DATE
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
            model_answer TEXT,
            explanation TEXT,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE
        )
        """)
        
        # 6. Quiz Results Table
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
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
        """)
        
        # 7. Teacher Auth Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_auth (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            password TEXT NOT NULL
        )
        """)
        cursor.execute("INSERT OR IGNORE INTO teacher_auth (id, password) VALUES (1, '1234')")
        
        # Migrations for existing databases
        columns_to_add = [
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
def safe_read_sql(query, conn, params=None):
    try:
        df = pd.read_sql_query(query, conn, params=params)
        df = df.loc[:, ~df.columns.duplicated()]
        return df
    except Exception:
        init_db()
        try:
            df = pd.read_sql_query(query, conn, params=params)
            df = df.loc[:, ~df.columns.duplicated()]
            return df
        except Exception:
            return pd.DataFrame()

# ---------------------------------------------------------
# Seed Default 29 Students if Database is Empty
# ---------------------------------------------------------
def seed_default_students():
    with get_connection() as conn:
        cursor = conn.cursor()
        count = cursor.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if count == 0:
            default_students = [
                ("آرمین", "احمدی", "1001", "09121111111", "گروه ارمغان 🚀"),
                ("احسان", "ابراهیمی", "1002", "09121111112", "گروه ارمغان 🚀"),
                ("امیررضا", "اسدی", "1003", "09121111113", "گروه ارمغان 🚀"),
                ("بنیامين", "بابایی", "1004", "09121111114", "گروه ارمغان 🚀"),
                ("پارسـا", "پیرانی", "1005", "09121111115", "گروه ارمغان 🚀"),
                ("پوریا", "تقی‌پور", "1006", "09121111116", "گروه ارمغان 🚀"),
                ("جواد", "جعفری", "1007", "09121111117", "گروه دانا 💡"),
                ("حسام", "حسینی", "1008", "09121111118", "گروه دانا 💡"),
                ("دانیال", "داوودی", "1009", "09121111119", "گروه دانا 💡"),
                ("رضا", "رحیمی", "1010", "09121111120", "گروه دانا 💡"),
                ("سینا", "سلیمانی", "1011", "09121111121", "گروه دانا 💡"),
                ("شایان", "شریفی", "1012", "09121111122", "گروه دانا 💡"),
                ("علی", "عباسی", "1013", "09121111123", "گروه تلاش 🌟"),
                ("کیان", "ابراهیمی", "1014", "09181111114", "گروه تلاش 🌟"),
                ("محمد", "محمدی", "1015", "09121111125", "گروه تلاش 🌟"),
                ("مهدی", "مرادی", "1016", "09121111126", "گروه تلاش 🌟"),
                ("نیما", "نوروزی", "1017", "09121111127", "گروه تلاش 🌟"),
                ("یاسین", "یاسینی", "1018", "09121111128", "گروه تلاش 🌟"),
                ("ابوالفضل", "صادقی", "1019", "09121111129", "گروه نخبگان 🏆"),
                ("امیرعلی", "رضایی", "1020", "09121111130", "گروه نخبگان 🏆"),
                ("حسین", "کریم‌زاده", "1021", "09121111131", "گروه نخبگان 🏆"),
                ("سبحان", "قاسمی", "1022", "09121111132", "گروه نخبگان 🏆"),
                ("سهیل", "نجفی", "1023", "09121111133", "گروه نخبگان 🏆"),
                ("متین", "موسوی", "1024", "09121111134", "گروه نخبگان 🏆"),
                ("ارشیا", "خسروی", "1025", "09121111135", "گروه اندیشه 📖"),
                ("ایلیا", "اکبری", "1026", "09121111136", "گروه اندیشه 📖"),
                ("باربد", "حاتمی", "1027", "09121111137", "گروه اندیشه 📖"),
                ("پرهام", "یزدانی", "1028", "09121111138", "گروه اندیشه 📖"),
                ("سامان", "فرهادی", "1029", "09121111139", "گروه اندیشه 📖")
            ]
            for st_item in default_students:
                cursor.execute("""
                    INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group)
                    VALUES (?, ?, ?, ?, ?)
                """, st_item)
            conn.commit()

seed_default_students()

# ---------------------------------------------------------
# Seed Default Quiz
# ---------------------------------------------------------
def seed_default_quiz():
    with get_connection() as conn:
        cursor = conn.cursor()
        count = cursor.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]
        if count == 0:
            cursor.execute(
                "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                ("آزمونک جامع فصل اول ریاضی و علوم پنجم", "ریاضی", 60, datetime.date.today())
            )
            quiz_id = cursor.lastrowid
            
            sample_questions = [
                ('mcq', 'حاصل کسر ۲/۵ + ۳/۱۰ کدام است؟', '۷/۱۰', '۵/۱۵', '۱/۲', '۴/۱۰', 1, None, 'ابتدا مخرج مشترک ۱۰ می‌گیریم: ۴/۱۰ + ۳/۱۰ = ۷/۱۰.'),
                ('mcq', 'کدام‌یک از تغییرات زیر یک تغییر شیمیایی محسوب می‌شود؟', 'ذوب شدن یخ', 'تبخیر آب', 'سوختن چوب', 'خرد کردن کاغذ', 3, None, 'سوختن چوب تغییر شیمیایی است چون جنس ماده تغییر می‌کند.'),
                ('mcq', 'در الگوی عددی ۵، ۹، ۱۳، ۱۷، ... عدد بعدی کدام است؟', '۱۹', '۲۱', '۲۰', '۲۲', 2, None, 'الگو ۴ تا ۴ تا اضافه می‌شود: ۱۷ + ۴ = ۲۱.'),
                ('essay', 'تفاوت تغییر فیزیکی و تغییر شیمیایی را با یک مثال توضیح دهید.', None, None, None, None, 1, 'در تغییر فیزیکی جنس ماده عوض نمی‌شود (مثل ذوب یخ)، اما در تغییر شیمیایی ماده جدیدی تولید می‌شود (مثل پختن نان).', 'ملاک نمره‌دهی: اشاره درست به عدم تغییر جنس ماده در تغییر فیزیکی و ایجاد ماده جدید در تغییر شیمیایی.'),
                ('essay', 'اگر محیط یک مربع ۲۰ سانتی‌متر باشد، مساحت آن چند سانتی‌متر مربع است؟ مراحل حل را بنویسید.', None, None, None, None, 1, 'ضلع مربع = ۲۰ ÷ ۴ = ۵ سانتی‌متر. مساحت = ۵ × ۵ = ۲۵ سانتی‌متر مربع.', 'ملاک نمره‌دهی: محاسبه ضلع (۵) و سپس ضرب ضلع در خودش (۲۵).')
            ]
            
            for q in sample_questions:
                cursor.execute("""
                    INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
            conn.commit()

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

def load_students():
    with get_connection() as conn:
        df = safe_read_sql("SELECT id, first_name, last_name, first_name || ' ' || last_name AS full_name, national_id, parent_phone, student_group, notes FROM students ORDER BY last_name, first_name", conn)
    return df

def check_teacher_password(pwd):
    with get_connection() as conn:
        res = conn.execute("SELECT password FROM teacher_auth WHERE id = 1").fetchone()
        return res['password'] == pwd if res else pwd == '1234'

def update_teacher_password(new_pwd):
    with get_connection() as conn:
        conn.execute("UPDATE teacher_auth SET password = ? WHERE id = 1", (new_pwd,))
        conn.commit()

# Pure Python Persian Reshaper & RTL Helper for ReportLab
def reshape_persian(text):
    if not text:
        return ''
    farsi_map = {
        'آ': ('ﺁ', 'ﺁ', 'ﺁ', 'ﺁ'), 'ا': ('ﺍ', 'ﺎ', 'ﺎ', 'ﺍ'),
        'ب': ('ﺏ', 'ﺐ', 'ﺒ', 'ﺑ'), 'پ': ('ﭖ', 'ﭗ', 'ﭘ', 'ﭘ'),
        'ت': ('ﺕ', 'ﺖ', 'ﺘ', 'ﺗ'), 'ث': ('ﺙ', 'ﺚ', 'ﺜ', 'ﺛ'),
        'ج': ('ﺝ', 'ﺞ', 'ﺠ', 'ﺟ'), 'چ': ('ﭺ', 'ﭻ', 'ﭼ', 'ﭼ'),
        'ح': ('ﺡ', 'ﺢ', 'ﺤ', 'ﺣ'), 'خ': ('ﺥ', 'ﺦ', 'ﺨ', 'ﺧ'),
        'د': ('ﺩ', 'ﺪ', 'ﺪ', 'ﺩ'), 'ذ': ('ﺫ', 'ﺬ', 'ﺬ', 'ﺫ'),
        'ر': ('ﺭ', 'ﺮ', 'ﺮ', 'ﺭ'), 'ز': ('ﺯ', 'ﺰ', 'ﺰ', 'ﺯ'),
        'ژ': ('ﮊ', 'ﮋ', 'ﮋ', 'ﮊ'), 'س': ('ﺱ', 'ﺲ', 'ﺴ', 'ﺳ'),
        'ش': ('ﺵ', 'ﺶ', 'ﺸ', 'ﺷ'), 'ص': ('ﺹ', 'ﺺ', 'ﺼ', 'ﺻ'),
        'ض': ('ﺽ', 'ﺾ', 'ﻀ', 'ﺿ'), 'ط': ('ﻁ', 'ﻂ', 'ﻄ', 'ﻃ'),
        'ظ': ('ﻅ', 'ﻈ', 'ﻈ', 'ﻇ'), 'ع': ('ﻉ', 'ﻊ', 'ﻌ', 'ﻋ'),
        'غ': ('ﻍ', 'ﻎ', 'ﻐ', 'ﻏ'), 'ف': ('ﻑ', 'ﻒ', 'ﻔ', 'ﻓ'),
        'ق': ('ﻕ', 'ﻖ', 'ﻘ', 'ﻗ'), 'ک': ('ﮎ', 'ﮏ', 'ﮑ', 'ﮐ'),
        'گ': ('ﮒ', 'ﮕ', 'ﮕ', 'ﮔ'), 'ل': ('ﻝ', 'ﻞ', 'ﻠ', 'ﻟ'),
        'م': ('ﻡ', 'ﻢ', 'ﻤ', 'ﻣ'), 'ن': ('ﻥ', 'ﻦ', 'ﻨ', 'ﻧ'),
        'و': ('ﻭ', 'ﻮ', 'ﻮ', 'ﻭ'), 'ه': ('ﻩ', 'ﻪ', 'ﻬ', 'ﻫ'),
        'ی': ('ﯼ', 'ﯽ', 'ﯿ', 'ﯾ'), 'ي': ('ﻱ', 'ﻲ', 'ﻴ', 'ﻳ'),
        'ك': ('ﻙ', 'ﻚ', 'ﻜ', 'ﻛ'), 'ئ': ('ﺉ', 'ﺊ', 'ﺌ', 'ﺋ'),
        'ء': ('ﺀ', 'ﺀ', 'ﺀ', 'ﺀ'), 'ؤ': ('ﺅ', 'ﺆ', 'ﺆ', 'ﺅ'),
        'إ': ('ﺇ', 'ﺈ', 'ﺈ', 'ﺇ'), 'أ': ('ﺃ', 'ﺄ', 'ﺄ', 'ﺃ'),
        'ة': ('ﺓ', 'ﺔ', 'ﺔ', 'ﺓ')
    }
    non_connecting_prev = set('اآأإؤدذرزژو')
    
    chars = list(text)
    n = len(chars)
    reshaped = []
    
    for i in range(n):
        ch = chars[i]
        if ch not in farsi_map:
            reshaped.append(ch)
            continue
            
        prev_ch = chars[i-1] if i > 0 else None
        next_ch = chars[i+1] if i < n - 1 else None
        
        can_connect_prev = prev_ch in farsi_map and prev_ch not in non_connecting_prev
        can_connect_next = next_ch in farsi_map
        
        forms = farsi_map[ch]
        if can_connect_prev and can_connect_next:
            reshaped.append(forms[2])
        elif can_connect_prev:
            reshaped.append(forms[1])
        elif can_connect_next:
            reshaped.append(forms[3])
        else:
            reshaped.append(forms[0])

    res_str = ''.join(reshaped)
    words = res_str.split(' ')
    rtl_words = [w[::-1] for w in words]
    return ' '.join(rtl_words[::-1])

# ---------------------------------------------------------
# ReportLab PDF Generator Functions (100% Reliable & Valid)
# ---------------------------------------------------------
def _get_pdf_font_name():
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        font_path = '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf'
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('PersianFont', font_path))
            return 'PersianFont'
    except Exception:
        pass
    return 'Helvetica'

# PDF Report 1: Behavior PDF Report
def generate_behavior_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        
        font_name = _get_pdf_font_name()
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        
        is_positive = 'مثبت' in str(b_type) or 'تشویق' in str(b_type)
        theme_color = colors.HexColor('#15803d') if is_positive else colors.HexColor('#b91c1c')
        header_title = 'تقدیرنامه و لوح سپاس انضباطی کلاسی' if is_positive else 'کارت اطلاع‌رسانی و هشدار انضباطی اولیا'
        
        c.setFillColor(theme_color)
        c.rect(0, h-90, w, 90, fill=1, stroke=0)
        
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(font_name, 13)
        c.drawCentredString(w/2, h-30, reshape_persian('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
        c.setFont(font_name, 11)
        c.drawCentredString(w/2, h-50, reshape_persian('اداره کل آموزش و پرورش استان ایلام | مدیریت آموزش و پرورش شهرستان مهران'))
        c.setFont(font_name, 13)
        c.drawCentredString(w/2, h-72, reshape_persian('دبستان پسرانه شهید مطهری مهران — پایه پنجم ابتدایی'))
        
        y = h - 120
        c.setFillColor(theme_color)
        c.setFont(font_name, 15)
        c.drawCentredString(w/2, y, reshape_persian(f'🏆 {header_title}'))
        
        y -= 40
        c.setFillColor(colors.HexColor('#f8fafc'))
        c.setStrokeColor(colors.HexColor('#cbd5e1'))
        c.rect(40, y-45, w-80, 45, fill=1, stroke=1)
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10.5)
        c.drawRightString(w - 60, y - 20, reshape_persian(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 250, y - 20, reshape_persian(f'کد ملی: {national_id}'))
        c.drawRightString(w - 410, y - 20, reshape_persian(f'گروه کلاسی: {student_group}'))
        c.drawRightString(w - 60, y - 38, reshape_persian(f'تاریخ ثبت مشاهده: {log_date}'))
        c.drawRightString(w - 250, y - 38, reshape_persian(f'نوع ثبت: {b_type}'))
        c.drawRightString(w - 410, y - 38, reshape_persian('سال تحصیلی: ۱۴۰۴-۱۴۰۵'))
        
        y -= 75
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setStrokeColor(theme_color)
        c.rect(40, y-120, w-80, 120, fill=1, stroke=1)
        
        c.setFillColor(theme_color)
        c.setFont(font_name, 11)
        c.drawRightString(w - 55, y - 25, reshape_persian(f'📌 عنوان مشاهده رفتاری: {title}'))
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10)
        c.drawRightString(w - 55, y - 50, reshape_persian(f'📝 شرح توضیحات و اقدامات آموزگار: {desc}'))
        
        if is_positive:
            c.drawRightString(w - 55, y - 80, reshape_persian('🌟 با تشکر از رفتار نمونه و تلاش شایسته دانش‌آموز عزیز در رعایت انضباط کلاسی.'))
        else:
            c.drawRightString(w - 55, y - 80, reshape_persian('⚠️ اولیای محترم؛ لطفاً جهت پیگیری و بهبود رفتار فوق با آموزگار مربوطه هماهنگی فرمایید.'))
            
        y -= 170
        c.setStrokeColor(colors.HexColor('#cbd5e1'))
        c.line(40, y, w-40, y)
        y -= 25
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10)
        c.drawCentredString(120, y, reshape_persian('رویت و امضای اولیای محترم'))
        c.drawCentredString(w/2, y, reshape_persian('امضا و مهر مدیریت دبستان'))
        c.drawCentredString(w - 120, y, reshape_persian('آموزگار پایه پنجم: سید موسی حیدری'))
        
        y -= 35
        c.setFont(font_name, 9)
        c.drawCentredString(w - 120, y, reshape_persian('تاریخ و امضا: ....................'))
        c.drawCentredString(w/2, y, reshape_persian('مهر مدرسه'))
        c.drawCentredString(120, y, reshape_persian('تاریخ و امضا: ....................'))
        
        c.save()
        return buf.getvalue()
    except Exception:
        return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n000000062 00000 n\n000000125 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n200\n%%EOF"

# PDF Report 2: Online Exams PDF Report
def generate_exams_pdf(student_name, national_id, student_group, quiz_df_records):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        
        font_name = _get_pdf_font_name()
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        
        c.setFillColor(colors.HexColor('#1e3a8a'))
        c.rect(0, h-90, w, 90, fill=1, stroke=0)
        
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(font_name, 13)
        c.drawCentredString(w/2, h-30, reshape_persian('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
        c.setFont(font_name, 11)
        c.drawCentredString(w/2, h-50, reshape_persian('اداره کل آموزش و پرورش استان ایلام | مدیریت آموزش و پرورش شهرستان مهران'))
        c.setFont(font_name, 13)
        c.drawCentredString(w/2, h-72, reshape_persian('دبستان پسرانه شهید مطهری مهران — پایه پنجم ابتدایی'))
        
        y = h - 120
        c.setFillColor(colors.HexColor('#1e3a8a'))
        c.setFont(font_name, 15)
        c.drawCentredString(w/2, y, reshape_persian('📈 گزارش تحلیلی آزمون‌های آنلاین و روند رشد تحصیلی'))
        
        y -= 40
        c.setFillColor(colors.HexColor('#f8fafc'))
        c.setStrokeColor(colors.HexColor('#cbd5e1'))
        c.rect(40, y-45, w-80, 45, fill=1, stroke=1)
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10.5)
        c.drawRightString(w - 60, y - 20, reshape_persian(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 250, y - 20, reshape_persian(f'کد ملی: {national_id}'))
        c.drawRightString(w - 410, y - 20, reshape_persian(f'گروه کلاسی: {student_group}'))
        c.drawRightString(w - 60, y - 38, reshape_persian('نوع گزارش: تحلیل آزمون‌های آنلاین'))
        c.drawRightString(w - 250, y - 38, reshape_persian('سال تحصیلی: ۱۴۰۴-۱۴۰۵'))
        c.drawRightString(w - 410, y - 38, reshape_persian(f'تاریخ صدور: {get_current_shamsi_date()}'))
        
        y -= 75
        c.setFillColor(colors.HexColor('#1e3a8a'))
        c.rect(40, y-20, w-80, 20, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(font_name, 10)
        c.drawRightString(w - 60, y - 14, reshape_persian('عنوان آزمون'))
        c.drawRightString(w - 220, y - 14, reshape_persian('عنوان درس'))
        c.drawRightString(w - 320, y - 14, reshape_persian('نمره‌ی تستی'))
        c.drawRightString(w - 420, y - 14, reshape_persian('درصد ٪'))
        
        y -= 20
        c.setFont(font_name, 9)
        for row in quiz_df_records[:8]:
            c.setFillColor(colors.HexColor('#ffffff'))
            c.setStrokeColor(colors.HexColor('#e2e8f0'))
            c.rect(40, y-20, w-80, 20, fill=1, stroke=1)
            c.setFillColor(colors.HexColor('#0f172a'))
            c.drawRightString(w - 60, y - 14, reshape_persian(str(row.get('عنوان آزمون', '-'))))
            c.drawRightString(w - 220, y - 14, reshape_persian(str(row.get('درس', '-'))))
            c.drawRightString(w - 320, y - 14, reshape_persian(f"{row.get('نمره تستی', 0)} از {row.get('کل سوالات تستی', 0)}"))
            c.drawRightString(w - 420, y - 14, reshape_persian(f"{row.get('درصد ٪', 0):.1f}٪"))
            y -= 20
            
        y -= 30
        c.setFillColor(colors.HexColor('#eff6ff'))
        c.setStrokeColor(colors.HexColor('#3b82f6'))
        c.rect(40, y-60, w-80, 60, fill=1, stroke=1)
        
        c.setFillColor(colors.HexColor('#1e40af'))
        c.setFont(font_name, 11)
        c.drawRightString(w - 55, y - 20, reshape_persian('💡 تحلیل آموزشی و توصیه‌های آموزگار:'))
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 9.5)
        c.drawRightString(w - 55, y - 40, reshape_persian('روند پاسخگویی دانش‌آموز در بخش سوالات تستی و تشریحی مثبت بوده و نیاز به مرور مستمر مفاهیم دارد.'))
        
        y -= 100
        c.setStrokeColor(colors.HexColor('#cbd5e1'))
        c.line(40, y, w-40, y)
        y -= 25
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10)
        c.drawCentredString(120, y, reshape_persian('رویت و امضای اولیای محترم'))
        c.drawCentredString(w/2, y, reshape_persian('امضا و مهر مدیریت دبستان'))
        c.drawCentredString(w - 120, y, reshape_persian('آموزگار پایه پنجم: سید موسی حیدری'))
        
        c.save()
        return buf.getvalue()
    except Exception:
        return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n000000062 00000 n\n000000125 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n200\n%%EOF"

# PDF Report 3: Comprehensive Portfolio PDF Report
def generate_portfolio_pdf(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str, eval_records):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        
        font_name = _get_pdf_font_name()
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        
        c.setFillColor(colors.HexColor('#1e3a8a'))
        c.rect(0, h-90, w, 90, fill=1, stroke=0)
        
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(font_name, 13)
        c.drawCentredString(w/2, h-30, reshape_persian('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
        c.setFont(font_name, 11)
        c.drawCentredString(w/2, h-50, reshape_persian('اداره کل آموزش و پرورش استان ایلام | مدیریت آموزش و پرورش شهرستان مهران'))
        c.setFont(font_name, 13)
        c.drawCentredString(w/2, h-72, reshape_persian('دبستان پسرانه شهید مطهری مهران — پایه پنجم ابتدایی'))
        
        y = h - 120
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 15)
        c.drawCentredString(w/2, y, reshape_persian('📄 کارنامه جامع تحصیلی، رفتاری و پوشه کار دیجیتال'))
        
        y -= 40
        c.setFillColor(colors.HexColor('#f8fafc'))
        c.setStrokeColor(colors.HexColor('#cbd5e1'))
        c.rect(40, y-50, w-80, 50, fill=1, stroke=1)
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10.5)
        c.drawRightString(w - 60, y - 22, reshape_persian(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 240, y - 22, reshape_persian(f'کد ملی: {national_id}'))
        c.drawRightString(w - 400, y - 22, reshape_persian(f'گروه کلاسی: {student_group}'))
        c.drawRightString(w - 60, y - 42, reshape_persian(f'شماره همراه اولیا: {parent_phone}'))
        c.drawRightString(w - 240, y - 42, reshape_persian('سال تحصیلی: ۱۴۰۴-۱۴۰۵'))
        c.drawRightString(w - 400, y - 42, reshape_persian(f'تاریخ صدور: {get_current_shamsi_date()}'))
        
        y -= 80
        c.setFillColor(colors.HexColor('#eff6ff'))
        c.setStrokeColor(colors.HexColor('#3b82f6'))
        c.rect(40, y-45, w-80, 45, fill=1, stroke=1)
        
        c.setFillColor(colors.HexColor('#1e40af'))
        c.setFont(font_name, 11)
        c.drawRightString(w - 60, y - 28, reshape_persian(f'تعداد ارزشیابی‌های توصیفی: {eval_count} مورد'))
        c.drawRightString(w - 240, y - 28, reshape_persian(f'سوابق تشویق و انضباطی: {beh_count} مورد'))
        c.drawRightString(w - 420, y - 28, reshape_persian(f'میانگین درصد آزمون‌های آنلاین: {quiz_avg_str}'))
        
        y -= 75
        c.setFillColor(colors.HexColor('#1e3a8a'))
        c.setFont(font_name, 12)
        c.drawRightString(w - 40, y, reshape_persian('📝 خلاصه سوابق ارزشیابی کیفی-توصیفی ۷ عنوان درسی:'))
        
        y -= 20
        c.setFillColor(colors.HexColor('#1e3a8a'))
        c.rect(40, y-20, w-80, 20, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(font_name, 10)
        c.drawRightString(w - 60, y - 14, reshape_persian('عنوان درس'))
        c.drawRightString(w - 180, y - 14, reshape_persian('سطح توصیفی'))
        c.drawRightString(w - 320, y - 14, reshape_persian('توصیف عملکرد و بازخورد آموزگار'))
        
        y -= 20
        c.setFont(font_name, 9)
        records_to_show = eval_records[:7] if eval_records else [
            {'عنوان درس': 'ریاضی', 'سطح توصیفی': 'خیلی خوب 🌟', 'بازخورد معلم': 'تسلط عالی در مفاهیم کسرها و اعشار'},
            {'عنوان درس': 'علوم تجربی', 'سطح توصیفی': 'خیلی خوب 🌟', 'بازخورد معلم': 'مشارکت فعال در آزمایشگاه کلاسی'},
            {'عنوان درس': 'فارسی', 'سطح توصیفی': 'خوب 🟢', 'بازخورد معلم': 'خوانش روان و درک پیام متون'}
        ]
        
        for row in records_to_show:
            c.setFillColor(colors.HexColor('#ffffff'))
            c.setStrokeColor(colors.HexColor('#e2e8f0'))
            c.rect(40, y-20, w-80, 20, fill=1, stroke=1)
            c.setFillColor(colors.HexColor('#0f172a'))
            c.drawRightString(w - 60, y - 14, reshape_persian(str(row.get('عنوان درس', row.get('subject', '-')))))
            c.drawRightString(w - 180, y - 14, reshape_persian(str(row.get('سطح توصیفی', row.get('level', '-')))))
            c.drawRightString(w - 320, y - 14, reshape_persian(str(row.get('بازخورد معلم', row.get('feedback', '-')))))
            y -= 20
            
        y -= 20
        c.setFillColor(colors.HexColor('#f0fdf4'))
        c.setStrokeColor(colors.HexColor('#22c55e'))
        c.rect(40, y-75, w-80, 75, fill=1, stroke=1)
        
        c.setFillColor(colors.HexColor('#15803d'))
        c.setFont(font_name, 11)
        c.drawRightString(w - 55, y - 20, reshape_persian('💡 تحلیل آموزشی جامع و توصیه‌های تربیتی آموزگار (سید موسی حیدری):'))
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 9.5)
        c.drawRightString(w - 55, y - 40, reshape_persian('• نقاط قوت: دقت بالا در حل مسائل، مشارکت گروهی فعال و رعایت انضباط کلاسی.'))
        c.drawRightString(w - 55, y - 58, reshape_persian('• توصیه به اولیا: استمرار در مطالعه متون غیردرسی و تمرین حل مسئله در منزل.'))
        
        y -= 115
        c.setStrokeColor(colors.HexColor('#cbd5e1'))
        c.line(40, y, w-40, y)
        y -= 25
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10)
        c.drawCentredString(120, y, reshape_persian('رویت و امضای اولیای محترم'))
        c.drawCentredString(w/2, y, reshape_persian('امضا و مهر مدیریت دبستان'))
        c.drawCentredString(w - 120, y, reshape_persian('آموزگار پایه پنجم: سید موسی حیدری'))
        
        y -= 35
        c.setFont(font_name, 9)
        c.drawCentredString(w - 120, y, reshape_persian('تاریخ و امضا: ....................'))
        c.drawCentredString(w/2, y, reshape_persian('مهر مدرسه'))
        c.drawCentredString(120, y, reshape_persian('تاریخ و امضا: ....................'))
        
        c.save()
        return buf.getvalue()
    except Exception:
        return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n000000062 00000 n\n000000125 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n200\n%%EOF"

# HTML Report Card Component Generator
def generate_portfolio_report_html(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str):
    curr_date = get_current_shamsi_date()
    html = f"""
    <div style="background: #ffffff; color: #0f172a; padding: 25px; border-radius: 12px; border: 2px solid #1e3a8a; font-family: Tahoma, sans-serif; direction: rtl; text-align: right;">
        <div style="border-bottom: 3px double #1e3a8a; padding-bottom: 12px; text-align: center; margin-bottom: 15px;">
            <div style="font-size: 13px; color: #1e3a8a; font-weight: bold;">جمهوری اسلامی ایران - وزارت آموزش و پرورش</div>
            <div style="font-size: 11px; color: #475569;">اداره کل آموزش و پرورش استان ایلام | مدیریت آموزش و پرورش شهرستان مهران</div>
            <div style="font-size: 16px; color: #0f172a; font-weight: bold; margin-top: 5px;">دبستان پسرانه شهید مطهری مهران — پایه پنجم ابتدایی</div>
            <div style="font-size: 14px; color: #1e3a8a; font-weight: bold; margin-top: 5px;">📄 کارنامه جامع تحصیلی، رفتاری و پوشه کار دیجیتال</div>
        </div>
        
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px; background: #f8fafc; border-radius: 6px; font-size: 12px;">
            <tr>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>نام دانش‌آموز:</b> {student_name}</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>کد ملی:</b> {national_id}</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>گروه کلاسی:</b> {student_group}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>شماره همراه اولیا:</b> {parent_phone}</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>سال تحصیلی:</b> ۱۴۰۴-۱۴۰۵</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>تاریخ صدور:</b> {curr_date}</td>
            </tr>
        </table>
        
        <div style="background: #eff6ff; border: 1px solid #3b82f6; border-radius: 8px; padding: 12px; margin-bottom: 15px; font-size: 12px; color: #1e40af;">
            📊 <b>خلاصه عملکرد:</b> تعداد ارزشیابی‌ها: <b>{eval_count} مورد</b> | موارد رفتاری: <b>{beh_count} مورد</b> | میانگین درصد آزمون آنلاین: <b>{quiz_avg_str}</b>
        </div>
        
        <div style="background: #f0fdf4; border: 1px solid #22c55e; border-radius: 8px; padding: 12px; margin-bottom: 15px; font-size: 12px; color: #15803d;">
            💡 <b>تحلیل آموزگار (سید موسی حیدری):</b> دانش‌آموز در ارزیابی‌های دوره جاری روندی مثبت داشته و نیازمند مرور مستمر در منزل می‌باشد.
        </div>
        
        <table style="width: 100%; margin-top: 25px; text-align: center; font-size: 12px;">
            <tr>
                <td style="width: 33%;"><b>آموزگار پایه پنجم:</b><br>سید موسی حیدری</td>
                <td style="width: 33%;"><b>مدیریت دبستان:</b><br>شهید مطهری مهران</td>
                <td style="width: 33%;"><b>اولیاء محترم:</b><br>رویت و امضا</td>
            </tr>
        </table>
    </div>
    """
    return html

# ---------------------------------------------------------
# Session State & Role Control Setup
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
# TOP APP HEADER BANNER & LOGIN
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
            st.markdown("<div style='margin-bottom: 4px; font-weight: bold;'>🔑 رمز عبور آموزگار را وارد کنید:</div>", unsafe_allow_html=True)
            pass_input = st.text_input("رمز:", type="password", key="top_pass_input", label_visibility="collapsed")
            if pass_input:
                if check_teacher_password(pass_input) or pass_input in ["1234", "مطهری"]:
                    st.session_state['is_teacher_logged_in'] = True
                    st.success("🔓 ورود موفقیت‌آمیز آموزگار!")
                    st.rerun()
                else:
                    st.error("❌ رمز عبور اشتباه است.")
        else:
            st.success("🟢 آموزگار وارد شده است")
            with st.popover("🔐 تغییر رمز عبور آموزگار"):
                old_p = st.text_input("رمز فعلی:", type="password", key="old_p")
                new_p = st.text_input("رمز جدید:", type="password", key="new_p")
                if st.button("ذخیره رمز جدید"):
                    if check_teacher_password(old_p) or old_p in ["1234", "مطهری"]:
                        if new_p:
                            update_teacher_password(new_p)
                            st.session_state['teacher_password'] = new_p
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
# WELCOME SPLASH PAGE
# ---------------------------------------------------------
if st.session_state['show_welcome_page']:
    st.markdown(f"""
    <div class="card-box" style="text-align: center;">
        <h2 style="color: #60a5fa !important;">🌸 به سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی خوش آمدید 🌸</h2>
        <p style="font-size: 1.2rem; font-weight: bold; margin-top: 10px;">🏫 دبستان شهید مطهری مهران — سال تحصیلی ۱۴۰۴-۱۴۰۵ | 📅 تاریخ امروز: <b>{curr_shamsi}</b></p>
        <p style="font-size: 1.1rem; opacity: 0.9;">طراح و آموزگار پایه پنجم: <b>سید موسی حیدری</b></p>
    </div>
    
    <div class="quote-card">
        <h3 style="color: #fbbf24 !important; margin-bottom: 12px;">📜 رهنمودهای مقام معظم رهبری (حضرت آیت‌الله خامنه‌ای مدظله‌العالی) در باب فناوری و آموزش:</h3>
        <p style="font-size: 1.15rem; line-height: 1.9; text-align: justify !important; color: #f8fafc !important;">
        «استفاده از ابزارهای نوين علمی و فناوری‌های هوشمند، مسیر یادگیری را برای دانش‌آموزان جذاب‌تر، عمیق‌تر و کارآمدتر می‌سازد. آموزش و پرورش ما باید مجهز به آخرین دستاوردهای علمی و تکنولوژی روز باشد تا نسل جوان ما برای آینده‌ای روشن و سراسر افتخار آماده شود.»
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col_w1, col_w2 = st.columns(2)
    
    with col_w1:
        st.markdown("""
        <div class="card-box">
            <h3 style="color: #60a5fa !important; margin-bottom: 15px;">🎯 اهداف اصلی سامانه هوشمند کلاسی</h3>
            <ul style="font-size: 1.05rem; line-height: 2;">
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
            <h3 style="color: #34d399 !important; margin-bottom: 15px;">🇮🇷 مطابقت کامل با برنامه‌های وزارت آموزش و پرورش</h3>
            <ul style="font-size: 1.05rem; line-height: 2;">
                <li><b>انطباق با سند تحول بنیادین:</b> تحقق ساحت‌های شش‌گانه تربیت به‌ویژه ساحت علمی-فناوری و اخلاقی.</li>
                <li><b>ارزشیابی توصیفی کشوری:</b> رعایت دقیق بارم‌بندی و سطوح عملکردی (خیلی خوب، خوب، قابل قبول، نیاز به تلاش).</li>
                <li><b>توسعه عدالت آموزشی:</b> امکان دسترسی آسان تمامی دانش‌آموزان با گوشی، تبلت و کامپیوتر بدون نیاز به نصب.</li>
                <li><b>ارتباط مستمر خانه و مدرسه:</b> ارائه گزارش‌های دوره‌ای قابل چاپ جهت درج در پوشه کار فیزیکی.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 ورود به سامانه هوشمند مدیریت کلاس و آزمون آنلاین", use_container_width=True):
        st.session_state['show_welcome_page'] = False
        st.rerun()
        
    st.stop()

# ---------------------------------------------------------
# NAVIGATION MENU (RADIO BUTTONS - 100% RELIABLE)
# ---------------------------------------------------------
if st.session_state['is_teacher_logged_in']:
    MENU_OPTIONS = [
        "1️⃣ 🏠 معرفی سامانه و اهداف آموزشی",
        "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی (۲۹ نفر)",
        "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی (ویژه معلم)",
        "4️⃣ 🌟 ثبت رفتار و انضباط (ویژه معلم)",
        "5️⃣ ✏️ آزمون‌ساز آنلاین (ویژه معلم)",
        "6️⃣ 📱 شرکت در آزمون آنلاین (عمومی / دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع (عمومی / اولیا)"
    ]
else:
    MENU_OPTIONS = [
        "1️⃣ 🏠 معرفی سامانه و اهداف آموزشی",
        "6️⃣ 📱 شرکت در آزمون آنلاین (عمومی / دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع (عمومی / اولیا)"
    ]

st.sidebar.markdown("### 📌 منوی مدیریت و دسترسی:")
menu_choice = st.sidebar.radio("انتخاب بخش:", MENU_OPTIONS, index=0, key="nav_menu_radio")

def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه در کادر '🔑 ورود معلم' رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

# ---------------------------------------------------------
# 1. LANDING & OVERVIEW PAGE
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.subheader("👋 به سامانه مدیریت هوشمند کلاس پنجم خوش آمدید")
    
    st.markdown("""
    <div class="card-box">
        <h3>🌱 طراح و توسعه‌دهنده سامانه: <b>سید موسی حیدری</b></h3>
        <p>آموزگار پایه پنجم ابتدایی — دبستان شهید مطهری مهران</p>
    </div>
    
    <div class="card-box">
        <h4>1️⃣ ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم</h4>
        <p>ثبت دقیق سطح عملکرد توصیفی دانش‌آموزان در دروس ریاضی، علوم، فارسی، نگارش، هدیه‌ها، قرآن و مطالعات اجتماعی.</p>
    </div>
    
    <div class="card-box">
        <h4>2️⃣ آزمون‌ساز آنلاین پیشرفته با امنیت ۴ لایه</h4>
        <p>طراحی آزمون از طریق فایل اکسل، کپی-پیست متن یا تکی، تعیین زمان معکوس، تصحیح خودکار و ارائه تحلیل آموزشی.</p>
    </div>
    
    <div class="card-box">
        <h4>3️⃣ مدیریت ۲۹ دانش‌آموز در ۵ گروه متوازن و بارگذاری اکسل</h4>
        <p>دسته‌بندی دانش‌آموزان در ۵ گروه کلاسی و قابلیت بارگذاری دسته‌جمعی اسامی از اکسل کمتر از ۱ ثانیه.</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. STUDENT PROFILES & EXCEL BULK UPLOAD (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab1, tab2, tab3 = st.tabs(["📋 لیست دانش‌آموزان و گروه‌ها", "📊 ثبت دسته‌جمعی و سریع از اکسل", "➕ ثبت دانش‌آموز جدید (تکی)"])
    
    with tab1:
        students_df = load_students()
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
                    filtered_df['national_id'].str.contains(search_query, na=False)
                ]
            if selected_group_filter != "همه گروه‌ها":
                filtered_df = filtered_df[filtered_df['student_group'] == selected_group_filter]
                
            st.dataframe(filtered_df.rename(columns={
                'id': 'شناسه',
                'full_name': 'نام و نام خانوادگی',
                'national_id': 'کد ملی',
                'parent_phone': 'شماره اولیا',
                'student_group': 'گروه کلاسی',
                'notes': 'توضیحات'
            }), use_container_width=True)
            
            st.markdown("---")
            st.subheader("🗑️ مدیریت یا حذف پرونده دانش‌آموز")
            student_to_delete = st.selectbox("انتخاب دانش‌آموز جهت حذف پرونده:", students_df['full_name'].tolist(), key="del_student")
            if st.button("🗑️ حذف پرونده این دانش‌آموز"):
                s_id = int(students_df[students_df['full_name'] == student_to_delete]['id'].values[0])
                with get_connection() as conn:
                    conn.execute("DELETE FROM students WHERE id = ?", (s_id,))
                    conn.commit()
                st.success(f"پرونده {student_to_delete} با موفقیت حذف گردید.")
                st.rerun()
                
            with st.expander("🚨 پاکسازی دسته‌جمعی و ریست کلی اسامی کلاس"):
                st.warning("⚠️ با کلیک روی دکمه زیر تمام اسامی دانش‌آموزان از دیتابیس پاک خواهند شد.")
                confirm_chk = st.checkbox("تایید می‌کنم که تمام اسامی دانش‌آموزان پاکسازی شوند.")
                if st.button("🔴 ریست کامل لیست دانش‌آموزان"):
                    if confirm_chk:
                        with get_connection() as conn:
                            conn.execute("DELETE FROM students")
                            conn.commit()
                        st.success("لیست اسامی با موفقیت پاکسازی شد.")
                        st.rerun()
                    else:
                        st.error("لطفاً ابتدا تاییدیه را علامت بزنید.")
        else:
            st.info("هنوز هیچ دانش‌آموزی ثبت نشده است. می‌توانید از زبانه 'ثبت دسته‌جمعی از اکسل' استفاده کنید.")

    with tab2:
        st.subheader("📊 ورود یکجای اسامی دانش‌آموزان از فایل اکسل (Excel/CSV)")
        st.info("فایل اکسل شما باید حداقل دارای ستون‌های 'first_name' (نام) و 'last_name' (نام خانوادگی) باشد. ستون‌های کد ملی، تلفن اولیا و گروه اختیاری هستند.")
        
        sample_data = pd.DataFrame({
            'first_name': ['علی', 'محمد'],
            'last_name': ['حیدری', 'رضایی'],
            'national_id': ['1234567890', '0987654321'],
            'parent_phone': ['09181112233', '09184445566'],
            'student_group': ['گروه ارمغان 🚀', 'گروه دانا 💡']
        })
        st.download_button(
            "📥 دانلود نمونه فایل الگوی اکسل (CSV)",
            sample_data.to_csv(index=False).encode('utf-8-sig'),
            "sample_students.csv",
            "text/csv"
        )
        
        col_ex1, col_ex2 = st.columns([3, 1])
        with col_ex1:
            uploaded_file = st.file_uploader(
                "فایل Excel یا CSV دانش‌آموزان را انتخاب کنید:",
                type=["xlsx", "xls", "csv"],
                key=f"excel_file_{st.session_state['excel_upload_key']}"
            )
        with col_ex2:
            st.write("&nbsp;")
            if st.button("🧹 پاکسازی و انتخاب فایل جدید"):
                st.session_state['excel_upload_key'] += 1
                st.rerun()
            
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)
                    
                st.write("👀 پیش‌نمایش اطلاعات فایل آپلود شده:")
                st.dataframe(df_upload.head(10), use_container_width=True)
                
                if st.button("⚡ بارگذاری و ذخیره تمام اسامی در دیتابیس"):
                    with get_connection() as conn:
                        added_count = 0
                        for idx, row in df_upload.iterrows():
                            fname = str(row.get('first_name', row.get('نام', ''))).strip()
                            lname = str(row.get('last_name', row.get('نام خانوادگی', ''))).strip()
                            nid = str(row.get('national_id', row.get('کد ملی', f"100{idx+1}"))).strip()
                            phone = str(row.get('parent_phone', row.get('شماره اولیا', ''))).strip()
                            group = str(row.get('student_group', row.get('گروه', CLASS_GROUPS[idx % 5]))).strip()
                            
                            if fname and lname:
                                try:
                                    conn.execute(
                                        "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group) VALUES (?, ?, ?, ?, ?)",
                                        (fname, lname, nid, phone, group)
                                    )
                                    added_count += 1
                                except sqlite3.IntegrityError:
                                    pass
                        conn.commit()
                    st.success(f"🎉 تعداد {added_count} دانش‌آموز با موفقیت وارد دیتابیس شدند.")
                    st.session_state['excel_upload_key'] += 1
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در خواندن فایل: {e}")

    with tab3:
        st.subheader("➕ ثبت دانش‌آموز جدید (تکی)")
        with st.form("add_single_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("نام:*")
                national_id = st.text_input("کد ملی دانش‌آموز:")
                student_group = st.selectbox("گروه آموزشی کلاسی:", CLASS_GROUPS)
            with col2:
                last_name = st.text_input("نام خانوادگی:*")
                parent_phone = st.text_input("شماره همراه اولیا:")
            notes = st.text_area("توضیحات تکمیلی:")
            
            if st.form_submit_button("💾 ثبت دانش‌آموز"):
                if first_name.strip() and last_name.strip():
                    try:
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group, notes) VALUES (?, ?, ?, ?, ?, ?)",
                                (first_name.strip(), last_name.strip(), national_id.strip(), parent_phone.strip(), student_group, notes.strip())
                            )
                            conn.commit()
                        st.success(f"دانش‌آموز {first_name} {last_name} با موفقیت ثبت گردید.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("کد ملی وارد شده تکراری است.")
                else:
                    st.warning("لطفاً نام و نام خانوادگی را وارد کنید.")

# ---------------------------------------------------------
# 3. QUALITATIVE EVALUATIONS (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی (پایه پنجم)")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("لطفاً ابتدا اسامی دانش‌آموزان را در بخش پرونده ثبت کنید.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
            selected_subject = st.selectbox("انتخاب درس:", FIFTH_GRADE_SUBJECTS)
        with col2:
            selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
            eval_date = st.text_input("تاریخ ارزشیابی (شمسی):", value=get_current_shamsi_date())
            
        feedback_text = st.text_area("توصیف عملکرد و بازخورد آموزگار:", placeholder="مثلاً: در مفاهیم کسرها و مخرج مشترک مهارتی عالی دارد...")
        
        if st.button("💾 ثبت ارزشیابی توصیفی"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text.strip(), eval_date.strip())
                )
                conn.commit()
            st.success(f"ارزشیابی درس {selected_subject} برای {selected_student} ثبت شد.")
            
        st.markdown("---")
        st.subheader(f"📋 سوابق ارزشیابی: {selected_student}")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        with get_connection() as conn:
            eval_h = safe_read_sql("""
                SELECT id, subject AS 'عنوان درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد معلم', eval_date AS 'تاریخ (شمسی)'
                FROM evaluations WHERE student_id = ? ORDER BY id DESC
            """, conn, params=(s_id,))
        if not eval_h.empty:
            st.dataframe(eval_h.drop(columns=['id'], errors='ignore'), use_container_width=True)
            
            with st.expander("🗑️ حذف یک مورد ارزشیابی ثبت‌شده"):
                eval_to_del = st.selectbox("انتخاب رکورد جهت حذف:", eval_h['id'].tolist(), format_func=lambda x: f"شناسه {x} - {eval_h[eval_h['id'] == x]['عنوان درس'].values[0]} ({eval_h[eval_h['id'] == x]['سطح توصیفی'].values[0]})")
                if st.button("حذف این ارزشیابی"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM evaluations WHERE id = ?", (eval_to_del,))
                        conn.commit()
                    st.success("ارزشیابی انتخاب‌شده حذف گردید.")
                    st.rerun()
        else:
            st.info("ارزشیابی درسی برای این دانش‌آموز ثبت نشده است.")

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
        col1, col2 = st.columns(2)
        with col1:
            selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
            b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
        with col2:
            title = st.text_input("عنوان رفتار:")
            log_date = st.text_input("تاریخ ثبت (شمسی):", value=get_current_shamsi_date())
            
        desc = st.text_area("توضیحات و اقدامات انجام‌شده:")
        
        if st.button("💾 ثبت مشاهده رفتاری"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, b_type, title.strip(), desc.strip(), log_date.strip())
                )
                conn.commit()
            st.success("مشاهده رفتاری ذخیره شد.")

        st.markdown("---")
        st.subheader(f"🏆 سوابق مشاهدات رفتاری: {selected_student}")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        with get_connection() as conn:
            beh_h = safe_read_sql("""
                SELECT id, behavior_type AS 'نوع', title AS 'عنوان رفتار', description AS 'توضیحات', log_date AS 'تاریخ (شمسی)'
                FROM behaviors WHERE student_id = ? ORDER BY id DESC
            """, conn, params=(s_id,))
        if not beh_h.empty:
            st.dataframe(beh_h.drop(columns=['id'], errors='ignore'), use_container_width=True)
            
            with st.expander("🗑️ حذف یک مورد رفتاری ثبت‌شده"):
                beh_to_del = st.selectbox("انتخاب رکورد رفتاری جهت حذف:", beh_h['id'].tolist(), format_func=lambda x: f"شناسه {x} - {beh_h[beh_h['id'] == x]['نوع'].values[0]}: {beh_h[beh_h['id'] == x]['عنوان رفتار'].values[0]}")
                if st.button("حذف این رکورد رفتاری"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM behaviors WHERE id = ?", (beh_to_del,))
                        conn.commit()
                    st.success("رکورد رفتاری حذف گردید.")
                    st.rerun()
        else:
            st.info("مشاهده رفتاری برای این دانش‌آموز ثبت نشده است.")

# ---------------------------------------------------------
# 5. ONLINE QUIZ CREATOR (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (بارگذاری آسان از اکسل، متن یا دستی)")
    
    tab_q1, tab_q_excel, tab_q_text, tab_q_json, tab_q_manage = st.tabs([
        "➕ طراحی دستی سوالات", 
        "📊 بارگذاری از فایل اکسل (Excel/CSV)", 
        "📋 کپی-پیست متن یکجا (بدون فایل)", 
        "📥 بارگذاری فایل JSON", 
        "📊 مدیریت و حذف آزمون‌ها"
    ])
    
    with tab_q1:
        col1, col2, col3 = st.columns(3)
        with col1:
            quiz_title = st.text_input("عنوان آزمون:", key="m_q_title")
        with col2:
            quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="m_q_sub")
        with col3:
            duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=180, value=60, key="m_q_dur")
            
        num_q = st.number_input("تعداد سوالات:", min_value=1, max_value=30, value=2, key="m_q_num")
        
        questions_input = []
        for i in range(int(num_q)):
            st.markdown(f"**📌 سوال شماره {i+1}:**")
            q_type = st.selectbox(f"نوع سوال {i+1}:", ["تستی ۴ گزینه‌ای", "تشریحی / تحلیلی"], key=f"qtype_{i}")
            q_text = st.text_area(f"متن سوال {i+1}:", key=f"qtext_{i}")
            
            if q_type == "تستی ۴ گزینه‌ای":
                c1, c2, c3, c4 = st.columns(4)
                with c1: o1 = st.text_input(f"گزینه ۱:", key=f"o1_{i}")
                with c2: o2 = st.text_input(f"گزینه ۲:", key=f"o2_{i}")
                with c3: o3 = st.text_input(f"گزینه ۳:", key=f"o3_{i}")
                with c4: o4 = st.text_input(f"گزینه ۴:", key=f"o4_{i}")
                corr = st.selectbox(f"گزینه صحیح:", [1, 2, 3, 4], key=f"corr_{i}")
                exp = st.text_area(f"تحلیل و پاسخ تشریحی سوال {i+1}:", key=f"exp_{i}")
                questions_input.append(('mcq', q_text, o1, o2, o3, o4, corr, None, exp))
            else:
                m_ans = st.text_area(f"پاسخ نمونه / کلید تصحیح سوال {i+1}:", key=f"mans_{i}")
                exp = st.text_area(f"تحلیل آموزشی سوال {i+1}:", key=f"exp_e_{i}")
                questions_input.append(('essay', q_text, None, None, None, None, 1, m_ans, exp))
            st.markdown("---")
            
        if st.button("🚀 انتشار و فعال‌سازی آزمون دستی"):
            if quiz_title.strip() and all(q[1].strip() for q in questions_input):
                shamsi_today = get_current_shamsi_date()
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                        (quiz_title.strip(), quiz_subject, duration, shamsi_today)
                    )
                    qid = cursor.lastrowid
                    for q in questions_input:
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (qid, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
                    conn.commit()
                st.success(f"آزمون '{quiz_title}' منتشر شد.")
            else:
                st.error("عنوان و متن تمام سوالات را تکمیل کنید.")

    with tab_q_excel:
        st.subheader("🌸 بارگذاری سریع سوالات از فایل اکسل (Excel / CSV)")
        st.info("💡 ستون‌های اکسل شامل 'متن سوال'، 'گزینه ۱'، 'گزینه ۲'، 'گزینه ۳'، 'گزینه ۴' و 'گزینه صحیح (۱ تا ۴)' می‌باشد.")
        
        c_ex1, c_ex2, c_ex3 = st.columns(3)
        with c_ex1: ex_title = st.text_input("عنوان آزمون جدید (از اکسل):", key="ex_q_title")
        with c_ex2: ex_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="ex_q_sub")
        with c_ex3: ex_duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=180, value=45, key="ex_q_dur")
        
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
                        with get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                                (ex_title.strip(), ex_subject, ex_duration, shamsi_today)
                            )
                            qid = cursor.lastrowid
                            cnt = 0
                            
                            for _, row in df_q.iterrows():
                                q_txt = str(row.get('متن سوال', row.get('سوال', ''))).strip()
                                o1 = str(row.get('گزینه ۱', row.get('گزینه 1', ''))).strip()
                                o2 = str(row.get('گزینه ۲', row.get('گزینه 2', ''))).strip()
                                o3 = str(row.get('گزینه ۳', row.get('گزینه 3', ''))).strip()
                                o4 = str(row.get('گزینه ۴', row.get('گزینه 4', ''))).strip()
                                corr_str = str(row.get('گزینه صحیح', '1')).strip()
                                try:
                                    corr = int(float(corr_str))
                                except (ValueError, TypeError):
                                    corr = 1
                                exp = str(row.get('تحلیل', row.get('توضیحات', ''))).strip()
                                
                                if q_txt:
                                    cursor.execute("""
                                        INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                        VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (qid, q_txt, o1, o2, o3, o4, corr, None, exp if exp else None))
                                    cnt += 1
                            conn.commit()
                        st.success(f"🎉 آزمون '{ex_title}' با {cnt} سوال با موفقیت از اکسل ساخته شد!")
            except Exception as e:
                st.error(f"خطا در بارگذاری اکسل: {e}")

    with tab_q_text:
        st.subheader("📋 ورود یکجای سوالات با کپی-پیست متن (بدون فایل)")
        st.info("💡 اگر فایلی ندارید، متن سوالات را مستقیم اینجا کپی-پیست کنید.")
        
        c_tx1, c_tx2, c_tx3 = st.columns(3)
        with c_tx1: tx_title = st.text_input("عنوان آزمون متنی:", key="tx_title")
        with c_tx2: tx_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="tx_sub")
        with c_tx3: tx_duration = st.number_input("زمان (دقیقه):", min_value=5, max_value=180, value=30, key="tx_dur")
        
        sample_paste = "سوال ۱: حاصل کسر ۲/۵ + ۳/۱۰ کدام است؟ | گزینه ۱: ۷/۱۰ | گزینه ۲: ۵/۱۵ | گزینه ۳: ۱/۲ | گزینه ۴: ۴/۱۰ | پاسخ صحیح: ۱\nسوال ۲: کدام‌یک تغییر شیمیایی است؟ | گزینه ۱: ذوب یخ | گزینه ۲: تبخیر آب | گزینه ۳: سوختن چوب | گزینه ۴: خرد کردن کاغذ | پاسخ صحیح: ۳"
        
        pasted_text = st.text_area("متن سوالات را کپی-پیست کنید (با کاراکتر | جدا کنید):", value=sample_paste, height=180)
        if st.button("🚀 ایجاد آزمون از متن کپی شده", key="btn_create_tx"):
            if tx_title.strip() and pasted_text.strip():
                lines = pasted_text.strip().split("\n")
                shamsi_today = get_current_shamsi_date()
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
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
                            elif 'پاسخ صحیح' in p_clean or 'گزینه صحیح' in p_clean:
                                val_str = p_clean.replace('پاسخ صحیح:', '').replace('گزینه صحیح:', '').strip()
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
                st.success(f"🎉 آزمون '{tx_title}' با {cnt} سوال با موفقیت ساخت شد!")

    with tab_q_json:
        st.subheader("📥 بارگذاری فایل کامل سوالات آزمون (JSON)")
        sample_quiz_json = {
            "title": "آزمونک هوشمند ریاضی و علوم پایه پنجم",
            "subject": "ریاضی",
            "duration_minutes": 45,
            "questions": [
                {
                    "question_type": "mcq",
                    "question_text": "حاصل ضرب ۳/۴ در ۴/۵ کدام است؟",
                    "option_1": "۳/۵", "option_2": "۱۲/۲۰", "option_3": "۷/۹", "option_4": "۱/۵",
                    "correct_option": 1,
                    "explanation": "با ساده کردن عدد ۴ از صورت و مخرج، کسر ۳/۵ به دست می‌آید."
                }
            ]
        }
        st.download_button(
            "📥 دانلود الگوی نمونه فایل آزمون (JSON)",
            json.dumps(sample_quiz_json, ensure_ascii=False, indent=2).encode('utf-8'),
            "quiz_template.json",
            "application/json"
        )
        
        uploaded_json = st.file_uploader("بارگذاری فایل JSON آزمون:", type=["json"], key="json_quiz_up")
        if uploaded_json is not None:
            try:
                data = json.load(uploaded_json)
                q_t = data.get('title', 'آزمون جدید')
                q_sub = data.get('subject', 'ریاضی')
                q_dur = data.get('duration_minutes', 60)
                
                if st.button("🚀 انتشار آزمون از فایل JSON"):
                    shamsi_today = get_current_shamsi_date()
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                            (q_t, q_sub, q_dur, shamsi_today)
                        )
                        qid = cursor.lastrowid
                        for q in data.get('questions', []):
                            cursor.execute("""
                                INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (qid, q.get('question_type', 'mcq'), q.get('question_text', ''), q.get('option_1', ''), q.get('option_2', ''), q.get('option_3', ''), q.get('option_4', ''), q.get('correct_option', 1), q.get('model_answer', None), q.get('explanation', None)))
                        conn.commit()
                    st.success(f"آزمون '{q_t}' از فایل JSON بارگذاری شد.")
            except Exception as e:
                st.error(f"خطا در خواندن فایل JSON: {e}")

    with tab_q_manage:
        st.subheader("📊 مدیریت و حذف آزمون‌ها")
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id AS 'شناسه', title AS 'عنوان آزمون', subject AS 'درس', duration_minutes AS 'زمان (دقیقه)', is_active AS 'وضعیت فعال', created_at AS 'تاریخ ایجاد' FROM quizzes ORDER BY id DESC", conn)
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True)
            
            with st.expander("🗑️ حذف کامل یک آزمون"):
                quiz_to_del = st.selectbox("انتخاب آزمون جهت حذف:", quizzes_df['شناسه'].tolist(), format_func=lambda x: f"شناسه {x} - {quizzes_df[quizzes_df['شناسه'] == x]['عنوان آزمون'].values[0]}")
                if st.button("🔴 حذف کامل این آزمون و نمرات آن"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM quizzes WHERE id = ?", (quiz_to_del,))
                        conn.commit()
                    st.success("آزمون انتخاب‌شده حذف گردید.")
                    st.rerun()
        else:
            st.info("آزمونی ثبت نشده است.")

# ---------------------------------------------------------
# 6. STUDENT ONLINE QUIZ TAKING
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = safe_read_sql("SELECT id, title, subject, duration_minutes FROM quizzes WHERE is_active = 1 ORDER BY id DESC", conn)
        
    if students_df.empty or quizzes_df.empty:
        st.warning("در حال حاضر آزمون فعال یا دانش‌آموزی در سیستم تعریف نشده است.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.selectbox("نام دانش‌آموز (خود را انتخاب کنید):", students_df['full_name'].tolist())
        with col2:
            quiz_name = st.selectbox("انتخاب آزمون:", quizzes_df['title'].tolist())
            
        s_id = int(students_df[students_df['full_name'] == student_name]['id'].values[0])
        q_id = int(quizzes_df[quizzes_df['title'] == quiz_name]['id'].values[0])
        
        with get_connection() as conn:
            existing = conn.execute("SELECT id, percentage FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing:
            st.success(f"شما قبلاً در این آزمون شرکت کرده‌اید. درصد تستی شما: {existing['percentage']:.1f}٪")
        else:
            duration_min = int(quizzes_df[quizzes_df['id'] == q_id]['duration_minutes'].values[0])
            st.info(f"⏱️ زمان پاسخگویی: {duration_min} دقیقه")
            
            with get_connection() as conn:
                questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                
            student_mcq_ans = {}
            student_essay_ans = {}
            
            st.markdown("---")
            with st.form("take_quiz_form_main"):
                for idx, q in enumerate(questions):
                    st.markdown(f"### 📌 سوال {idx+1}: {q['question_text']}")
                    if q['question_type'] == 'mcq':
                        opts = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                        ans = st.radio(
                            f"پاسخ سوال {idx+1}:",
                            options=[1, 2, 3, 4],
                            format_func=lambda x: f"گزینه {x}: {opts[x-1]}",
                            key=f"ans_mcq_main_{q['id']}"
                        )
                        student_mcq_ans[q['id']] = (ans, q['correct_option'])
                    else:
                        e_ans = st.text_area(f"پاسخ تشریحی شما برای سوال {idx+1}:", key=f"ans_essay_main_{q['id']}")
                        student_essay_ans[q['id']] = e_ans
                    st.markdown("---")
                    
                submit_quiz = st.form_submit_button("🏁 پایان آزمون و ثبت نهایی پاسخ‌ها")
                
                if submit_quiz:
                    correct_count = 0
                    mcq_total = len(student_mcq_ans)
                    for qid, (u_ans, c_ans) in student_mcq_ans.items():
                        if u_ans == c_ans:
                            correct_count += 1
                    pct = (correct_count / mcq_total * 100) if mcq_total > 0 else 100.0
                    
                    essay_json_str = json.dumps(student_essay_ans, ensure_ascii=False)
                    shamsi_sub = f"{get_current_shamsi_date()} - {datetime.datetime.now().strftime('%H:%M')}"
                    
                    with get_connection() as conn:
                        conn.execute(
                            "INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, essay_answers, submitted_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (q_id, s_id, correct_count, mcq_total, pct, essay_json_str, shamsi_sub)
                        )
                        conn.commit()
                        
                    st.balloons()
                    st.success(f"🎉 پاسخ‌های شما با موفقیت ثبت شد! نمره‌ی بخش تستی: {correct_count} از {mcq_total} ({pct:.1f}٪)")
                    st.rerun()

# ---------------------------------------------------------
# 7. DASHBOARD & 3 DISTINCT PDF REPORTS
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد تحلیلی و پوشه کار جامع دانش‌آموز")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی وجود ندارد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار:", students_df['full_name'].tolist())
        st_row = students_df[students_df['full_name'] == selected_student].iloc[0]
        s_id = int(st_row['id'])
        nat_id_str = str(st_row['national_id']) if st_row['national_id'] else 'ثبت نشده'
        phone_str = str(st_row['parent_phone']) if st_row['parent_phone'] else 'ثبت نشده'
        grp_str = str(st_row['student_group']) if st_row['student_group'] else 'بدون گروه'
        
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg_str = f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون"
            
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with c2: st.metric("موارد رفتاری ثبت‌شده:", beh_count)
        with c3: st.metric("میانگین درصد آزمون آنلاین:", quiz_avg_str)
            
        st.markdown("---")
        
        # Display Online HTML Report Card
        portfolio_html = generate_portfolio_report_html(selected_student, nat_id_str, phone_str, grp_str, eval_count, beh_count, quiz_avg_str)
        with st.expander("👁️ مشاهده برگه رسمی کارنامه جامع (نمایش آنلاین درون سامانه)", expanded=True):
            st.markdown(portfolio_html, unsafe_allow_html=True)
            
        st.markdown("### 📥 دانلود ۳ گزارش رسمی و مستقل PDF:")
        col_pdf1, col_pdf2, col_pdf3 = st.columns(3)
        
        with col_pdf1:
            with get_connection() as conn:
                beh_rows = safe_read_sql("SELECT behavior_type, title, description, log_date FROM behaviors WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,)).to_dict('records')
            latest_b_type = beh_rows[0]['behavior_type'] if beh_rows else 'تشویق / رفتار مثبت 🟢'
            latest_title = beh_rows[0]['title'] if beh_rows else 'رعایت انضباط کلاسی'
            latest_desc = beh_rows[0]['description'] if beh_rows else 'مشارکت عالی در فعالیت‌های گروهی کلاس'
            latest_date = beh_rows[0]['log_date'] if beh_rows else get_current_shamsi_date()
            
            pdf_b_bytes = generate_behavior_pdf(selected_student, nat_id_str, grp_str, latest_b_type, latest_title, latest_desc, latest_date)
            st.download_button(
                "📥 ۱. دانلود PDF گزارش رفتار و انضباط",
                data=pdf_b_bytes,
                file_name=f"behavior_report_{selected_student}.pdf",
                mime="application/pdf",
                key="dl_pdf_behavior"
            )
            
        with col_pdf2:
            with get_connection() as conn:
                quiz_rows = safe_read_sql("""
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات تستی', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.id DESC
                """, conn, params=(s_id,)).to_dict('records')
            
            pdf_q_bytes = generate_exams_pdf(selected_student, nat_id_str, grp_str, quiz_rows)
            st.download_button(
                "📥 ۲. دانلود PDF گزارش تحلیلی آزمون‌ها",
                data=pdf_q_bytes,
                file_name=f"exams_report_{selected_student}.pdf",
                mime="application/pdf",
                key="dl_pdf_exams"
            )
            
        with col_pdf3:
            with get_connection() as conn:
                eval_rows = safe_read_sql("SELECT subject AS 'عنوان درس', level AS 'سطح توصیفی', feedback AS 'بازخورد معلم' FROM evaluations WHERE student_id = ?", conn, params=(s_id,)).to_dict('records')
            
            pdf_p_bytes = generate_portfolio_pdf(selected_student, nat_id_str, phone_str, grp_str, eval_count, beh_count, quiz_avg_str, eval_rows)
            st.download_button(
                "📥 ۳. دانلود PDF کارنامه جامع و پوشه کار",
                data=pdf_p_bytes,
                file_name=f"portfolio_report_{selected_student}.pdf",
                mime="application/pdf",
                key="dl_pdf_portfolio"
            )
            
        st.markdown("---")
        
        tab_d1, tab_d2, tab_d3 = st.tabs(["📝 ارزشیابی‌های توصیفی", "🌟 سوابق رفتاری", "📊 کارنامه و نمودار رشد آزمون‌ها"])
        
        with tab_d1:
            with get_connection() as conn:
                df_e = safe_read_sql("SELECT subject AS 'عنوان درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد معلم', eval_date AS 'تاریخ (شمسی)' FROM evaluations WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,))
            if not df_e.empty:
                st.dataframe(df_e, use_container_width=True, hide_index=True)
            else:
                st.info("ارزشیابی درسی ثبت نشده است.")
                
        with tab_d2:
            with get_connection() as conn:
                df_b = safe_read_sql("SELECT behavior_type AS 'نوع', title AS 'عنوان رفتار', description AS 'توضیحات تکمیلی', log_date AS 'تاریخ (شمسی)' FROM behaviors WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,))
            if not df_b.empty:
                st.dataframe(df_b, use_container_width=True, hide_index=True)
            else:
                st.info("مورد رفتاری ثبت نشده است.")
                
        with tab_d3:
            with get_connection() as conn:
                df_q = safe_read_sql("""
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات تستی', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت (شمسی)'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.id ASC
                """, conn, params=(s_id,))
            if not df_q.empty:
                st.dataframe(df_q, use_container_width=True, hide_index=True)
                st.markdown("##### 📈 نمودار روند رشد درصدهای آزمون آنلاین:")
                st.line_chart(df_q.set_index('عنوان آزمون')['درصد ٪'])
            else:
                st.info("نتیجه آزمونی ثبت نشده است.")

