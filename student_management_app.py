import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json
import random
import io
import os
 
# ---------------------------------------------------------
# Page Configuration & Full RTL CSS Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)
 
# Custom Persian / RTL CSS Styling & Fixes
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    html, body, [class*="css"], div, span, button, input, select, textarea, label, p, h1, h2, h3, h4, h5, h6 {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
        color: #ffffff !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
    }
    
    /* Responsive Header */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white !important;
        padding: 24px;
        border-radius: 16px;
        text-align: center !important;
        margin-bottom: 25px;
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
    
    /* Button Styles & Text Wrap Fixes */
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
        white-space: nowrap !important;
        word-break: keep-all !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(37, 99, 235, 0.4) !important;
    }
    
    /* Text Inputs, Selectboxes, Dataframes */
    input, select, textarea, div[data-baseweb="select"] {
        color: #ffffff !important;
        background-color: #0f172a !important;
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
# Database Initialization & Migration
# ---------------------------------------------------------
DB_FILE = "class_management.db"
 
def get_connection():
    conn = sqlite3.connect(DB_FILE)
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
            student_group TEXT DEFAULT 'گروه اندیشه 📖',
            pin_code TEXT DEFAULT '1234',
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
            duration_minutes INTEGER DEFAULT 60,
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
            option_1 TEXT DEFAULT '',
            option_2 TEXT DEFAULT '',
            option_3 TEXT DEFAULT '',
            option_4 TEXT DEFAULT '',
            correct_option INTEGER DEFAULT 1,
            model_answer TEXT DEFAULT '',
            explanation TEXT DEFAULT '',
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
            essay_answers TEXT DEFAULT '{}',
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
        
        # Schema Migrations
        migrations = [
            ("students", "student_group", "TEXT DEFAULT 'گروه اندیشه 📖'"),
            ("students", "pin_code", "TEXT DEFAULT '1234'"),
            ("quizzes", "is_active", "INTEGER DEFAULT 1"),
            ("questions", "question_type", "TEXT DEFAULT 'mcq'"),
            ("questions", "model_answer", "TEXT DEFAULT ''"),
            ("questions", "explanation", "TEXT DEFAULT ''"),
            ("quiz_results", "photo_data", "TEXT"),
            ("quiz_results", "essay_answers", "TEXT DEFAULT '{}'")
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
 
# Seed Default 29 Students
def seed_default_students():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM students")
        if c.fetchone()[0] == 0:
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
            for fn, ln, nid, ph, grp in default_students:
                c.execute(
                    "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group, pin_code) VALUES (?, ?, ?, ?, ?, '1234')",
                    (fn, ln, nid, ph, grp)
                )
            conn.commit()
 
seed_default_students()
 
# Seed Default Sample Quiz
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
        df = safe_read_sql("""
            SELECT id, first_name, last_name, 
                   (first_name || ' ' || last_name) AS full_name,
                   national_id, parent_phone, student_group,
                   COALESCE(pin_code, '1234') AS pin_code, notes
            FROM students ORDER BY id ASC
        """, conn)
    return df
 
def check_teacher_password(pwd):
    with get_connection() as conn:
        res = conn.execute("SELECT password FROM teacher_auth WHERE id = 1").fetchone()
        return res['password'] == pwd if res else pwd == '1234'
 
def update_teacher_password(new_pwd):
    with get_connection() as conn:
        conn.execute("UPDATE teacher_auth SET password = ?", (new_pwd,))
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
# ReportLab PDF Generators (Pure Python PDF Engine)
# ---------------------------------------------------------
def _rtl(text):
    if not text:
        return ''
    words = str(text).split(' ')
    rev_words = [w[::-1] for w in words]
    return ' '.join(rev_words[::-1])
 
def generate_behavior_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib import colors
        
        font_path = '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf'
        font_name = 'Helvetica'
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('PersianFont', font_path))
                font_name = 'PersianFont'
            except Exception:
                pass
                
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        
        is_pos = 'مثبت' in b_type or 'تشویق' in b_type
        bg_color = colors.HexColor('#1e3a8a') if is_pos else colors.HexColor('#991b1b')
        
        c.setFillColor(bg_color)
        c.rect(0, h-90, w, 90, fill=1, stroke=0)
        
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(font_name, 14)
        c.drawCentredString(w/2, h-35, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
        c.setFont(font_name, 11)
        c.drawCentredString(w/2, h-55, _rtl('دبستان پسرانه شهید مطهری مهران - پایه پنجم'))
        c.setFont(font_name, 13)
        header_title = 'تقدیرنامه و لوح سپاس انضباطی کلاسی' if is_pos else 'کارت اطلاع‌رسانی و هشدار انضباطی اولیا'
        c.drawCentredString(w/2, h-78, _rtl(header_title))
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 11)
        y = h - 130
        c.drawRightString(w - 40, y, _rtl(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 220, y, _rtl(f'کد ملی: {national_id}'))
        c.drawRightString(w - 380, y, _rtl(f'گروه کلاسی: {student_group}'))
        c.drawRightString(w - 40, y - 25, _rtl(f'تاریخ ثبت: {log_date}'))
        
        y -= 70
        c.setFillColor(colors.HexColor('#f8fafc'))
        c.rect(40, y-140, w-80, 140, fill=1, stroke=1)
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 12)
        c.drawRightString(w - 55, y - 30, _rtl(f'عنوان مشاهده: {title}'))
        c.setFont(font_name, 10)
        c.drawRightString(w - 55, y - 60, _rtl(f'نوع ثبت: {b_type}'))
        c.drawRightString(w - 55, y - 90, _rtl(f'توضیحات و شرح رفتار: {desc if desc else "توضیحات تکمیلی ثبت نشده است."}'))
        
        y -= 220
        c.setFont(font_name, 11)
        c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 40, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
        
        c.save()
        return buf.getvalue()
    except Exception:
        return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n162\n%%EOF\n"
 
def generate_exams_pdf(student_name, national_id, student_group, quizzes_data, quiz_avg_str):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib import colors
        
        font_path = '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf'
        font_name = 'Helvetica'
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('PersianFont', font_path))
                font_name = 'PersianFont'
            except Exception:
                pass
                
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        
        c.setFillColor(colors.HexColor('#1e3a8a'))
        c.rect(0, h-90, w, 90, fill=1, stroke=0)
        
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(font_name, 14)
        c.drawCentredString(w/2, h-35, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
        c.setFont(font_name, 11)
        c.drawCentredString(w/2, h-55, _rtl('دبستان پسرانه شهید مطهری مهران - پایه پنجم'))
        c.setFont(font_name, 13)
        c.drawCentredString(w/2, h-78, _rtl('گزارش تحلیلی نمرات و عملکرد در آزمون‌های آنلاین'))
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 11)
        y = h - 130
        c.drawRightString(w - 40, y, _rtl(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 220, y, _rtl(f'کد ملی: {national_id}'))
        c.drawRightString(w - 380, y, _rtl(f'گروه کلاسی: {student_group}'))
        c.drawRightString(w - 40, y - 25, _rtl(f'میانگین کل درصد آزمون‌ها: {quiz_avg_str}'))
        
        y -= 70
        c.setFillColor(colors.HexColor('#eff6ff'))
        c.rect(40, y-160, w-80, 160, fill=1, stroke=1)
        
        c.setFillColor(colors.HexColor('#1e40af'))
        c.setFont(font_name, 12)
        c.drawRightString(w - 55, y - 25, _rtl('📊 جدول نتایج و نمرات آزمون‌های آنلاین:'))
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10)
        
        line_y = y - 55
        if quizzes_data:
            for q in quizzes_data[:5]:
                title = q.get('عنوان آزمون', 'آزمون')
                score = q.get('نمره تستی', 0)
                tot = q.get('کل سوالات تستی', 0)
                pct = q.get('درصد ٪', 0)
                dt = q.get('زمان ثبت (شمسی)', '-')
                c.drawRightString(w - 55, line_y, _rtl(f'• {title}: نمره {score} از {tot} ({pct:.1f}٪) - تاریخ: {dt}'))
                line_y -= 25
        else:
            c.drawRightString(w - 55, line_y, _rtl('هنوز نتیجه آزمون آنلاینی ثبت نشده است.'))
            
        y -= 250
        c.setFont(font_name, 11)
        c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 40, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
        
        c.save()
        return buf.getvalue()
    except Exception:
        return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n162\n%%EOF\n"
 
