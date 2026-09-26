
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
# Page Configuration & High-Contrast Dark Theme CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    html, body, [class*="st-"], .stMarkdown, p, span, button, input, select, textarea, label, h1, h2, h3, h4, h5, h6 {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stApp {
        background-color: #0f172a !important;
        color: #ffffff !important;
    }
    
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

    div[data-baseweb="popover"], div[data-baseweb="popover"] * {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    
    li[role="option"] {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }
    li[role="option"]:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }

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
</style>
""", unsafe_allow_html=True)

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
            pin_code TEXT DEFAULT '1234',
            parent_phone TEXT,
            student_group TEXT DEFAULT 'گروه ارمغان 🚀',
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
            level TEXT NOT NULL,
            feedback TEXT,
            eval_date TEXT,
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
            log_date TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
        """)
        
        # 4. Quizzes Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            duration_minutes INTEGER DEFAULT 60,
            is_active INTEGER DEFAULT 1,
            created_at TEXT
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
            submitted_at TEXT,
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
        
        # Schema Migrations
        columns_to_add = [
            ("students", "pin_code", "TEXT DEFAULT '1234'"),
            ("students", "student_group", "TEXT DEFAULT 'گروه ارمغان 🚀'"),
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
            except Exception:
                pass
                
        conn.commit()

init_db()

# Safe SQL Read Helper
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
# Seed Default 29 Students & Comprehensive Sample Quiz
# ---------------------------------------------------------
CLASS_GROUPS = [
    "گروه ارمغان 🚀",
    "گروه دانا 💡",
    "گروه تلاش 🌟",
    "گروه نخبگان 🏆",
    "گروه اندیشه 📖"
]

def seed_default_students():
    with get_connection() as conn:
        cursor = conn.cursor()
        count = cursor.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if count == 0:
            students = [
                ("آرمین", "احمدی", "1001", "09181111101", "گروه ارمغان 🚀"),
                ("احسان", "ابراهیمی", "1002", "09181111102", "گروه ارمغان 🚀"),
                ("امیررضا", "اسدی", "1003", "09181111103", "گروه ارمغان 🚀"),
                ("بنیامين", "بابایی", "1004", "09181111104", "گروه ارمغان 🚀"),
                ("پارسـا", "پیرانی", "1005", "09181111105", "گروه ارمغان 🚀"),
                ("پوریا", "تقی‌پور", "1006", "09181111106", "گروه ارمغان 🚀"),
                ("جواد", "جعفری", "1007", "09181111107", "گروه دانا 💡"),
                ("حسام", "حسینی", "1008", "09181111108", "گروه دانا 💡"),
                ("دانیال", "داوودی", "1009", "09181111109", "گروه دانا 💡"),
                ("رضا", "رحیمی", "1010", "09181111110", "گروه دانا 💡"),
                ("سینا", "سلیمانی", "1011", "09181111111", "گروه دانا 💡"),
                ("شایان", "شریفی", "1012", "09181111112", "گروه دانا 💡"),
                ("علی", "عباسی", "1013", "09181111113", "گروه تلاش 🌟"),
                ("کیان", "ابراهیمی", "1014", "09181111114", "گروه تلاش 🌟"),
                ("محمد", "محمدی", "1015", "09181111115", "گروه تلاش 🌟"),
                ("مهدی", "مرادی", "1016", "09181111116", "گروه تلاش 🌟"),
                ("نیما", "نوروزی", "1017", "09181111117", "گروه تلاش 🌟"),
                ("یاسین", "یاسینی", "1018", "09181111118", "گروه تلاش 🌟"),
                ("ابوالفضل", "صادقی", "1019", "09181111119", "گروه نخبگان 🏆"),
                ("امیرعلی", "رضایی", "1020", "09181111120", "گروه نخبگان 🏆"),
                ("حسین", "کریم‌زاده", "1021", "09181111121", "گروه نخبگان 🏆"),
                ("سبحان", "قاسمی", "1022", "09181111122", "گروه نخبگان 🏆"),
                ("سهیل", "نجفی", "1023", "09181111123", "گروه نخبگان 🏆"),
                ("متین", "موسوی", "1024", "09181111124", "گروه نخبگان 🏆"),
                ("ارشیا", "خسروی", "1025", "09181111125", "گروه اندیشه 📖"),
                ("ایلیا", "اکبری", "1026", "09181111126", "گروه اندیشه 📖"),
                ("باربد", "حاتمی", "1027", "09181111127", "گروه اندیشه 📖"),
                ("پرهام", "یزدانی", "1028", "09181111128", "گروه اندیشه 📖"),
                ("سامان", "فرهادی", "1029", "09181111129", "گروه اندیشه 📖")
            ]
            shamsi_today = get_current_shamsi_date()
            for fn, ln, nid, ph, grp in students:
                cursor.execute(
                    "INSERT INTO students (first_name, last_name, national_id, pin_code, parent_phone, student_group, created_at) VALUES (?, ?, ?, '1234', ?, ?, ?)",
                    (fn, ln, nid, ph, grp, shamsi_today)
                )
            conn.commit()

seed_default_students()

def seed_default_quiz():
    with get_connection() as conn:
        cursor = conn.cursor()
        count = cursor.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]
        if count == 0:
            shamsi_today = get_current_shamsi_date()
            cursor.execute(
                "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                ("آزمونک جامع فصل اول ریاضی و علوم پنجم", "ریاضی", 60, shamsi_today)
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

def load_students():
    with get_connection() as conn:
        df = safe_read_sql("SELECT id, first_name, last_name, first_name || ' ' || last_name AS full_name, national_id, parent_phone, student_group, notes, pin_code FROM students ORDER BY last_name, first_name", conn)
    return df

def check_teacher_password(pwd):
    with get_connection() as conn:
        res = conn.execute("SELECT password FROM teacher_auth WHERE id = 1").fetchone()
        return res['password'] == pwd if res else pwd == '1234' or pwd == 'مطهری'

def update_teacher_password(new_pwd):
    with get_connection() as conn:
        conn.execute("UPDATE teacher_auth SET password = ? WHERE id = 1", (new_pwd,))
        conn.commit()

# Session State Setup
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = 'دانش‌آموز'
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False
if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 0
if 'show_welcome_page' not in st.session_state:
    st.session_state['show_welcome_page'] = True

# ---------------------------------------------------------
# Pure Python Reshaper Helper for ReportLab PDF Printing
# ---------------------------------------------------------
def _rtl_text(text):
    if not text:
        return ""
    text_str = str(text).strip()
    words = text_str.split(" ")
    reversed_words = [w[::-1] for w in reversed(words)]
    return " ".join(reversed_words)

# ---------------------------------------------------------
# PDF Generators (ReportLab with Fallbacks)
# ---------------------------------------------------------
@st.cache_data
def generate_behavior_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib import colors
        
        font_path = "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"
        font_name = "Helvetica"
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
                font_name = 'ArabicFont'
            except Exception:
                pass
                
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        
        is_pos = 'مثبت' in b_type or 'تشویق' in b_type
        header_color = colors.HexColor('#15803d') if is_pos else colors.HexColor('#b91c1c')
        
        c.setFillColor(header_color)
        c.rect(0, h-90, w, 90, fill=1, stroke=0)
        
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(font_name, 14)
        c.drawCentredString(w/2, h-35, _rtl_text('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
        c.setFont(font_name, 11)
        c.drawCentredString(w/2, h-55, _rtl_text('دبستان پسرانه شهید مطهری مهران - پایه پنجم'))
        c.setFont(font_name, 13)
        doc_title = 'تقدیرنامه و لوح سپاس انضباطی' if is_pos else 'کارت اطلاع‌رسانی و هشدار انضباطی'
        c.drawCentredString(w/2, h-78, _rtl_text(doc_title))
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 11)
        y = h - 130
        c.drawRightString(w - 40, y, _rtl_text(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 220, y, _rtl_text(f'کد ملی: {national_id}'))
        c.drawRightString(w - 380, y, _rtl_text(f'گروه کلاسی: {student_group}'))
        
        y -= 40
        c.drawRightString(w - 40, y, _rtl_text(f'نوع مشاهده: {b_type}'))
        c.drawRightString(w - 220, y, _rtl_text(f'عنوان رفتار: {title}'))
        c.drawRightString(w - 380, y, _rtl_text(f'تاریخ ثبت: {log_date}'))
        
        y -= 60
        c.setFillColor(colors.HexColor('#f8fafc'))
        c.rect(40, y-100, w-80, 100, fill=1, stroke=1)
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 11)
        c.drawRightString(w - 55, y - 25, _rtl_text('📌 توضیحات و اقدامات انجام‌شده توسط آموزگار:'))
        c.setFont(font_name, 10)
        c.drawRightString(w - 55, y - 55, _rtl_text(str(desc)[:80]))
        
        y -= 160
        c.setFont(font_name, 11)
        c.drawRightString(w - 80, y, _rtl_text('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 40, y, _rtl_text('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl_text('رویت و امضای اولیاء'))
        
        c.save()
        return buf.getvalue()
    except Exception:
        return f"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>endobj trailer<</Root 1 0 R>>\n%%EOF".encode('utf-8')

@st.cache_data
def generate_exams_pdf(student_name, national_id, student_group, quiz_count, quiz_avg_str):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib import colors
        
        font_path = "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"
        font_name = "Helvetica"
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
                font_name = 'ArabicFont'
            except Exception:
                pass
                
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        
        c.setFillColor(colors.HexColor('#0284c7'))
        c.rect(0, h-90, w, 90, fill=1, stroke=0)
        
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(font_name, 14)
        c.drawCentredString(w/2, h-35, _rtl_text('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
        c.setFont(font_name, 11)
        c.drawCentredString(w/2, h-55, _rtl_text('دبستان پسرانه شهید مطهری مهران - پایه پنجم'))
        c.setFont(font_name, 13)
        c.drawCentredString(w/2, h-78, _rtl_text('گزارش تحلیلی نمرات و آزمون‌های آنلاین'))
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 11)
        y = h - 130
        c.drawRightString(w - 40, y, _rtl_text(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 220, y, _rtl_text(f'کد ملی: {national_id}'))
        c.drawRightString(w - 380, y, _rtl_text(f'گروه کلاسی: {student_group}'))
        
        y -= 50
        c.setFillColor(colors.HexColor('#f1f5f9'))
        c.rect(40, y-60, w-80, 60, fill=1, stroke=1)
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 11)
        c.drawRightString(w - 60, y - 35, _rtl_text(f'تعداد آزمون‌های شرکت کرده: {quiz_count}'))
        c.drawRightString(w - 300, y - 35, _rtl_text(f'میانگین درصد آزمون‌های آنلاین: {quiz_avg_str}'))
        
        y -= 140
        c.setFont(font_name, 11)
        c.drawRightString(w - 80, y, _rtl_text('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 40, y, _rtl_text('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl_text('امضا و تاریخ'))
        
        c.save()
        return buf.getvalue()
    except Exception:
        return f"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>endobj trailer<</Root 1 0 R>>\n%%EOF".encode('utf-8')

@st.cache_data
def generate_portfolio_pdf(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib import colors
        
        font_path = "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"
        font_name = "Helvetica"
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
                font_name = 'ArabicFont'
            except Exception:
                pass
                
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.rect(0, h-90, w, 90, fill=1, stroke=0)
        
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(font_name, 14)
        c.drawCentredString(w/2, h-35, _rtl_text('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
        c.setFont(font_name, 11)
        c.drawCentredString(w/2, h-55, _rtl_text('دبستان پسرانه شهید مطهری مهران - پایه پنجم'))
        c.setFont(font_name, 13)
        c.drawCentredString(w/2, h-78, _rtl_text('کارنامه جامع تحصیلی و پوشه کار دیجیتال'))
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 11)
        y = h - 130
        c.drawRightString(w - 40, y, _rtl_text(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 220, y, _rtl_text(f'کد ملی: {national_id}'))
        c.drawRightString(w - 380, y, _rtl_text(f'گروه کلاسی: {student_group}'))
        
        y -= 50
        c.setFillColor(colors.HexColor('#f1f5f9'))
        c.rect(40, y-60, w-80, 60, fill=1, stroke=1)
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 11)
        c.drawRightString(w - 60, y - 35, _rtl_text(f'تعداد ارزشیابی‌ها: {eval_count}'))
        c.drawRightString(w - 240, y - 35, _rtl_text(f'موارد رفتاری: {beh_count}'))
        c.drawRightString(w - 420, y - 35, _rtl_text(f'میانگین آزمون‌ها: {quiz_avg_str}'))
        
        y -= 100
        c.setFillColor(colors.HexColor('#eff6ff'))
        c.rect(40, y-100, w-80, 100, fill=1, stroke=1)
        
        c.setFillColor(colors.HexColor('#1e40af'))
        c.setFont(font_name, 12)
        c.drawRightString(w - 55, y - 25, _rtl_text('💡 تحلیل آموزشی و توصیه‌های تربیتی آموزگار:'))
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10)
        c.drawRightString(w - 55, y - 55, _rtl_text('۱. نقاط قوت: حضور منظم، مشارکت فعال در فعالیت‌های گروهی کلاسی.'))
        c.drawRightString(w - 55, y - 80, _rtl_text('۲. توصیه به اولیا: تمرین مستمر مفاهیم ریاضی و علوم در منزل.'))
        
        y -= 160
        c.setFont(font_name, 11)
        c.drawRightString(w - 80, y, _rtl_text('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 40, y, _rtl_text('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl_text('رویت و امضای اولیاء'))
        
        c.save()
        return buf.getvalue()
    except Exception:
        return f"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>endobj trailer<</Root 1 0 R>>\n%%EOF".encode('utf-8')

# ---------------------------------------------------------
# WELCOME SPLASH PAGE (صفحه ورودی و معرفی برنامه)
# ---------------------------------------------------------
if st.session_state['show_welcome_page']:
    curr_shamsi = get_current_shamsi_date()
    st.markdown(f"""
    <div class="main-header">
        <h1>🌸 به سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی خوش آمدید 🌸</h1>
        <p style="font-size: 1.2rem; font-weight: bold; margin-top: 10px;">🏫 دبستان شهید مطهری مهران — سال تحصیلی ۱۴۰۴-۱۴۰۵ | 📅 تاریخ امروز: <b>{curr_shamsi}</b></p>
        <p style="font-size: 1.1rem; opacity: 0.9;">طراح و آموزگار پایه پنجم: <b>سید موسی حیدری</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
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
    
    if st.button("🚀 ورود به سامانه مدیریت کلاس و آزمون آنلاین", use_container_width=True):
        st.session_state['show_welcome_page'] = False
        st.rerun()
        
    st.stop()

# ---------------------------------------------------------
# TOP APP HEADER & TEACHER LOGIN BAR
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
                if check_teacher_password(pass_input):
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
                    if check_teacher_password(old_p):
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
# STABLE & FAST DROPDOWN MENU
# ---------------------------------------------------------
if st.session_state['is_teacher_logged_in']:
    MENU_OPTIONS = [
        "1️⃣ 🏠 معرفی سامانه و اهداف آموزشی",
        "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی (۲۹ نفر)",
        "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی",
        "4️⃣ 🌟 مدیریت رفتار و مشاهدات انضباطی",
        "5️⃣ ✏️ آزمون‌ساز آنلاین و طراحی سوالات",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع"
    ]
else:
    MENU_OPTIONS = [
        "1️⃣ 🏠 معرفی سامانه و اهداف آموزشی",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع"
    ]

st.markdown("""
<div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 14px; border-radius: 12px; border: 2px solid #3b82f6; margin-bottom: 18px;">
    <h3 style="color: #60a5fa !important; margin: 0; font-size: 1.15rem;">📌 منوی دسترسی و انتقال بین بخش‌های سامانه:</h3>
</div>
""", unsafe_allow_html=True)

menu_choice = st.selectbox(
    "انتخاب بخش مورد نظر:",
    MENU_OPTIONS,
    index=0,
    key="main_stable_dropdown_menu",
    label_visibility="collapsed"
)

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
        <p>ثبت دقیق سطح عملکرد توصیفی دانش‌آموزان همراه با بازخوردهای اصلاحی جهت ارائه به اولیا.</p>
    </div>
    
    <div class="card-box">
        <h4>2️⃣ آزمون‌ساز آنلاین با امکان بارگذاری اکسل، کپی-پیست متن و دستی</h4>
        <p>طراحی آزمون، تعیین زمان معکوس (مثلاً ۶۰ دقیقه)، تصحیح خودکار بخش تستی و ارائه تحلیل آموزشی.</p>
    </div>
    
    <div class="card-box">
        <h4>3️⃣ مدیریت ۲۹ دانش‌آموز در ۵ گروه متوازن</h4>
        <p>دسته‌بندی دانش‌آموزان در ۵ گروه آموزشی و قابلیت بارگذاری دسته‌جمعی اسامی از فایل اکسل.</p>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------
# 2. STUDENT PROFILES & BULK EXCEL UPLOAD (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab1, tab2, tab3, tab_del = st.tabs([
        "📋 لیست دانش‌آموزان و گروه‌ها", 
        "📊 ثبت دسته‌جمعی و سریع از اکسل", 
        "➕ ثبت دانش‌آموز جدید (تکی)",
        "🗑️ مدیریت و حذف پرونده"
    ])
    
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
                
            display_df = filtered_df[['id', 'first_name', 'last_name', 'full_name', 'national_id', 'parent_phone', 'student_group']].copy()
            display_df = display_df.rename(columns={
                'id': 'شناسه',
                'first_name': 'نام',
                'last_name': 'نام خانوادگی',
                'full_name': 'نام و نام خانوادگی',
                'national_id': 'کد ملی',
                'parent_phone': 'شماره همراه اولیا',
                'student_group': 'گروه کلاسی'
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            st.info(f"📊 تعداد کل دانش‌آموزان پیدا شده: {len(filtered_df)} نفر")
        else:
            st.info("هنوز هیچ دانش‌آموزی ثبت نشده است.")

    with tab2:
        st.subheader("📊 بارگذاری دسته‌جمعی اسامی دانش‌آموزان از فایل اکسل (Excel / CSV)")
        st.info("💡 فایل اکسل شما باید حداقل شامل ستون‌های 'نام' (first_name) و 'نام خانوادگی' (last_name) باشد.")
        
        sample_data = pd.DataFrame({
            'first_name': ['علی', 'محمد'],
            'last_name': ['حیدری', 'رضایی'],
            'national_id': ['1001', '1002'],
            'parent_phone': ['09181112233', '09184445566'],
            'student_group': ['گروه ارمغان 🚀', 'گروه دانا 💡']
        })
        st.download_button(
            "📥 دانلود نمونه فایل الگوی اکسل (CSV)",
            sample_data.to_csv(index=False).encode('utf-8-sig'),
            "student_template.csv",
            "text/csv"
        )
        
        col_ex1, col_ex2 = st.columns([3, 1])
        with col_ex1:
            uploaded_file = st.file_uploader("فایل Excel یا CSV دانش‌آموزان را انتخاب کنید:", type=["xlsx", "xls", "csv"], key=f"excel_file_{st.session_state['excel_upload_key']}")
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
                
                if st.button("🚀 افزودن همگی به دیتابیس کلاس"):
                    shamsi_today = get_current_shamsi_date()
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        success_count = 0
                        for idx, row in df_upload.iterrows():
                            fn = str(row.get('first_name', row.get('نام', ''))).strip()
                            ln = str(row.get('last_name', row.get('نام خانوادگی', ''))).strip()
                            nid = str(row.get('national_id', row.get('کد ملی', f'100{idx+1}'))).strip()
                            phone = str(row.get('parent_phone', row.get('شماره اولیا', ''))).strip()
                            grp = str(row.get('student_group', row.get('گروه', CLASS_GROUPS[idx % 5]))).strip()
                            
                            if fn and ln:
                                try:
                                    cursor.execute(
                                        "INSERT INTO students (first_name, last_name, national_id, pin_code, parent_phone, student_group, created_at) VALUES (?, ?, ?, '1234', ?, ?, ?)",
                                        (fn, ln, nid, phone, grp, shamsi_today)
                                    )
                                    success_count += 1
                                except Exception:
                                    pass
                        conn.commit()
                    st.success(f"🎉 تعداد {success_count} دانش‌آموز با موفقیت وارد دیتابیس شدند.")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ خطا در خواندن فایل: {e}")

    with tab3:
        st.subheader("➕ ثبت دانش‌آموز جدید (تکی)")
        with st.form("add_single_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                fn = st.text_input("نام:*")
                nid = st.text_input("کد ملی دانش‌آموز:")
                grp = st.selectbox("گروه آموزشی کلاسی:", CLASS_GROUPS)
            with col2:
                ln = st.text_input("نام خانوادگی:*")
                pin = st.text_input("رمز ۴ رقمی اختصاصی دانش‌آموز:", value="1234")
                phone = st.text_input("شماره همراه اولیا:")
            notes = st.text_area("توضیحات تکمیلی:")
            
            if st.form_submit_button("💾 ثبت پرونده دانش‌آموز"):
                if fn.strip() and ln.strip():
                    shamsi_today = get_current_shamsi_date()
                    with get_connection() as conn:
                        try:
                            conn.execute(
                                "INSERT INTO students (first_name, last_name, national_id, pin_code, parent_phone, student_group, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (fn.strip(), ln.strip(), nid.strip(), pin.strip(), phone.strip(), grp, notes.strip(), shamsi_today)
                            )
                            conn.commit()
                            st.success(f"دانش‌آموز {fn} {ln} با موفقیت ثبت شد.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("❌ کد ملی وارد شده تکراری است.")
                else:
                    st.warning("لطفاً نام و نام خانوادگی را وارد نمایید.")

    with tab_del:
        st.subheader("🗑️ مدیریت و حذف پرونده دانش‌آموزان")
        students_df = load_students()
        if not students_df.empty:
            student_options = [f"{row['id']} - {row['first_name']} {row['last_name']} (کد ملی: {row['national_id']})" for _, row in students_df.iterrows()]
            selected_st_del = st.selectbox("انتخاب دانش‌آموز جهت حذف پرونده:", student_options, key="del_st_select")
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("🗑️ حذف پرونده این دانش‌آموز"):
                    st_id = int(selected_st_del.split(" - ")[0])
                    with get_connection() as conn:
                        conn.execute("DELETE FROM students WHERE id = ?", (st_id,))
                        conn.commit()
                    st.success("پرونده دانش‌آموز با موفقیت حذف شد.")
                    st.rerun()
                    
            st.markdown("---")
            st.write("⚠️ **پاکسازی دسته‌جمعی دیتابیس کلاس:**")
            confirm_del_all = st.checkbox("تایید می‌کنم که تمام اسامی دانش‌آموزان پاکسازی شوند.")
            if st.button("🔥 پاکسازی کامل لیست دانش‌آموزان"):
                if confirm_del_all:
                    with get_connection() as conn:
                        conn.execute("DELETE FROM students")
                        conn.commit()
                    st.success("تمامی پرونده‌های دانش‌آموزان پاکسازی گردید.")
                    st.rerun()
                else:
                    st.error("لطفاً تیک تایید پاکسازی را بزنید.")

# ---------------------------------------------------------
# 3. QUALITATIVE EVALUATIONS (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی (پایه پنجم)")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("لطفاً ابتدا اسامی دانش‌آموزان را ثبت کنید.")
    else:
        student_options = [f"{row['id']} - {row['first_name']} {row['last_name']} (گروه: {row['student_group']})" for _, row in students_df.iterrows()]
        selected_st_str = st.selectbox("انتخاب دانش‌آموز:", student_options, key="eval_st_select")
        s_id = int(selected_st_str.split(" - ")[0])
        
        col1, col2 = st.columns(2)
        with col1:
            selected_subject = st.selectbox("انتخاب درس:", FIFTH_GRADE_SUBJECTS)
            selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
        with col2:
            eval_date = st.text_input("تاریخ ارزشیابی (شمسی):", value=get_current_shamsi_date())
            feedback_text = st.text_area("توصیف عملکرد و بازخورد آموزگار:")
            
        if st.button("💾 ثبت ارزشیابی توصیفی"):
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text.strip(), eval_date.strip())
                )
                conn.commit()
            st.success(f"ارزشیابی درس {selected_subject} ثبت گردید.")
            st.rerun()
            
        st.markdown("---")
        st.subheader("📋 سوابق ارزشیابی‌های ثبت‌شده:")
        with get_connection() as conn:
            eval_h = safe_read_sql("""
                SELECT id AS 'شناسه', subject AS 'عنوان درس', level AS 'سطح توصیفی', feedback AS 'بازخورد آموزگار', eval_date AS 'تاریخ'
                FROM evaluations WHERE student_id = ? ORDER BY id DESC
            """, conn, params=(s_id,))
        if not eval_h.empty:
            st.dataframe(eval_h, use_container_width=True, hide_index=True)
            
            with st.expander("🗑️ حذف رکورد ارزشیابی خاص"):
                eval_ids = eval_h['شناسه'].tolist()
                del_eval_id = st.selectbox("شناسه ارزشیابی جهت حذف:", eval_ids, key="del_eval_id")
                if st.button("حذف این ارزشیابی"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM evaluations WHERE id = ?", (del_eval_id,))
                        conn.commit()
                    st.success("ارزشیابی با موفقیت حذف شد.")
                    st.rerun()
        else:
            st.info("ارزشیابی درسی ثبت نشده است.")

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
        student_options = [f"{row['id']} - {row['first_name']} {row['last_name']} (گروه: {row['student_group']})" for _, row in students_df.iterrows()]
        selected_st_str = st.selectbox("انتخاب دانش‌آموز:", student_options, key="beh_st_select")
        s_id = int(selected_st_str.split(" - ")[0])
        
        col1, col2 = st.columns(2)
        with col1:
            b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
            title = st.text_input("عنوان رفتار:")
        with col2:
            log_date = st.text_input("تاریخ ثبت (شمسی):", value=get_current_shamsi_date())
            desc = st.text_area("جزییات و توضیحات آموزگار:")
            
        if st.button("💾 ثبت مشاهده رفتاری"):
            if title.strip():
                with get_connection() as conn:
                    conn.execute(
                        "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                        (s_id, b_type, title.strip(), desc.strip(), log_date.strip())
                    )
                    conn.commit()
                st.success("مشاهده رفتاری با موفقیت ذخیره گردید.")
                st.rerun()
            else:
                st.error("لطفاً عنوان رفتار را وارد کنید.")
                
        st.markdown("---")
        st.subheader("📋 سوابق رفتاری ثبت‌شده:")
        with get_connection() as conn:
            beh_h = safe_read_sql("""
                SELECT id AS 'شناسه', behavior_type AS 'نوع', title AS 'عنوان رفتار', description AS 'توضیحات', log_date AS 'تاریخ'
                FROM behaviors WHERE student_id = ? ORDER BY id DESC
            """, conn, params=(s_id,))
        if not beh_h.empty:
            st.dataframe(beh_h, use_container_width=True, hide_index=True)
            
            with st.expander("🗑️ حذف رکورد رفتاری"):
                beh_ids = beh_h['شناسه'].tolist()
                del_beh_id = st.selectbox("شناسه رفتار جهت حذف:", beh_ids, key="del_beh_id")
                if st.button("حذف این مورد رفتاری"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM behaviors WHERE id = ?", (del_beh_id,))
                        conn.commit()
                    st.success("مورد رفتاری حذف گردید.")
                    st.rerun()
        else:
            st.info("مورد رفتاری ثبت نشده است.")

# ---------------------------------------------------------
# 5. ONLINE QUIZ CREATOR (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (طراحی و انتشار آزمون)")
    
    tab_q1, tab_q_excel, tab_q_text, tab_q_json, tab_q_manage = st.tabs([
        "➕ طراحی دستی آزمون", 
        "📊 بارگذاری از فایل اکسل (Excel/CSV)", 
        "📋 کپی-پیست متن یکجا", 
        "📥 فایل JSON",
        "🗑️ مدیریت و حذف آزمون‌ها"
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
                st.rerun()
            else:
                st.error("عنوان و متن تمام سوالات را تکمیل کنید.")

    with tab_q_excel:
        st.subheader("📊 بارگذاری سوالات از فایل اکسل (Excel / CSV)")
        c_ex1, c_ex2, c_ex3 = st.columns(3)
        with c_ex1: ex_title = st.text_input("عنوان آزمون جدید (از اکسل):", key="ex_q_title")
        with c_ex2: ex_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="ex_q_sub")
        with c_ex3: ex_duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=180, value=45, key="ex_q_dur")
        
        uploaded_excel = st.file_uploader("فایل اکسل (xlsx) یا (csv) را انتخاب کنید:", type=["xlsx", "xls", "csv"], key="quiz_excel_file")
        if uploaded_excel is not None:
            try:
                if uploaded_excel.name.endswith(".csv"):
                    df_q = pd.read_csv(uploaded_excel)
                else:
                    df_q = pd.read_excel(uploaded_excel)
                    
                st.success(f"فایل با موفقیت خوانده شد ({len(df_q)} سوال پیدا شد).")
                st.dataframe(df_q, use_container_width=True)
                
                if st.button("🚀 ایجاد و فعال‌سازی آزمون از اکسل", key="btn_create_ex"):
                    if ex_title.strip():
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
                                corr = int(row.get('گزینه صحیح', 1))
                                exp = str(row.get('پاسخ تشریحی', row.get('تحلیل', ''))).strip()
                                
                                if q_txt:
                                    cursor.execute("""
                                        INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                        VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (qid, q_txt, o1, o2, o3, o4, corr, None, exp if exp else None))
                                    cnt += 1
                            conn.commit()
                        st.success(f"🎉 آزمون '{ex_title}' با {cnt} سوال ساخته شد.")
                        st.rerun()
            except Exception as e:
                st.error(f"خطا در بارگذاری اکسل: {e}")

    with tab_q_text:
        st.subheader("📋 ورود یکجای سوالات با کپی-پیست متن")
        c_tx1, c_tx2, c_tx3 = st.columns(3)
        with c_tx1: tx_title = st.text_input("عنوان آزمون متنی:", key="tx_title")
        with c_tx2: tx_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="tx_sub")
        with c_tx3: tx_duration = st.number_input("زمان (دقیقه):", min_value=5, max_value=180, value=30, key="tx_dur")
        
        sample_text_format = "سوال ۱: حاصل عبارت ۳/۵ + ۱/۱۰ کدام است؟ | گزینه ۱: ۷/۱۰ | گزینه ۲: ۴/۱۰ | گزینه ۳: ۵/۱۰ | گزینه ۴: ۳/۱۰ | پاسخ صحیح: ۱\nسوال ۲: کدام یک تغییر شیمیایی است؟ | گزینه ۱: ذوب یخ | گزینه ۲: تبخیر آب | گزینه ۳: سوختن چوب | گزینه ۴: خرد کردن کاغذ | پاسخ صحیح: ۳"
        pasted_text = st.text_area("متن سوالات را کپی-پیست کنید (هر سوال در یک سطر با کاراکتر | ):", value=sample_text_format, height=160)
        
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
                        o1 = parts[1] if len(parts) > 1 else ""
                        o2 = parts[2] if len(parts) > 2 else ""
                        o3 = parts[3] if len(parts) > 3 else ""
                        o4 = parts[4] if len(parts) > 4 else ""
                        corr = 1
                        if len(parts) > 5:
                            try: corr = int(re.sub(r'\D', '', parts[5]))
                            except Exception: corr = 1
                        
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                            VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (qid, q_txt, o1, o2, o3, o4, corr, None, None))
                        cnt += 1
                    conn.commit()
                st.success(f"آزمون با {cnt} سوال ساخته شد.")
                st.rerun()

    with tab_q_json:
        st.subheader("📥 بارگذاری فایل آزمون (JSON)")
        uploaded_json = st.file_uploader("فایل JSON آزمون را انتخاب کنید:", type=["json"])
        if uploaded_json is not None:
            try:
                data = json.load(uploaded_json)
                st.write(f"<b>عنوان:</b> {data.get('title')}", unsafe_allow_html=True)
                if st.button("🚀 ایجاد آزمون از JSON"):
                    shamsi_today = get_current_shamsi_date()
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                            (data.get('title', 'آزمون آنلاین'), data.get('subject', 'ریاضی'), data.get('duration_minutes', 60), shamsi_today)
                        )
                        qid = cursor.lastrowid
                        for q in data.get('questions', []):
                            cursor.execute("""
                                INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (qid, q.get('question_type', 'mcq'), q.get('question_text', ''), q.get('option_1', ''), q.get('option_2', ''), q.get('option_3', ''), q.get('option_4', ''), q.get('correct_option', 1), q.get('model_answer', ''), q.get('explanation', '')))
                        conn.commit()
                    st.success("آزمون با موفقیت بارگذاری شد.")
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در فایل JSON: {e}")

    with tab_q_manage:
        st.subheader("🗑️ مدیریت و حذف آزمون‌ها")
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id AS 'شناسه', title AS 'عنوان آزمون', subject AS 'درس', duration_minutes AS 'زمان', is_active AS 'وضعیت' FROM quizzes ORDER BY id DESC", conn)
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True, hide_index=True)
            
            q_ids = quizzes_df['شناسه'].tolist()
            del_q_id = st.selectbox("انتخاب آزمون جهت حذف کامل:", q_ids, key="del_q_id")
            if st.button("🗑️ حذف کامل آزمون انتخاب‌شده"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM quizzes WHERE id = ?", (del_q_id,))
                    conn.commit()
                st.success("آزمون و تمام نتایج مرتبط با آن حذف گردید.")
                st.rerun()
        else:
            st.info("هیچ آزمونی ثبت نشده است.")

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
        student_options = [f"{row['id']} - {row['first_name']} {row['last_name']} (کد ملی: {row['national_id']})" for _, row in students_df.iterrows()]
        quiz_options = [f"{row['id']} - {row['title']} ({row['subject']} - {row['duration_minutes']} دقیقه)" for _, row in quizzes_df.iterrows()]
        
        col1, col2 = st.columns(2)
        with col1:
            selected_st_str = st.selectbox("نام دانش‌آموز (خود را انتخاب کنید):", student_options, key="quiz_st_select")
        with col2:
            selected_q_str = st.selectbox("انتخاب آزمون آنلاین:", quiz_options, key="quiz_q_select")
            
        s_id = int(selected_st_str.split(" - ")[0])
        q_id = int(selected_q_str.split(" - ")[0])
        
        with get_connection() as conn:
            existing = conn.execute("SELECT id, percentage FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing:
            st.success(f"شما قبلاً در این آزمون شرکت کرده‌اید. درصد نمره تستی شما: {existing['percentage']:.1f}٪")
        else:
            q_info = quizzes_df[quizzes_df['id'] == q_id].iloc[0]
            st.info(f"⏱️ **زمان تعیین‌شده برای پاسخ‌گویی: {q_info['duration_minutes']} دقیقه می‌باشد.**")
            
            with get_connection() as conn:
                questions = safe_read_sql("SELECT * FROM questions WHERE quiz_id = ? ORDER BY id ASC", conn, params=(q_id,))
                
            student_mcq_ans = {}
            student_essay_ans = {}
            
            st.markdown("---")
            with st.form("take_quiz_form"):
                for idx, q in questions.iterrows():
                    st.markdown(f"### 📌 سوال {idx+1}: {q['question_text']}")
                    if q['question_type'] == 'mcq':
                        opts = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                        ans = st.radio(
                            f"پاسخ سوال {idx+1}:",
                            options=[1, 2, 3, 4],
                            format_func=lambda x: f"گزینه {x}: {opts[x-1]}",
                            key=f"ans_mcq_{q['id']}"
                        )
                        student_mcq_ans[q['id']] = (ans, q['correct_option'])
                    else:
                        e_ans = st.text_area(f"پاسخ تشریحی شما برای سوال {idx+1}:", key=f"ans_essay_{q['id']}")
                        student_essay_ans[q['id']] = e_ans
                    st.markdown("---")
                    
                st.markdown("##### 📸 ثبت تصویر چهره دانش‌آموز جهت احراز هویت:")
                photo = st.camera_input("ثبت تصویر چهره دانش‌آموز", key=f"cam_{s_id}_{q_id}")
                
                submit_quiz = st.form_submit_button("🏁 پایان آزمون و ثبت نهایی پاسخ‌ها")
                
                if submit_quiz:
                    photo_data_str = ""
                    if photo is not None:
                        bytes_data = photo.getvalue()
                        photo_data_str = "data:image/png;base64," + base64.b64encode(bytes_data).decode('utf-8')
                        
                    correct_count = 0
                    mcq_total = len(student_mcq_ans)
                    for qid, (u_ans, c_ans) in student_mcq_ans.items():
                        if u_ans == c_ans:
                            correct_count += 1
                    pct = (correct_count / mcq_total * 100) if mcq_total > 0 else 100.0
                    
                    essay_json_str = json.dumps(student_essay_ans, ensure_ascii=False)
                    shamsi_submitted = f"{get_current_shamsi_date()} - {datetime.datetime.now().strftime('%H:%M')}"
                    
                    with get_connection() as conn:
                        conn.execute(
                            "INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, photo_data, essay_answers, submitted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (q_id, s_id, correct_count, mcq_total, pct, photo_data_str, essay_json_str, shamsi_submitted)
                        )
                        conn.commit()
                        
                    st.balloons()
                    st.success(f"🎉 پاسخ‌های شما با موفقیت ثبت گردید! نمره‌ی بخش تستی: {correct_count} از {mcq_total} ({pct:.1f}٪)")

# ---------------------------------------------------------
# 7. DASHBOARD & STUDENT PORTFOLIO (3 SEPARATE PDF REPORTS)
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد تحلیلی و کارنامه جامع دانش‌آموز")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی وجود ندارد.")
    else:
        student_options = [f"{row['id']} - {row['first_name']} {row['last_name']} (کد ملی: {row['national_id']} | گروه: {row['student_group']})" for _, row in students_df.iterrows()]
        selected_st_str = st.selectbox("انتخاب دانش‌آموز جهت مشاهده کارنامه و گزارش‌ها:", student_options, key="portfolio_st_select")
        s_id = int(selected_st_str.split(" - ")[0])
        
        st_info = students_df[students_df['id'] == s_id].iloc[0]
        st_name = f"{st_info['first_name']} {st_info['last_name']}"
        st_nid = str(st_info['national_id'])
        st_phone = str(st_info['parent_phone'])
        st_grp = str(st_info['student_group'])
        
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_res = conn.execute("SELECT COUNT(*), AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()
            quiz_count = quiz_res[0]
            quiz_avg = quiz_res[1]
            quiz_avg_str = f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون"
            
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("ارزشیابی‌های درسی:", eval_count)
        with c2: st.metric("مشاهدات رفتاری:", beh_count)
        with c3: st.metric("میانگین آزمون آنلاین:", quiz_avg_str)
        
        st.markdown("---")
        
        # 📄 3 DISTINCT OFFICIAL REPORTS SUB-TABS
        rep_tab1, rep_tab2, rep_tab3 = st.tabs([
            "🌟 ۱. گزارش رفتاری و انضباطی",
            "📈 ۲. گزارش تحلیلی آزمون‌ها",
            "🏆 ۳. کارنامه جامع تحصیلی و پوشه کار"
        ])
        
        with rep_tab1:
            st.subheader(f"🌟 گزارش رفتاری و انضباطی: {st_name}")
            with get_connection() as conn:
                df_b = safe_read_sql("""
                    SELECT id AS 'شناسه', behavior_type AS 'نوع', title AS 'عنوان رفتار', description AS 'توضیحات', log_date AS 'تاریخ'
                    FROM behaviors WHERE student_id = ? ORDER BY id DESC
                """, conn, params=(s_id,))
            if not df_b.empty:
                st.dataframe(df_b, use_container_width=True, hide_index=True)
                
                # Report 1 PDF Generator Call
                last_b = df_b.iloc[0]
                pdf_b_bytes = generate_behavior_pdf(st_name, st_nid, st_grp, last_b['نوع'], last_b['عنوان رفتار'], last_b['توضیحات'], last_b['تاریخ'])
                st.download_button(
                    "📥 دانلود PDF رسمی گزارش رفتاری و انضباطی",
                    data=pdf_b_bytes,
                    file_name=f"behavior_report_{st_info['last_name']}.pdf",
                    mime="application/pdf"
                )
            else:
                st.info("مورد رفتاری ثبت نشده است.")

        with rep_tab2:
            st.subheader(f"📈 گزارش تحلیلی آزمون‌های آنلاین: {st_name}")
            with get_connection() as conn:
                df_q = safe_read_sql("""
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.id DESC
                """, conn, params=(s_id,))
            if not df_q.empty:
                st.dataframe(df_q, use_container_width=True, hide_index=True)
                
                # Interactive Line Chart for Exam Growth
                st.markdown("##### 📈 نمودار رشد درصد نمرات آزمون‌ها:")
                df_chart = safe_read_sql("""
                    SELECT q.title AS 'آزمون', r.percentage AS 'درصد'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id 
                    WHERE r.student_id = ? ORDER BY r.id ASC
                """, conn, params=(s_id,))
                if not df_chart.empty:
                    st.line_chart(df_chart.set_index('آزمون'))
                    
                # Report 2 PDF Generator Call
                pdf_q_bytes = generate_exams_pdf(st_name, st_nid, st_grp, quiz_count, quiz_avg_str)
                st.download_button(
                    "📥 دانلود PDF رسمی گزارش تحلیلی آزمون‌ها",
                    data=pdf_q_bytes,
                    file_name=f"exams_report_{st_info['last_name']}.pdf",
                    mime="application/pdf"
                )
            else:
                st.info("نتیجه آزمونی ثبت نشده است.")

        with rep_tab3:
            st.subheader(f"🏆 کارنامه جامع تحصیلی و پوشه کار نهایی: {st_name}")
            with get_connection() as conn:
                df_e = safe_read_sql("""
                    SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد', eval_date AS 'تاریخ'
                    FROM evaluations WHERE student_id = ? ORDER BY id DESC
                """, conn, params=(s_id,))
            if not df_e.empty:
                st.write("📝 **سوابق ارزشیابی کیفی-توصیفی ۷ درس:**")
                st.dataframe(df_e, use_container_width=True, hide_index=True)
            else:
                st.info("ارزشیابی توصیفی ثبت نشده است.")
                
            # Report 3 PDF Generator Call
            pdf_p_bytes = generate_portfolio_pdf(st_name, st_nid, st_phone, st_grp, eval_count, beh_count, quiz_avg_str)
            st.download_button(
                "📥 دانلود PDF رسمی کارنامه جامع تحصیلی و پوشه کار",
                data=pdf_p_bytes,
                file_name=f"comprehensive_portfolio_{st_info['last_name']}.pdf",
                mime="application/pdf"
            )