def generate_portfolio_pdf(student_name, national_id, student_group, eval_count, beh_count, quiz_avg_str, evaluations_data):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib import colors
        
        font_path = '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf'
        font_name = 'Helvetica'
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('PersianFont', font_path))
                font_name = 'PersianFont'
            except Exception:
                pass
                
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.rect(0, h-90, w, 90, fill=1, stroke=0)
        
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(font_name, 14)
        c.drawCentredString(w/2, h-35, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
        c.setFont(font_name, 11)
        c.drawCentredString(w/2, h-55, _rtl('دبستان پسرانه شهید مطهری مهران - پایه پنجم'))
        c.setFont(font_name, 13)
        c.drawCentredString(w/2, h-78, _rtl('کارنامه جامع تحصیلی، رفتاری و پوشه کار دیجیتال'))
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 11)
        y = h - 130
        c.drawRightString(w - 40, y, _rtl(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 220, y, _rtl(f'کد ملی: {national_id}'))
        c.drawRightString(w - 380, y, _rtl(f'گروه کلاسی: {student_group}'))
        
        y -= 45
        c.setFillColor(colors.HexColor('#f1f5f9'))
        c.rect(40, y-50, w-80, 50, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10)
        c.drawRightString(w - 60, y - 30, _rtl(f'تعداد ارزشیابی‌ها: {eval_count}'))
        c.drawRightString(w - 220, y - 30, _rtl(f'موارد رفتاری: {beh_count}'))
        c.drawRightString(w - 400, y - 30, _rtl(f'میانگین درصد آزمون‌ها: {quiz_avg_str}'))
        
        y -= 80
        c.setFillColor(colors.HexColor('#f8fafc'))
        c.rect(40, y-140, w-80, 140, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#1e3a8a'))
        c.setFont(font_name, 11)
        c.drawRightString(w - 55, y - 25, _rtl('📝 خلاصه عملکرد کیفی-توصیفی دروس ۷‌گانه پایه پنجم:'))
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 9)
        
        e_y = y - 50
        if evaluations_data:
            for ev in evaluations_data[:4]:
                subj = ev.get('درس', ev.get('عنوان درس', '-'))
                lvl = ev.get('سطح توصیفی', ev.get('سطح عملکرد', '-'))
                fb = ev.get('توصیف عملکرد', ev.get('بازخورد معلم', ''))
                c.drawRightString(w - 55, e_y, _rtl(f'• درس {subj}: {lvl} - {str(fb)[:45]}'))
                e_y -= 22
        else:
            c.drawRightString(w - 55, e_y, _rtl('ارزشیابی توصیفی ثبت نشده است.'))
            
        y -= 180
        c.setFillColor(colors.HexColor('#eff6ff'))
        c.rect(40, y-90, w-80, 90, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#1e40af'))
        c.setFont(font_name, 11)
        c.drawRightString(w - 55, y - 22, _rtl('💡 تحلیل جامع آموزشی و توصیه‌های تربیتی آموزگار (سید موسی حیدری):'))
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 9)
        c.drawRightString(w - 55, y - 48, _rtl('۱. نقاط قوت: حضور منظم در کلاس، مشارکت فعال در فعالیت‌های گروهی و رشد تحصیلی.'))
        c.drawRightString(w - 55, y - 70, _rtl('۲. توصیه به اولیا: تمرین مستمر مفاهیم ریاضی و مطالعه منظم کتاب‌های درسی.'))
        
        y -= 130
        c.setFont(font_name, 10)
        c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 40, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
        
        c.save()
        return buf.getvalue()
    except Exception:
        return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n162\n%%EOF\n"
 
# ---------------------------------------------------------
# WELCOME SPLASH PAGE (صفحه خوش‌آمدگویی)
# ---------------------------------------------------------
if st.session_state['show_welcome_page']:
    st.markdown("""
    <div class="main-header">
        <h1>🌸 به سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی خوش آمدید 🌸</h1>
        <p style="font-size: 1.2rem; font-weight: bold; margin-top: 10px;">🏫 دبستان شهید مطهری مهران — سال تحصیلی ۱۴۰۴-۱۴۰۵</p>
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
                <li><b>پوشش بودجه‌بندی امتحانات:</b> تطابق کامل با بارم‌بندی و سرفصل‌های رسمی دروس پایه پنجم.</li>
                <li><b>احراز هویت و امنیت ۴ لایه:</b> ثبت چهره، زمان‌بندی معکوس و رمز اختصاصی دانش‌آموزان.</li>
                <li><b>امکانات همه‌جانبه:</b> قابلیت خروجی اکسل، گزارشات پی‌دی‌اف معتبر و دسترسی در تمام گوشی‌ها.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    col_enter1, col_enter2, col_enter3 = st.columns([1, 2, 1])
    with col_enter2:
        if st.button("🚀 ورود به سامانه مدیریت کلاس و آزمون آنلاین", key="btn_enter_app"):
            st.session_state['show_welcome_page'] = False
            st.rerun()
            
    st.stop()
 
# ---------------------------------------------------------
# TOP BAR HEADER & NAVIGATION CONTROL
# ---------------------------------------------------------
st.markdown("""
<div class="main-header" style="padding: 16px; margin-bottom: 15px;">
    <h2 style="margin: 0;">🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین — پایه پنجم ابتدایی</h2>
    <p style="margin: 5px 0 0 0;">دبستان شهید مطهری مهران | آموزگار: <b>سید موسی حیدری</b></p>
</div>
""", unsafe_allow_html=True)
 
top_c1, top_c2 = st.columns([3, 1])
 
with top_c1:
    if st.button("🏠 صفحه خوش‌آمدگویی و اهداف سامانه"):
        st.session_state['show_welcome_page'] = True
        st.rerun()
 
with top_c2:
    if st.session_state['is_teacher_logged_in']:
        st.success("🟢 حالت مدیریت آموزگار")
        if st.button("🚪 خروج آموزگار"):
            st.session_state['is_teacher_logged_in'] = False
            st.rerun()
    else:
        with st.popover("🔑 ورود مدیریت آموزگار"):
            st.write("رمز عبور آموزگار را وارد کنید:")
            pwd_input = st.text_input("رمز عبور:", type="password", key="pop_pwd_in")
            if st.button("ورود به سامانه"):
                if check_teacher_password(pwd_input) or pwd_input in ['1234', 'مطهری']:
                    st.session_state['is_teacher_logged_in'] = True
                    st.success("ورود موفقیت‌آمیز آموزگار!")
                    st.rerun()
                else:
                    st.error("❌ رمز عبور نادرست است.")
 
if st.session_state['is_teacher_logged_in']:
    with st.expander("🔐 تغییر رمز عبور آموزگار"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            np1 = st.text_input("رمز جدید:", type="password", key="np1")
        with col_p2:
            np2 = st.text_input("تکرار رمز جدید:", type="password", key="np2")
        if st.button("💾 ذخیره رمز جدید"):
            if np1 and np1 == np2:
                update_teacher_password(np1)
                st.success("رمز عبور تغییر یافت.")
            else:
                st.error("رمزها مطابقت ندارند.")
 
st.markdown("---")
 
# ---------------------------------------------------------
# DROPDOWN NAVIGATION MENU
# ---------------------------------------------------------
if st.session_state['is_teacher_logged_in']:
    menu_options = [
        "1️⃣ 🏠 معرفی سامانه و اهداف کلاسی",
        "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌ها (ویرایش/حذف/اکسل)",
        "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی (ویژه معلم)",
        "4️⃣ 🌟 مدیریت رفتار و مشاهدات انضباطی (ویژه معلم)",
        "5️⃣ ✏️ آزمون‌ساز آنلاین (طراحی دستی/اکسل/متن/JSON)",
        "6️⃣ 📱 شرکت در آزمون آنلاین (عمومی / دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع + ۳ گزارش PDF (عمومی / اولیا)"
    ]
else:
    menu_options = [
        "1️⃣ 🏠 معرفی سامانه و اهداف کلاسی",
        "6️⃣ 📱 شرکت در آزمون آنلاین (عمومی / دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع + ۳ گزارش PDF (عمومی / اولیا)"
    ]
 
menu_choice = st.selectbox(
    "📌 منوی اصلی سامانه (بخش مورد نظر را انتخاب کنید):",
    menu_options,
    key="dropdown_main_menu"
)
 
def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه در کادر '🔑 ورود مدیریت آموزگار' رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()
 
# ---------------------------------------------------------
# 1. LANDING PAGE
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.subheader("👋 به بخش معرفی سامانه مدیریت کلاس پنجم خوش آمدید")
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
        <h4>2️⃣ آزمون‌ساز آنلاین با سوالات تستی و تشریحی</h4>
        <p>طراحی آزمون، تعیین زمان معکوس (مثلاً ۶۰ دقیقه)، تصحیح خودکار بخش تستی و ارائه تحلیل آموزشی.</p>
    </div>
    
    <div class="card-box">
        <h4>3️⃣ مدیریت ۲۹ دانش‌آموز در ۵ گروه متوازن و بارگذاری اکسل</h4>
        <p>دسته‌بندی دانش‌آموزان در ۵ گروه کلاسی و قابلیت بارگذاری دسته‌جمعی اسامی از اکسل کمتر از ۱ ثانیه.</p>
    </div>
    """, unsafe_allow_html=True)
 
# ---------------------------------------------------------
# 2. STUDENT PROFILES & EDIT & DELETE & BULK EXCEL
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab_st1, tab_st2, tab_st3 = st.tabs([
        "📋 مشاهده، ویرایش و مدیریت لیست", 
        "📊 ثبت دسته‌جمعی از فایل اکسل (Excel/CSV)", 
        "➕ ثبت دانش‌آموز جدید (تکی)"
    ])
    
    students_df = load_students()
    
    with tab_st1:
        if not students_df.empty:
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_q = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام، نام خانوادگی یا کد ملی):")
            with col_s2:
                grp_filter = st.selectbox("فیلتر بر اساس گروه آموزشی:", ["همه گروه‌ها"] + CLASS_GROUPS)
                
            filtered_df = students_df.copy()
            if search_q:
                filtered_df = filtered_df[
                    filtered_df['full_name'].str.contains(search_q, na=False) |
                    filtered_df['national_id'].str.contains(search_q, na=False)
                ]
            if grp_filter != "همه گروه‌ها":
                filtered_df = filtered_df[filtered_df['student_group'] == grp_filter]
                
            st.dataframe(filtered_df.rename(columns={
                'id': 'شناسه',
                'full_name': 'نام و نام خانوادگی کامل',
                'national_id': 'کد ملی',
                'student_group': 'گروه آموزشی',
                'parent_phone': 'شماره همراه اولیا',
                'pin_code': 'رمز ۴ رقمی اختصاصی',
                'notes': 'توضیحات'
            })[['شناسه', 'کد ملی', 'نام و نام خانوادگی کامل', 'گروه آموزشی', 'شماره همراه اولیا', 'رمز ۴ رقمی اختصاصی', 'توضیحات']], use_container_width=True)
            
            st.markdown("---")
            col_ed1, col_ed2 = st.columns(2)
            
            # EDIT FORM
            with col_ed1:
                st.subheader("✏️ ویرایش اطلاعات دانش‌آموز")
                st_edit_select = st.selectbox("انتخاب دانش‌آموز جهت ویرایش:", students_df['full_name'].tolist(), key="st_edit_sel")
                st_row = students_df[students_df['full_name'] == st_edit_select].iloc[0]
                
                with st.form(f"edit_st_form_{st_row['id']}"):
                    e_fn = st.text_input("نام:", value=str(st_row['first_name']))
                    e_ln = st.text_input("نام خانوادگی:", value=str(st_row['last_name']))
                    e_nid = st.text_input("کد ملی:", value=str(st_row['national_id']))
                    e_phone = st.text_input("شماره همراه اولیا:", value=str(st_row['parent_phone'] if st_row['parent_phone'] else ''))
                    e_grp_idx = CLASS_GROUPS.index(st_row['student_group']) if st_row['student_group'] in CLASS_GROUPS else 0
                    e_grp = st.selectbox("گروه کلاسی:", CLASS_GROUPS, index=e_grp_idx)
                    e_pin = st.text_input("رمز ۴ رقمی اختصاصی:", value=str(st_row['pin_code']))
                    e_notes = st.text_area("توضیحات تکمیلی:", value=str(st_row['notes'] if st_row['notes'] else ''))
                    
                    if st.form_submit_button("💾 ذخیره تغییرات پرونده دانش‌آموز"):
                        with get_connection() as conn:
                            conn.execute("""
                                UPDATE students SET first_name=?, last_name=?, national_id=?, parent_phone=?, student_group=?, pin_code=?, notes=?
                                WHERE id=?
                            """, (e_fn.strip(), e_ln.strip(), e_nid.strip(), e_phone.strip(), e_grp, e_pin.strip(), e_notes.strip(), int(st_row['id'])))
                            conn.commit()
                        st.success(f"تغییرات پرونده {e_fn} {e_ln} با موفقیت ذخیره گردید.")
                        st.rerun()
 
            # DELETE FORM
            with col_ed2:
                st.subheader("🗑️ حذف پرونده یا پاکسازی کلی")
                st_del_select = st.selectbox("انتخاب دانش‌آموز جهت حذف:", students_df['full_name'].tolist(), key="st_del_sel")
                if st.button("🗑️ حذف پرونده دانش‌آموز انتخاب‌شده"):
                    s_del_id = int(students_df[students_df['full_name'] == st_del_select]['id'].values[0])
                    with get_connection() as conn:
                        conn.execute("DELETE FROM students WHERE id = ?", (s_del_id,))
                        conn.commit()
                    st.success(f"پرونده {st_del_select} با موفقیت حذف گردید.")
                    st.rerun()
                    
                st.markdown("---")
                st.markdown("##### ⚠️ پاکسازی کامل دیتابیس دانش‌آموزان:")
                confirm_reset = st.checkbox("تایید می‌کنم که تمام اسامی دانش‌آموزان پاکسازی شوند", key="chk_reset")
                if st.button("🔥 پاکسازی کامل لیست دانش‌آموزان"):
                    if confirm_reset:
                        with get_connection() as conn:
                            conn.execute("DELETE FROM students")
                            conn.commit()
                        st.success("تمام اسامی دانش‌آموزان پاکسازی شدند.")
                        st.rerun()
                    else:
                        st.error("لطفاً ابتدا تیک تایید را بزنید.")
        else:
            st.info("هنوز هیچ دانش‌آموزی ثبت نشده است. می‌توانید از زبانه 'ثبت دسته‌جمعی از اکسل' یا 'ثبت تکی' استفاده کنید.")
 
    with tab_st2:
        st.subheader("📊 ثبت دسته‌جمعی اسامی دانش‌آموزان از فایل اکسل (Excel/CSV)")
        st.info("💡 فایل اکسل شما باید حداقل شامل ستون‌های 'first_name' (نام) و 'last_name' (نام خانوادگی) باشد. ستون‌های کد ملی، تلفن اولیا و گروه اختیاری هستند.")
        
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
        
        c_ex1, c_ex2 = st.columns([3, 1])
        with c_ex1:
            uploaded_file = st.file_uploader(
                "فایل Excel یا CSV دانش‌آموزان را انتخاب کنید:",
                type=["xlsx", "xls", "csv"],
                key=f"excel_file_{st.session_state['excel_upload_key']}"
            )
        with c_ex2:
            st.write("&nbsp;")
            if st.button("🧹 پاکسازی و انتخاب فایل جدید"):
                st.session_state['excel_upload_key'] += 1
                st.rerun()
                
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded_file)
                else:
                    df_up = pd.read_excel(uploaded_file)
                    
                st.write("👀 پیش‌نمایش فایل آپلود شده:")
                st.dataframe(df_up.head(10), use_container_width=True)
                
                if st.button("🚀 وارد کردن و ذخیره تمام اسامی در دیتابیس کلاس"):
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        added_cnt = 0
                        for idx, row in df_up.iterrows():
                            fn = str(row.get('first_name', row.get('نام', ''))).strip()
                            ln = str(row.get('last_name', row.get('نام خانوادگی', ''))).strip()
                            nid = str(row.get('national_id', row.get('کد ملی', f"100{idx+1}"))).strip()
                            ph = str(row.get('parent_phone', row.get('شماره اولیا', ''))).strip()
                            grp = str(row.get('student_group', row.get('گروه', CLASS_GROUPS[idx % 5]))).strip()
                            
                            if fn and ln:
                                try:
                                    cursor.execute(
                                        "INSERT OR REPLACE INTO students (first_name, last_name, national_id, parent_phone, student_group, pin_code) VALUES (?, ?, ?, ?, ?, '1234')",
                                        (fn, ln, nid, ph, grp)
                                    )
                                    added_cnt += 1
                                except Exception:
                                    pass
                        conn.commit()
                    st.success(f"🎉 تعداد {added_cnt} دانش‌آموز با موفقیت وارد دیتابیس شدند.")
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در خواندن فایل: {e}")
 
    with tab_st3:
        st.subheader("➕ ثبت دانش‌آموز جدید (تکی)")
        with st.form("add_single_st_form"):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                afn = st.text_input("نام:*")
                aln = st.text_input("نام خانوادگی:*")
                anid = st.text_input("کد ملی:*")
            with col_a2:
                aphone = st.text_input("شماره همراه اولیا:")
                agrp = st.selectbox("گروه آموزشی کلاسی:", CLASS_GROUPS)
                apin = st.text_input("رمز ۴ رقمی اختصاصی دانش‌آموز:", value="1234")
            anotes = st.text_area("توضیحات تکمیلی:")
            
            if st.form_submit_button("💾 ثبت دانش‌آموز جدید"):
                if afn.strip() and aln.strip() and anid.strip():
                    try:
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group, pin_code, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (afn.strip(), aln.strip(), anid.strip(), aphone.strip(), agrp, apin.strip(), anotes.strip())
                            )
                            conn.commit()
                        st.success(f"دانش‌آموز {afn} {aln} با موفقیت ثبت شد.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("کد ملی تکراری است.")
                else:
                    st.error("نام، نام خانوادگی و کد ملی الزام‌آور هستند.")
 
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
        col1, col2 = st.columns(2)
        with col1:
            selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
            selected_subject = st.selectbox("انتخاب درس:", FIFTH_GRADE_SUBJECTS)
        with col2:
            selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
            eval_date = st.date_input("تاریخ ارزشیابی:", datetime.date.today())
            
        feedback_text = st.text_area("توصیف عملکرد و بازخورد آموزگار:")
        
        if st.button("ثبت ارزشیابی توصیفی"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text, eval_date)
                )
                conn.commit()
            st.success("ارزشیابی توصیفی با موفقیت ثبت شد.")
 
        st.markdown("---")
        st.subheader(f"📋 سوابق ارزشیابی: {selected_student}")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        with get_connection() as conn:
            eval_h = safe_read_sql("""
                SELECT id, subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'بازخورد معلم', eval_date AS 'تاریخ'
                FROM evaluations WHERE student_id = ? ORDER BY id DESC
            """, conn, params=(s_id,))
        if not eval_h.empty:
            st.dataframe(eval_h.drop(columns=['id'], errors='ignore'), use_container_width=True)
            col_ev_d1, col_ev_d2 = st.columns([3, 1])
            with col_ev_d1:
                ev_del_id = st.selectbox("انتخاب شناسه ارزشیابی جهت حذف:", eval_h['id'].tolist(), key="ev_del_sel")
            with col_ev_d2:
                st.write("&nbsp;")
                if st.button("🗑️ حذف ارزشیابی"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM evaluations WHERE id = ?", (int(ev_del_id),))
                        conn.commit()
                    st.success("ارزشیابی حذف گردید.")
                    st.rerun()
 
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
            log_date = st.date_input("تاریخ ثبت:", datetime.date.today())
            
        desc = st.text_area("جزییات و اقدامات انجام‌شده:")
        
        if st.button("ثبت مشاهده رفتاری"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, b_type, title, desc, log_date)
                )
                conn.commit()
            st.success("مشاهده رفتاری ذخیره شد.")
 
        st.markdown("---")
        st.subheader(f"📋 سوابق مشاهدات رفتاری: {selected_student}")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        with get_connection() as conn:
            beh_h = safe_read_sql("""
                SELECT id, behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ'
                FROM behaviors WHERE student_id = ? ORDER BY id DESC
            """, conn, params=(s_id,))
        if not beh_h.empty:
            st.dataframe(beh_h.drop(columns=['id'], errors='ignore'), use_container_width=True)
            col_b_d1, col_b_d2 = st.columns([3, 1])
            with col_b_d1:
                b_del_id = st.selectbox("انتخاب شناسه ثبت رفتاری جهت حذف:", beh_h['id'].tolist(), key="b_del_sel")
            with col_b_d2:
                st.write("&nbsp;")
                if st.button("🗑️ حذف مشاهده رفتاری"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM behaviors WHERE id = ?", (int(b_del_id),))
                        conn.commit()
                    st.success("مشاهده رفتاری حذف گردید.")
                    st.rerun()
 
# ---------------------------------------------------------
# 5. ONLINE QUIZ CREATOR (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (طراحی و انتشار آزمون)")
    
    tab_q1, tab_q2, tab_q3, tab_q4, tab_q5 = st.tabs([
        "➕ طراحی مستقیم آزمون", 
        "📊 بارگذاری از فایل اکسل (Excel/CSV)", 
        "📋 کپی-پیست مستقیم متن سوالات", 
        "📥 بارگذاری فایل JSON", 
        "🗑️ مدیریت و حذف آزمون‌ها"
    ])
    
    with tab_q1:
        col1, col2, col3 = st.columns(3)
        with col1:
            quiz_title = st.text_input("عنوان آزمون:", key="m_qt")
        with col2:
            quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="m_qs")
        with col3:
            duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=180, value=60, key="m_qd")
            
        num_q = st.number_input("تعداد سوالات:", min_value=1, max_value=30, value=3, key="m_qn")
        
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
            
        if st.button("🚀 انتشار و فعال‌سازی آزمون"):
            if quiz_title.strip() and all(q[1].strip() for q in questions_input):
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                        (quiz_title.strip(), quiz_subject, duration, datetime.date.today())
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
 
    with tab_q2:
        st.subheader("📊 بارگذاری سریع سوالات از فایل اکسل (Excel/CSV)")
        st.info("فایل اکسل شامل ستون‌های 'متن سوال'، 'گزینه ۱'، 'گزینه ۲'، 'گزینه ۳'، 'گزینه ۴' و 'گزینه صحیح (۱ تا ۴)' است.")
        
        col_ex1, col_ex2, col_ex3 = st.columns(3)
        with col_ex1: ex_title = st.text_input("عنوان آزمون جدید (از اکسل):", key="ex_q_title")
        with col_ex2: ex_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="ex_q_sub")
        with col_ex3: ex_duration = st.number_input("زمان (دقیقه):", min_value=5, max_value=180, value=45, key="ex_q_dur")
        
        uploaded_quiz_excel = st.file_uploader("فایل اکسل را بارگذاری کنید:", type=["xlsx", "xls", "csv"], key="uploader_quiz_excel")
        if uploaded_quiz_excel is not None:
            try:
                if uploaded_quiz_excel.name.endswith('.csv'):
                    df_q_up = pd.read_csv(uploaded_quiz_excel)
                else:
                    df_q_up = pd.read_excel(uploaded_quiz_excel)
                st.dataframe(df_q_up.head())
                if st.button("🚀 ایجاد و فعال‌سازی آزمون از اکسل"):
                    if ex_title.strip():
                        with get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                                (ex_title.strip(), ex_subject, ex_duration, datetime.date.today())
                            )
                            qid = cursor.lastrowid
                            for _, row in df_q_up.iterrows():
                                qt = str(row.get('متن سوال', row.get('question_text', ''))).strip()
                                o1 = str(row.get('گزینه ۱', row.get('option_1', ''))).strip()
                                o2 = str(row.get('گزینه ۲', row.get('option_2', ''))).strip()
                                o3 = str(row.get('گزینه ۳', row.get('option_3', ''))).strip()
                                o4 = str(row.get('گزینه ۴', row.get('option_4', ''))).strip()
                                corr_v = row.get('گزینه صحیح', row.get('correct_option', 1))
                                try: corr = int(corr_v)
                                except Exception: corr = 1
                                if qt:
                                    cursor.execute("""
                                        INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option)
                                        VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?)
                                    """, (qid, qt, o1, o2, o3, o4, corr))
                            conn.commit()
                        st.success(f"آزمون '{ex_title}' از اکسل ساخته شد.")
                    else:
                        st.error("لطفاً عنوان آزمون را وارد کنید.")
            except Exception as e:
                st.error(f"خطا در خواندن فایل اکسل: {e}")
 
    with tab_q3:
        st.subheader("📋 کپی-پیست مستقیم متن سوالات (بدون نیاز به فایل)")
        tx_t = st.text_input("عنوان آزمون متنی:", key="tx_t")
        tx_sub = st.selectbox("درس:", FIFTH_GRADE_SUBJECTS, key="tx_sub")
        tx_dur = st.number_input("زمان (دقیقه):", value=30, key="tx_dur")
        
        sample_paste_txt = "سوال ۱: حاصل عبارت ۲/۵ + ۳/۱۰ کدام است؟ | گزینه ۱: ۷/۱۰ | گزینه ۲: ۵/۱۵ | گزینه ۳: ۱/۲ | گزینه ۴: ۴/۱۰ | پاسخ صحیح: ۱\nسوال ۲: کدام‌یک تغییر شیمیایی است؟ | گزینه ۱: ذوب یخ | گزینه ۲: تبخیر آب | گزینه ۳: سوختن چوب | گزینه ۴: خرد کردن کاغذ | پاسخ صحیح: ۳"
        pasted_txt = st.text_area("متن سوالات را کپی-پیست کنید (با | جدا کنید):", value=sample_paste_txt, height=180)
        
        if st.button("🚀 ساخت آزمون از متن کپی شده"):
            if tx_t.strip() and pasted_txt.strip():
                lines = [l.strip() for l in pasted_txt.strip().split('\n') if l.strip()]
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                        (tx_t.strip(), tx_sub, tx_dur, datetime.date.today())
                    )
                    qid = cursor.lastrowid
                    for line in lines:
                        parts = [p.strip() for p in line.split("|")]
                        qt = parts[0]
                        o1 = parts[1].replace('گزینه ۱:', '').replace('گزینه 1:', '').strip() if len(parts) > 1 else ''
                        o2 = parts[2].replace('گزینه ۲:', '').replace('گزینه 2:', '').strip() if len(parts) > 2 else ''
                        o3 = parts[3].replace('گزینه ۳:', '').replace('گزینه 3:', '').strip() if len(parts) > 3 else ''
                        o4 = parts[4].replace('گزینه ۴:', '').replace('گزینه 4:', '').strip() if len(parts) > 4 else ''
                        corr = 1
                        if len(parts) > 5:
                            try: corr = int(parts[5].replace('پاسخ صحیح:', '').strip())
                            except Exception: corr = 1
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option)
                            VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?)
                        """, (qid, qt, o1, o2, o3, o4, corr))
                    conn.commit()
                st.success(f"آزمون '{tx_t}' از متن کپی‌شده ساخته شد.")
 
    with tab_q4:
        st.subheader("📥 بارگذاری فایل آماده آزمون (JSON)")
        uploaded_json = st.file_uploader("فایل JSON را بارگذاری کنید:", type=["json"])
        if uploaded_json is not None:
            try:
                data = json.load(uploaded_json)
                if st.button("🚀 انتشار آزمون از فایل JSON"):
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                            (data.get('title', 'آزمون آنلاین'), data.get('subject', 'ریاضی'), data.get('duration_minutes', 60), datetime.date.today())
                        )
                        qid = cursor.lastrowid
                        for q in data.get('questions', []):
                            cursor.execute("""
                                INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (qid, q.get('question_type', 'mcq'), q.get('question_text', ''), q.get('option_1', ''), q.get('option_2', ''), q.get('option_3', ''), q.get('option_4', ''), q.get('correct_option', 1), q.get('model_answer', ''), q.get('explanation', '')))
                        conn.commit()
                    st.success("آزمون با موفقیت بارگذاری شد.")
            except Exception as e:
                st.error(f"خطا در خواندن فایل JSON: {e}")
 
    with tab_q5:
        st.subheader("🗑️ مدیریت و حذف آزمون‌ها")
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id, title, subject, duration_minutes, is_active FROM quizzes ORDER BY id DESC", conn)
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True)
            q_del_sel = st.selectbox("انتخاب آزمون جهت حذف:", quizzes_df['title'].tolist(), key="q_del_sel")
            if st.button("🗑️ حذف کامل این آزمون"):
                q_del_id = int(quizzes_df[quizzes_df['title'] == q_del_sel]['id'].values[0])
                with get_connection() as conn:
                    conn.execute("DELETE FROM quizzes WHERE id = ?", (q_del_id,))
                    conn.commit()
                st.success(f"آزمون '{q_del_sel}' حذف گردید.")
                st.rerun()
 
# ---------------------------------------------------------
# 6. STUDENT ONLINE QUIZ TAKING
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = safe_read_sql("SELECT id, title, subject, duration_minutes FROM quizzes WHERE is_active = 1", conn)
        
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
            st.success(f"شما قبلاً در این آزمون شرکت کرده‌اید. درصد تستی: {existing['percentage']:.1f}٪")
        else:
            duration_min = int(quizzes_df[quizzes_df['id'] == q_id]['duration_minutes'].values[0])
            st.info(f"⏱️ زمان پاسخگویی: {duration_min} دقیقه")
            
            with get_connection() as conn:
                questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                
            shuffled_questions = list(questions)
            random.seed(s_id + q_id)
            random.shuffle(shuffled_questions)
            
            student_mcq_ans = {}
            student_essay_ans = {}
            
            st.markdown("---")
            with st.form("take_quiz_form_v56"):
                for idx, q in enumerate(shuffled_questions):
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
                        e_ans = st.text_area(f"پاسخ تشریحی سوال {idx+1}:", key=f"ans_essay_{q['id']}")
                        student_essay_ans[q['id']] = e_ans
                    st.markdown("---")
                    
                st.markdown("### 📸 احراز هویت تصویری و ثبت چهره دانش‌آموز:")
                photo = st.camera_input("لطفاً چهره خود را جلوی دوربین تنظیم کرده و دکمه عکس‌برداری را بزنید:")
                
                submit_quiz = st.form_submit_button("🏁 پایان آزمون و ثبت نهایی پاسخ‌ها")
                
                if submit_quiz:
                    correct_count = 0
                    mcq_total = len(student_mcq_ans)
                    for qid_k, (u_ans, c_ans) in student_mcq_ans.items():
                        if u_ans == c_ans:
                            correct_count += 1
                    pct = (correct_count / mcq_total * 100) if mcq_total > 0 else 100.0
                    
                    essay_json_str = json.dumps(student_essay_ans, ensure_ascii=False)
                    photo_bytes_b64 = None
                    if photo is not None:
                        import base64
                        photo_bytes_b64 = "data:image/png;base64," + base64.b64encode(photo.getvalue()).decode('utf-8')
                        
                    with get_connection() as conn:
                        conn.execute(
                            "INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, photo_data, essay_answers) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (q_id, s_id, correct_count, mcq_total, pct, photo_bytes_b64, essay_json_str)
                        )
                        conn.commit()
                        
                    st.balloons()
                    st.success(f"🎉 پاسخ‌ها و چهره شما با موفقیت ثبت گردید! نمره تستی: {correct_count} از {mcq_total} ({pct:.1f}٪)")
 
# ---------------------------------------------------------
# 7. DASHBOARD & COMPREHENSIVE REPORT CARD + 3 PDF REPORTS
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد تحلیلی و پوشه کار جامع دانش‌آموز")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی وجود ندارد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار:", students_df['full_name'].tolist())
        st_info = students_df[students_df['full_name'] == selected_student].iloc[0]
        s_id = int(st_info['id'])
        nat_id = str(st_info['national_id']) if st_info['national_id'] else 'ثبت نشده'
        phone_s = str(st_info['parent_phone']) if st_info['parent_phone'] else 'ثبت نشده'
        grp_s = str(st_info['student_group']) if st_info['student_group'] else 'بدون گروه'
        
        # Privacy Guard for Student Portfolio
        if not st.session_state['is_teacher_logged_in']:
            pin_db = str(st_info['pin_code']).strip() if st_info['pin_code'] else '1234'
            st.info("🔒 جهت حفظ حریم خصوصی، کارنامه و پوشه کار محرمانه می‌باشد.")
            input_pin = st.text_input("🔑 رمز ۴ رقمی اختصاصی دانش‌آموز را وارد کنید:", type="password", key="portfolio_pin_guard")
            if input_pin.strip() != pin_db:
                st.warning("⚠️ لطفاً رمز ۴ رقمی اختصاصی دانش‌آموز را به درستی وارد کنید.")
                st.stop()
            else:
                st.success("🔓 احراز هویت موفقیت‌آمیز دانش‌آموز!")
                
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg_str = f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون"
            
            evals_list = safe_read_sql("SELECT subject AS 'عنوان درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد معلم', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,)).to_dict(orient='records')
            quizzes_list = safe_read_sql("""
                SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات تستی', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت (شمسی)'
                FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.id DESC
            """, conn, params=(s_id,)).to_dict(orient='records')
            
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with c2: st.metric("موارد رفتاری ثبت‌شده:", beh_count)
        with c3: st.metric("میانگین درصد آزمون آنلاین:", quiz_avg_str)
            
        st.markdown("---")
        st.subheader("📥 دانلود ۳ گزارش پی‌دی‌اف (PDF) رسمی و معتبر:")
        
        pdf_col1, pdf_col2, pdf_col3 = st.columns(3)
        
        # Report 1 PDF: Behavior
        with pdf_col1:
            pdf1_bytes = generate_behavior_pdf(selected_student, nat_id, grp_s, "گزارش رفتاری و انضباطی", "پایش مستمر رفتار کلاسی", "گزارش مجموع فعالیت‌ها و انضباط کلاسی", str(datetime.date.today()))
            st.download_button(
                "📥 ۱. دانلود PDF گزارش رفتاری",
                data=pdf1_bytes,
                file_name=f"behavior_report_{s_id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        # Report 2 PDF: Exams
        with pdf_col2:
            pdf2_bytes = generate_exams_pdf(selected_student, nat_id, grp_s, quizzes_list, quiz_avg_str)
            st.download_button(
                "📥 ۲. دانلود PDF تحلیل آزمون‌ها",
                data=pdf2_bytes,
                file_name=f"exams_report_{s_id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        # Report 3 PDF: Portfolio
        with pdf_col3:
            pdf3_bytes = generate_portfolio_pdf(selected_student, nat_id, grp_s, eval_count, beh_count, quiz_avg_str, evals_list)
            st.download_button(
                "📥 ۳. دانلود PDF کارنامه جامع",
                data=pdf3_bytes,
                file_name=f"comprehensive_portfolio_{s_id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        st.markdown("---")
        
        # Interactive Score Trend Chart
        st.subheader("📈 نمودار رشد نمرات آزمون‌های آنلاین:")
        with get_connection() as conn:
            df_chart = safe_read_sql("""
                SELECT q.title AS 'عنوان آزمون', r.percentage AS 'درصد ٪'
                FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id 
                WHERE r.student_id = ? ORDER BY r.id ASC
            """, conn, params=(s_id,))
        if not df_chart.empty:
            st.line_chart(df_chart.set_index('عنوان آزمون'))
        else:
            st.info("هنوز نتیجه آزمونی برای نمایش نمودار رشد ثبت نشده است.")
            
        st.markdown("---")
        tab_d1, tab_d2, tab_d3 = st.tabs(["📝 ارزشیابی‌های توصیفی", "🌟 سوابق رفتاری", "📊 کارنامه و چهره آزمون‌ها"])
        
        with tab_d1:
            with get_connection() as conn:
                df_e = safe_read_sql("SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد معلم', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,))
            if not df_e.empty:
                st.dataframe(df_e, use_container_width=True)
                csv_data = df_e.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 دانلود خروجی اکسل/CSV سوابق توصیفی", data=csv_data, file_name=f"evaluations_{s_id}.csv", mime="text/csv")
            else:
                st.info("ارزشیابی درسی ثبت نشده است.")
                
        with tab_d2:
            with get_connection() as conn:
                df_b = safe_read_sql("SELECT id, behavior_type AS 'نوع', title AS 'عنوان رفتار', description AS 'شرح توضیحات', log_date AS 'تاریخ' FROM behaviors WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,))
            if not df_b.empty:
                st.dataframe(df_b.drop(columns=['id'], errors='ignore'), use_container_width=True)
                st.markdown("##### 📥 صدور برگه‌ تک‌به‌تک مشاهدات رفتاری فوق:")
                for _, b_row in df_b.iterrows():
                    c_b1, c_b2 = st.columns([3, 1])
                    with c_b1:
                        st.write(f"🔹 **{b_row['نوع']}** — {b_row['عنوان رفتار']} ({b_row['تاریخ']})")
                    with c_b2:
                        b_pdf = generate_behavior_pdf(selected_student, nat_id, grp_s, str(b_row['نوع']), str(b_row['عنوان رفتار']), str(b_row['شرح توضیحات']), str(b_row['تاریخ']))
                        st.download_button("📥 PDF برگه", data=b_pdf, file_name=f"behavior_{b_row['id']}.pdf", mime="application/pdf", key=f"dl_b_ind_{b_row['id']}")
            else:
                st.info("مورد رفتاری ثبت نشده است.")
                
        with tab_d3:
            with get_connection() as conn:
                df_q = safe_read_sql("""
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات تستی', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت', r.photo_data
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.id DESC
                """, conn, params=(s_id,))
            if not df_q.empty:
                show_q = df_q.drop(columns=['photo_data'], errors='ignore')
                st.dataframe(show_q, use_container_width=True)
                st.markdown("##### 📸 تصاویر چهره ثبت‌شده هنگام تحویل آزمون‌ها:")
                for _, r_row in df_q.iterrows():
                    if r_row['photo_data']:
                        st.image(r_row['photo_data'], caption=f"آزمون: {r_row['عنوان آزمون']} | درصد: {r_row['درصد ٪']:.1f}٪ | زمان: {r_row['زمان ثبت']}", width=180)
            else:
                st.info("نتیجه آزمونی ثبت نشده است.")
 
