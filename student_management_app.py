import os
import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json
import random
import io
import base64

# ---------------------------------------------------------
# Page Configuration & Clean Persian RTL CSS Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="auto"
)

# Custom Persian / RTL CSS (Targeted, high-contrast, no text leakage)
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    /* Base Typography & Color Reset */
    html, body, .stApp {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #f8fafc !important;
    }
    
    /* Standard Text & Headings Color */
    p, span, label, h1, h2, h3, h4, h5, h6, .stMarkdown {
        color: #f8fafc !important;
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
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
    .main-header h1, .main-header h2, .main-header p {
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
    
    /* Input Control Boxes */
    input, select, textarea, div[data-baseweb="select"] > div {
        color: #ffffff !important;
        background-color: #0f172a !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
    }
    
    /* Clean Popover Box Styling */
    div[data-baseweb="popover"] {
        background-color: #1e293b !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 10px !important;
    }
    
    /* Button Styling */
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
    
    /* Tab Styling */
    button[data-baseweb="tab"] {
        background-color: rgba(30, 41, 59, 0.6) !important;
        color: #94a3b8 !important;
        border-radius: 8px 8px 0 0 !important;
        font-weight: bold !important;
        padding: 10px 16px !important;
    }
    
    button[aria-selected="true"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Database Initialization & Migration System
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
            student_group TEXT DEFAULT 'گروه ارمغان 🚀',
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
        
        # Schema Migrations
        migrations = [
            ("students", "student_group", "TEXT DEFAULT 'گروه ارمغان 🚀'"),
            ("students", "pin_code", "TEXT DEFAULT '1234'"),
            ("quizzes", "is_active", "INTEGER DEFAULT 1"),
            ("questions", "question_type", "TEXT DEFAULT 'mcq'"),
            ("questions", "model_answer", "TEXT"),
            ("questions", "explanation", "TEXT"),
            ("quiz_results", "photo_data", "TEXT"),
            ("quiz_results", "essay_answers", "TEXT")
        ]
        for table, col, col_type in migrations:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            except Exception:
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

# Seed 29 Default Students if Empty
def seed_default_students():
    with get_connection() as conn:
        c = conn.cursor()
        count = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if count == 0:
            st_data = [
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
            for fn, ln, nid, ph, grp in st_data:
                c.execute("""
                    INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group)
                    VALUES (?, ?, ?, ?, ?)
                """, (fn, ln, nid, ph, grp))
            conn.commit()

seed_default_students()

# Seed Sample Quiz
def seed_default_quiz():
    with get_connection() as conn:
        cursor = conn.cursor()
        count = cursor.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]
        if count == 0:
            cursor.execute(
                "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                ("آزمونک جامع فصل اول ریاضی و علوم پنجم", "ریاضی", 60, datetime.date.today().strftime("%Y/%m/%d"))
            )
            quiz_id = cursor.lastrowid
            sample_questions = [
                ('mcq', 'حاصل کسر ۲/۵ + ۳/۱۰ کدام است؟', '۷/۱۰', '۵/۱۵', '۱/۲', '۴/۱۰', 1, None, 'ابتدا مخرج مشترک ۱۰ می‌گیریم: ۴/۱۰ + ۳/۱۰ = ۷/۱۰.'),
                ('mcq', 'کدام‌یک از تغییرات زیر یک تغییر شیمیایی محسوب می‌شود؟', 'ذوب شدن یخ', 'تبخیر آب', 'سوختن چوب', 'خرد کردن کاغذ', 3, None, 'سوختن چوب تغییر شیمیایی است چون جنس ماده تغییر می‌کند.'),
                ('mcq', 'در الگوی عددی ۵، ۹، ۱۳، ۱۷، ... عدد بعدی کدام است؟', '۱۹', '۲۱', '۲۰', '۲۲', 2, None, 'الگو ۴ تا ۴ تا اضافه می‌شود: ۱۷ + ۴ = ۲۱.'),
                ('essay', 'تفاوت تغییر فیزیکی و تغییر شیمیایی را با یک مثال توضیح دهید.', None, None, None, None, 1, 'در تغییر فیزیکی جنس ماده عوض نمی‌شود (مثل ذوب یخ)، اما در تغییر شیمیایی ماده جدیدی تولید می‌شود (مثل پختن نان).', 'ملاک نمره‌دهی: اشاره درست به عدم تغییر جنس ماده در تغییر فیزیکی و ایجاد ماده جدید در تغییر شیمیایی.')
            ]
            for q in sample_questions:
                cursor.execute("""
                    INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
            conn.commit()

seed_default_quiz()

# ---------------------------------------------------------
# Helper Functions & Persian Font / Bidi Reshaper
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

def _rtl(text):
    if not text: return ""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return str(text)

def load_students():
    with get_connection() as conn:
        df = safe_read_sql("SELECT id, first_name, last_name, national_id, parent_phone, student_group, pin_code, notes FROM students", conn)
        if not df.empty:
            df['full_name'] = df['first_name'].astype(str).str.strip() + ' ' + df['last_name'].astype(str).str.strip()
            df = df.loc[:, ~df.columns.duplicated()]
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

# ---------------------------------------------------------
# PDF GENERATION ENGINE (REPORTLAB WITH PERSIAN SUPPORT)
# ---------------------------------------------------------
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
        
        # Header Box
        header_color = colors.HexColor('#166534') if 'تشویق' in b_type or 'مثبت' in b_type else colors.HexColor('#991b1b')
        c.setFillColor(header_color)
        c.rect(0, h-90, w, 90, fill=1, stroke=0)
        
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(font_name, 14)
        c.drawCentredString(w/2, h-35, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
        c.setFont(font_name, 11)
        c.drawCentredString(w/2, h-55, _rtl('دبستان پسرانه شهید مطهری مهران - پایه پنجم'))
        c.setFont(font_name, 13)
        doc_title = 'تقدیرنامه و لوح سپاس انضباطی کلاسی' if 'تشویق' in b_type or 'مثبت' in b_type else 'کارت هشدار و پیگیری انضباطی اولیا'
        c.drawCentredString(w/2, h-78, _rtl(doc_title))
        
        # Body Box
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 11)
        y = h - 130
        c.drawRightString(w - 40, y, _rtl(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 220, y, _rtl(f'کد ملی: {national_id}'))
        c.drawRightString(w - 380, y, _rtl(f'گروه کلاسی: {student_group}'))
        c.drawRightString(w - 40, y - 25, _rtl(f'تاریخ ثبت: {log_date}'))
        
        y -= 70
        bg_box = colors.HexColor('#f0fdf4') if 'تشویق' in b_type or 'مثبت' in b_type else colors.HexColor('#fef2f2')
        c.setFillColor(bg_box)
        c.rect(40, y-120, w-80, 120, fill=1, stroke=1)
        
        c.setFillColor(header_color)
        c.setFont(font_name, 12)
        c.drawRightString(w - 55, y - 30, _rtl(f'📌 عنوان مشاهده: {title}'))
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10)
        c.drawRightString(w - 55, y - 60, _rtl(f'نوع ثبت: {b_type}'))
        c.drawRightString(w - 55, y - 90, _rtl(f'توضیحات و شرح رفتار: {desc if desc else "توضیحات تکمیلی ثبت نشده است."}'))
        
        y -= 200
        c.setFont(font_name, 11)
        c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 40, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
        
        c.save()
        return buf.getvalue()
    except Exception as e:
        return f"Error generating PDF: {e}".encode('utf-8')

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
                dt = q.get('زمان ثبت', '-')
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
    except Exception as e:
        return f"Error generating PDF: {e}".encode('utf-8')

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
        c.drawCentredString(w/2, h-78, _rtl('کارنامه جامع تحصیلی و پوشه کار دیجیتال'))
        
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 11)
        y = h - 130
        c.drawRightString(w - 40, y, _rtl(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 220, y, _rtl(f'کد ملی: {national_id}'))
        c.drawRightString(w - 380, y, _rtl(f'گروه کلاسی: {student_group}'))
        
        y -= 45
        c.setFillColor(colors.HexColor('#f1f5f9'))
        c.rect(40, y-45, w-80, 45, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10)
        c.drawRightString(w - 55, y - 28, _rtl(f'تعداد ارزشیابی‌های توصیفی: {eval_count} | ثبت انضباطی: {beh_count} | میانگین آزمون‌ها: {quiz_avg_str}'))
        
        y -= 65
        c.setFillColor(colors.HexColor('#f0fdf4'))
        c.rect(40, y-170, w-80, 170, fill=1, stroke=1)
        
        c.setFillColor(colors.HexColor('#166534'))
        c.setFont(font_name, 11)
        c.drawRightString(w - 55, y - 22, _rtl('📝 خلاصه آخرین ارزشیابی‌های کیفی-توصیفی ۷ درس:'))
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 9)
        
        line_y = y - 45
        if evaluations_data:
            for ev in evaluations_data[:5]:
                sub = ev.get('درس', 'درس')
                lvl = ev.get('سطح توصیفی', '-')
                fb = ev.get('توصیف عملکرد', 'ثبت شده')
                c.drawRightString(w - 55, line_y, _rtl(f'• {sub}: {lvl} — بازخورد: {fb[:45]}'))
                line_y -= 24
        else:
            c.drawRightString(w - 55, line_y, _rtl('ارزشیابی توصیفی ثبت نشده است.'))
            
        y -= 210
        c.setFillColor(colors.HexColor('#eff6ff'))
        c.rect(40, y-80, w-80, 80, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#1e40af'))
        c.setFont(font_name, 11)
        c.drawRightString(w - 55, y - 22, _rtl('💡 تحلیل جامع تربیتی و آموزشی آموزگار (سید موسی حیدری):'))
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 9)
        c.drawRightString(w - 55, y - 45, _rtl('دانش‌آموز در فعالیت‌های کلاسی و آزمون‌های آنلاین مشارکتی فعال دارد. تمرین مستمر کسرها توصیه می‌شود.'))
        
        y -= 130
        c.setFont(font_name, 11)
        c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 40, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
        
        c.save()
        return buf.getvalue()
    except Exception as e:
        return f"Error generating PDF: {e}".encode('utf-8')

# ---------------------------------------------------------
# HEADER & AUTHENTICATION BAR
# ---------------------------------------------------------
curr_shamsi = datetime.date.today().strftime("%Y/%m/%d")

st.markdown(f"""
<div class="main-header">
    <h1>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین — پایه پنجم ابتدایی</h1>
    <p>دبستان شهید مطهری مهران | آموزگار: سید موسی حیدری | 📅 امروز: {curr_shamsi}</p>
</div>
""", unsafe_allow_html=True)

# Top Bar Auth Card (Explicit labels, zero text leakage)
col_top1, col_top2 = st.columns([3, 1])

with col_top1:
    role_choice = st.radio(
        "👤 انتخاب نقش کاربری جهت ورود:",
        ["دانش‌آموز (ورود عمومی)", "معلم / آموزگار (مدیریت)"],
        horizontal=True,
        key="role_radio"
    )
    if "دانش‌آموز" in role_choice:
        st.session_state['user_role'] = 'دانش‌آموز'
        st.session_state['is_teacher_logged_in'] = False
    else:
        st.session_state['user_role'] = 'معلم'

with col_top2:
    if st.session_state['user_role'] == 'معلم':
        if not st.session_state['is_teacher_logged_in']:
            with st.popover("🔑 ورود مدیریت آموزگار"):
                st.write("رمز عبور آموزگار را وارد کنید:")
                pass_input = st.text_input("رمز عبور آموزگار:", type="password", key="top_pass_input")
                if st.button("ورود به سیستم"):
                    if check_teacher_password(pass_input):
                        st.session_state['is_teacher_logged_in'] = True
                        st.success("🔓 ورود موفقیت‌آمیز آموزگار!")
                        st.rerun()
                    else:
                        st.error("❌ رمز عبور اشتباه است.")
        else:
            st.success("🟢 آموزگار وارد شده است")
            with st.popover("🔐 تغییر رمز عبور آموزگار"):
                old_p = st.text_input("رمز فعلی آموزگار:", type="password", key="old_p")
                new_p = st.text_input("رمز جدید آموزگار:", type="password", key="new_p")
                if st.button("ذخیره رمز جدید"):
                    if check_teacher_password(old_p):
                        if new_p:
                            update_teacher_password(new_p)
                            st.success("رمز عبور با موفقیت تغییر یافت.")
                        else:
                            st.warning("رمز جدید نمی‌تواند خالی باشد.")
                    else:
                        st.error("رمز فعلی نادرست است.")

st.markdown("---")

# ---------------------------------------------------------
# DROPDOWN NAVIGATION MENU (100% RELIABLE & COMPACT)
# ---------------------------------------------------------
if st.session_state['is_teacher_logged_in']:
    menu_options = [
        "1️⃣ 🏠 معرفی برنامه و اهداف آموزشی",
        "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌ها (۲۹ نفر)",
        "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی (ویژه معلم)",
        "4️⃣ 🌟 ثبت رفتار و انضباط (ویژه معلم)",
        "5️⃣ ✏️ آزمون‌ساز آنلاین (ویژه معلم)",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و ۳ گزارش رسمی (اولیا / معلم)"
    ]
else:
    menu_options = [
        "1️⃣ 🏠 معرفی برنامه و اهداف آموزشی",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و ۳ گزارش رسمی (اولیا / معلم)"
    ]

menu_choice = st.selectbox("📌 منوی بخش‌های سامانه (بخش مورد نظر را انتخاب کنید):", menu_options, key="main_nav_menu_sel")

def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه در کادر '🔑 ورود مدیریت آموزگار' رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

# -----------------------------------------------------------------
# 1. LANDING PAGE & WELCOME OVERVIEW
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.subheader("👋 به سامانه مدیریت هوشمند کلاس پنجم خوش آمدید")
    
    st.markdown("""
    <div class="card-box">
        <h3>🌱 طراح و توسعه‌دهنده سامانه: <b>سید موسی حیدری</b></h3>
        <p>آموزگار پایه پنجم ابتدایی — دبستان شهید مطهری مهران | سال تحصیلی ۱۴۰۴-۱۴۰۵</p>
    </div>
    
    <div class="quote-card">
        <h3 style="color: #fbbf24 !important; margin-bottom: 12px;">📜 رهنمودهای مقام معظم رهبری (حضرت آیت‌الله خامنه‌ای مدظله‌العالی) در باب فناوری و آموزش:</h3>
        <p style="font-size: 1.1rem; line-height: 1.9; color: #f8fafc !important;">
        «استفاده از ابزارهای نوين علمی و فناوری‌های هوشمند، مسیر یادگیری را برای دانش‌آموزان جذاب‌تر، عمیق‌تر و کارآمدتر می‌سازد. آموزش و پرورش ما باید مجهز به آخرین دستاوردهای علمی و تکنولوژی روز باشد تا نسل جوان ما برای آینده‌ای روشن و سراسر افتخار آماده شود.»
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.markdown("""
        <div class="card-box">
            <h3 style="color: #60a5fa !important; margin-bottom: 15px;">🎯 اهداف اصلی سامانه هوشمند کلاسی</h3>
            <ul style="font-size: 1.02rem; line-height: 2;">
                <li><b>ارتقای کیفیت یادگیری:</b> برگزاری آزمون‌های آنلاین هوشمند با تصحیح خودکار.</li>
                <li><b>شفافیت و آگاهی اولیا:</b> دسترسی خانواده‌ها به پوشه کار، ۳ گزارش PDF و نمودار رشد.</li>
                <li><b>تقویت روحیه همکاری:</b> گروه‌بندی ۲۹ دانش‌آموز در ۵ گروه متوازن و پایش رفتاری.</li>
                <li><b>ارزشیابی توصیفی:</b> ثبت دقیق عملکرد در ۷ عنوان درسی پایه پنجم.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with col_w2:
        st.markdown("""
        <div class="card-box">
            <h3 style="color: #34d399 !important; margin-bottom: 15px;">🇮🇷 مطابقت با برنامه‌های آموزش و پرورش</h3>
            <ul style="font-size: 1.02rem; line-height: 2;">
                <li><b>انطباق با سند تحول بنیادین:</b> تحقق ساحت‌های شش‌گانه تربیت اسلامی.</li>
                <li><b>ارزشیابی کیفی-توصیفی:</b> بر اساس آخرین مصوبات دفتر دبیرخانه کشوری ابتدایی.</li>
                <li><b>بودجه‌بندی امتحانات:</b> مطابق با جدول زمان‌بندی رسمی دروس پایه پنجم.</li>
                <li><b>حفظ کرامت دانش‌آموز:</b> اختصاص رمز ۴ رقمی برای حریم خصوصی پرونده‌ها.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. STUDENT PROFILES & EDIT/DELETE (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان، ثبت، ویرایش و حذف پرونده‌ها (۲۹ نفر)")
    
    tab1, tab2, tab3 = st.tabs(["📋 مشاهده، ویرایش و مدیریت اسامی", "📊 ثبت دسته‌جمعی از فایل اکسل", "➕ ثبت دانش‌آموز جدید (تکی)"])
    
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
                filtered_df = filtered_df[filtered_df['full_name'].str.contains(search_query, na=False) | filtered_df['national_id'].str.contains(search_query, na=False)]
            if selected_group_filter != "همه گروه‌ها":
                filtered_df = filtered_df[filtered_df['student_group'] == selected_group_filter]
                
            st.dataframe(filtered_df[['id', 'full_name', 'national_id', 'parent_phone', 'student_group', 'pin_code', 'notes']].rename(columns={
                'id': 'شناسه',
                'full_name': 'نام و نام خانوادگی',
                'national_id': 'کد ملی',
                'parent_phone': 'شماره اولیا',
                'student_group': 'گروه کلاسی',
                'pin_code': 'رمز اختصاصی',
                'notes': 'توضیحات'
            }), use_container_width=True, hide_index=True)
            
            st.markdown("---")
            col_ed1, col_ed2 = st.columns(2)
            
            with col_ed1:
                st.subheader("✏️ ویرایش مشخصات دانش‌آموز")
                st_list = [f"{row['id']} - {row['full_name']} (کد ملی: {row['national_id']})" for _, row in students_df.iterrows()]
                st_to_edit_str = st.selectbox("انتخاب دانش‌آموز جهت ویرایش:", st_list, key="sel_edit_st")
                edit_id = int(st_to_edit_str.split(" - ")[0])
                
                st_row = students_df[students_df['id'] == edit_id].iloc[0]
                
                with st.form(f"edit_st_form_{edit_id}"):
                    e_fn = st.text_input("نام:", value=st_row['first_name'])
                    e_ln = st.text_input("نام خانوادگی:", value=st_row['last_name'])
                    e_nid = st.text_input("کد ملی:", value=st_row['national_id'])
                    e_ph = st.text_input("شماره اولیا:", value=st_row['parent_phone'])
                    e_grp = st.selectbox("گروه کلاسی:", CLASS_GROUPS, index=CLASS_GROUPS.index(st_row['student_group']) if st_row['student_group'] in CLASS_GROUPS else 0)
                    e_pin = st.text_input("رمز اختصاصی ۴ رقمی:", value=st_row['pin_code'])
                    
                    if st.form_submit_button("💾 ذخیره تغییرات پرونده"):
                        with get_connection() as conn:
                            conn.execute("""
                                UPDATE students SET first_name=?, last_name=?, national_id=?, parent_phone=?, student_group=?, pin_code=? WHERE id=?
                            """, (e_fn.strip(), e_ln.strip(), e_nid.strip(), e_ph.strip(), e_grp, e_pin.strip(), edit_id))
                            conn.commit()
                        st.success(f"پرونده {e_fn} {e_ln} به‌روزرسانی شد.")
                        st.rerun()

            with col_ed2:
                st.subheader("🗑️ حذف پرونده دانش‌آموز")
                st_to_del_str = st.selectbox("انتخاب دانش‌آموز جهت حذف:", st_list, key="sel_del_st")
                del_id = int(st_to_del_str.split(" - ")[0])
                
                if st.button("🗑️ حذف کامل پرونده این دانش‌آموز"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM students WHERE id = ?", (del_id,))
                        conn.commit()
                    st.success("پرونده با موفقیت حذف گردید.")
                    st.rerun()
                    
                st.markdown("---")
                st.warning("⚠️ پاکسازی کامل دیتابیس دانش‌آموزان:")
                confirm_clean = st.checkbox("تایید می‌کنم که تمام اسامی دانش‌آموزان پاک شوند.")
                if st.button("🔥 پاکسازی کلی تمام اسامی") and confirm_clean:
                    with get_connection() as conn:
                        conn.execute("DELETE FROM students")
                        conn.commit()
                    st.success("تمام اسامی پاکسازی شدند.")
                    st.rerun()
        else:
            st.info("هنوز دانش‌آموزی ثبت نشده است.")

    with tab2:
        st.subheader("📊 بارگذاری دسته‌جمعی اسامی از فایل اکسل (Excel/CSV)")
        st.info("فایل اکسل باید شامل ستون‌های 'first_name' (نام) و 'last_name' (نام خانوادگی) باشد.")
        
        sample_df = pd.DataFrame({
            'first_name': ['علی', 'رضا'],
            'last_name': ['محمدی', 'حسینی'],
            'national_id': ['1001', '1002'],
            'parent_phone': ['09120000000', '09120000001'],
            'student_group': ['گروه ارمغان 🚀', 'گروه دانا 💡']
        })
        st.download_button("📥 دانلود نمونه فایل اکسل", sample_df.to_csv(index=False).encode('utf-8-sig'), "template.csv", "text/csv")
        
        uploaded_file = st.file_uploader("انتخاب فایل اکسل یا CSV:", type=["xlsx", "csv"], key=f"ex_up_{st.session_state['excel_upload_key']}")
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded_file)
                else:
                    df_up = pd.read_excel(uploaded_file)
                st.dataframe(df_up.head())
                if st.button("🚀 افزودن همگی به لیست کلاس"):
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cnt = 0
                        for idx, row in df_up.iterrows():
                            fn = str(row.get('first_name', '')).strip()
                            ln = str(row.get('last_name', '')).strip()
                            nid = str(row.get('national_id', f"100{idx+1}")).strip()
                            ph = str(row.get('parent_phone', '')).strip()
                            grp = str(row.get('student_group', CLASS_GROUPS[idx % 5])).strip()
                            if fn and ln:
                                try:
                                    cursor.execute("INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group) VALUES (?, ?, ?, ?, ?)", (fn, ln, nid, ph, grp))
                                    cnt += 1
                                except Exception: pass
                        conn.commit()
                    st.success(f"تعداد {cnt} دانش‌آموز ثبت شدند.")
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در خواندن فایل: {e}")

    with tab3:
        st.subheader("➕ ثبت دانش‌آموز جدید (تکی)")
        with st.form("add_single_st_form"):
            c_a1, c_a2 = st.columns(2)
            with c_a1:
                fn = st.text_input("نام:*")
                ln = st.text_input("نام خانوادگی:*")
                nid = st.text_input("کد ملی:")
            with c_a2:
                ph = st.text_input("شماره اولیا:")
                grp = st.selectbox("گروه آموزشی:", CLASS_GROUPS)
                pin = st.text_input("رمز اختصاصی ۴ رقمی:", value="1234")
                
            if st.form_submit_button("💾 ثبت دانش‌آموز"):
                if fn.strip() and ln.strip():
                    with get_connection() as conn:
                        try:
                            conn.execute("INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group, pin_code) VALUES (?, ?, ?, ?, ?, ?)", (fn.strip(), ln.strip(), nid.strip(), ph.strip(), grp, pin.strip()))
                            conn.commit()
                            st.success(f"دانش‌آموز {fn} {ln} ثبت شد.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("کد ملی تکراری است.")
                else:
                    st.warning("نام و نام خانوادگی الزامی است.")

# ---------------------------------------------------------
# 3. QUALITATIVE EVALUATIONS (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("لطفاً ابتدا اسامی دانش‌آموزان را ثبت کنید.")
    else:
        st_list = [f"{row['id']} - {row['full_name']} (کد ملی: {row['national_id']} | گروه: {row['student_group']})" for _, row in students_df.iterrows()]
        col1, col2 = st.columns(2)
        with col1:
            selected_st_str = st.selectbox("انتخاب دانش‌آموز:", st_list)
            selected_subject = st.selectbox("انتخاب درس:", FIFTH_GRADE_SUBJECTS)
        with col2:
            selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
            eval_date = st.date_input("تاریخ ارزشیابی:", datetime.date.today()).strftime("%Y/%m/%d")
            
        feedback_text = st.text_area("توصیف عملکرد و بازخورد آموزگار:")
        
        if st.button("💾 ثبت ارزشیابی توصیفی"):
            s_id = int(selected_st_str.split(" - ")[0])
            with get_connection() as conn:
                conn.execute("INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)", (s_id, selected_subject, selected_level, feedback_text, eval_date))
                conn.commit()
            st.success(f"ارزشیابی {selected_subject} ثبت شد.")

        st.markdown("---")
        s_id = int(selected_st_str.split(" - ")[0])
        st.subheader("📋 سوابق ارزشیابی‌های ثبت‌شده")
        with get_connection() as conn:
            eval_h = safe_read_sql("SELECT id, subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'بازخورد معلم', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,))
        if not eval_h.empty:
            st.dataframe(eval_h.drop(columns=['id']), use_container_width=True, hide_index=True)
            
            st.markdown("##### 🗑️ مدیریت و حذف ارزشیابی:")
            e_del_id = st.selectbox("انتخاب شناسه جهت حذف:", eval_h['id'].tolist(), key="del_eval_id")
            if st.button("حذف این ارزشیابی"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM evaluations WHERE id = ?", (e_del_id,))
                    conn.commit()
                st.success("ارزشیابی حذف شد.")
                st.rerun()

# ---------------------------------------------------------
# 4. BEHAVIOR & DISCIPLINE (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("4"):
    check_teacher_auth()
    st.header("🌟 مدیریت رفتار و مشاهدات انضباطی کلاسی")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("لطفاً ابتدا اسامی دانش‌آموزان را ثبت کنید.")
    else:
        st_list = [f"{row['id']} - {row['full_name']} (کد ملی: {row['national_id']} | گروه: {row['student_group']})" for _, row in students_df.iterrows()]
        col1, col2 = st.columns(2)
        with col1:
            selected_st_str = st.selectbox("انتخاب دانش‌آموز:", st_list)
            b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
        with col2:
            title = st.text_input("عنوان رفتار:")
            log_date = st.date_input("تاریخ ثبت:", datetime.date.today()).strftime("%Y/%m/%d")
            
        desc = st.text_area("جزییات و اقدامات انجام‌شده:")
        
        if st.button("💾 ثبت مشاهده رفتاری"):
            s_id = int(selected_st_str.split(" - ")[0])
            with get_connection() as conn:
                conn.execute("INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)", (s_id, b_type, title, desc, log_date))
                conn.commit()
            st.success("مشاهده رفتاری ذخیره شد.")

        st.markdown("---")
        s_id = int(selected_st_str.split(" - ")[0])
        st.subheader("📋 سوابق رفتاری این دانش‌آموز")
        with get_connection() as conn:
            beh_h = safe_read_sql("SELECT id, behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ' FROM behaviors WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,))
        if not beh_h.empty:
            st.dataframe(beh_h.drop(columns=['id']), use_container_width=True, hide_index=True)
            b_del_id = st.selectbox("انتخاب شناسه جهت حذف:", beh_h['id'].tolist(), key="del_beh_id")
            if st.button("حذف این مشاهده رفتاری"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM behaviors WHERE id = ?", (b_del_id,))
                    conn.commit()
                st.success("مشاهده رفتاری حذف شد.")
                st.rerun()

# ---------------------------------------------------------
# 5. ONLINE QUIZ CREATOR (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (۴ روش طراحی و بارگذاری سوالات)")
    
    tab_q1, tab_q_excel, tab_q_text, tab_q_json, tab_q_manage = st.tabs([
        "➕ طراحی دستی تکی", 
        "📊 بارگذاری از فایل اکسل (Excel/CSV)", 
        "📋 کپی-پیست مستقیم متن", 
        "📥 بارگذاری JSON", 
        "🗑️ مدیریت و حذف آزمون‌ها"
    ])
    
    with tab_q1:
        c1, c2, c3 = st.columns(3)
        with c1: q_title = st.text_input("عنوان آزمون:", key="q1_t")
        with c2: q_sub = st.selectbox("درس:", FIFTH_GRADE_SUBJECTS, key="q1_sub")
        with c3: q_dur = st.number_input("زمان (دقیقه):", value=60, min_value=5, key="q1_dur")
        
        num_q = st.number_input("تعداد سوالات:", min_value=1, max_value=30, value=2, key="q1_num")
        q_inputs = []
        for i in range(int(num_q)):
            st.markdown(f"**📌 سوال شماره {i+1}:**")
            qt = st.selectbox(f"نوع سوال {i+1}:", ["تستی ۴ گزینه‌ای", "تشریحی / تحلیلی"], key=f"qt_{i}")
            qtxt = st.text_area(f"متن سوال {i+1}:", key=f"qtxt_{i}")
            if qt == "تستی ۴ گزینه‌ای":
                ca, cb, cc, cd = st.columns(4)
                with ca: o1 = st.text_input(f"گزینه ۱:", key=f"o1_{i}")
                with cb: o2 = st.text_input(f"گزینه ۲:", key=f"o2_{i}")
                with cc: o3 = st.text_input(f"گزینه ۳:", key=f"o3_{i}")
                with cd: o4 = st.text_input(f"گزینه ۴:", key=f"o4_{i}")
                corr = st.selectbox(f"گزینه صحیح:", [1, 2, 3, 4], key=f"corr_{i}")
                exp = st.text_area(f"تحلیل پاسخ:", key=f"exp_{i}")
                q_inputs.append(('mcq', qtxt, o1, o2, o3, o4, corr, None, exp))
            else:
                mans = st.text_area(f"پاسخ نمونه معلم:", key=f"mans_{i}")
                exp = st.text_area(f"تحلیل آموزشی:", key=f"exp_e_{i}")
                q_inputs.append(('essay', qtxt, None, None, None, None, 1, mans, exp))
            st.markdown("---")
            
        if st.button("🚀 انتشار و فعال‌سازی آزمون"):
            if q_title.strip() and all(q[1].strip() for q in q_inputs):
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)", (q_title.strip(), q_sub, q_dur, datetime.date.today().strftime("%Y/%m/%d")))
                    qid = cursor.lastrowid
                    for q in q_inputs:
                        cursor.execute("INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (qid, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
                    conn.commit()
                st.success(f"آزمون '{q_title}' منتشر شد.")
            else:
                st.error("عنوان و تمام سوالات را وارد کنید.")

    with tab_q_excel:
        st.subheader("📊 بارگذاری فایل اکسل سوالات (Excel/CSV)")
        c_ex1, c_ex2, c_ex3 = st.columns(3)
        with c_ex1: ex_t = st.text_input("عنوان آزمون اکسل:", key="ex_t")
        with c_ex2: ex_sub = st.selectbox("درس:", FIFTH_GRADE_SUBJECTS, key="ex_sub")
        with c_ex3: ex_dur = st.number_input("زمان (دقیقه):", value=45, key="ex_dur")
        
        uploaded_q_ex = st.file_uploader("انتخاب فایل اکسل سوالات:", type=["xlsx", "csv"], key="q_ex_file")
        if uploaded_q_ex is not None:
            try:
                df_q_up = pd.read_csv(uploaded_q_ex) if uploaded_q_ex.name.endswith('.csv') else pd.read_excel(uploaded_q_ex)
                st.dataframe(df_q_up.head())
                if st.button("🚀 ساخت آزمون از اکسل"):
                    if ex_t.strip():
                        with get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)", (ex_t.strip(), ex_sub, ex_dur, datetime.date.today().strftime("%Y/%m/%d")))
                            qid = cursor.lastrowid
                            cnt = 0
                            for _, row in df_q_up.iterrows():
                                qtxt = str(row.get('متن سوال', row.get('سوال', ''))).strip()
                                o1 = str(row.get('گزینه ۱', row.get('گزینه 1', ''))).strip()
                                o2 = str(row.get('گزینه ۲', row.get('گزینه 2', ''))).strip()
                                o3 = str(row.get('گزینه ۳', row.get('گزینه 3', ''))).strip()
                                o4 = str(row.get('گزینه ۴', row.get('گزینه 4', ''))).strip()
                                try: corr = int(row.get('گزینه صحیح', 1))
                                except: corr = 1
                                if qtxt:
                                    cursor.execute("INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option) VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?)", (qid, qtxt, o1, o2, o3, o4, corr))
                                    cnt += 1
                            conn.commit()
                        st.success(f"آزمون با {cnt} سوال ساخته شد.")
            except Exception as e:
                st.error(f"خطا در خواندن فایل: {e}")

    with tab_q_text:
        st.subheader("📋 کپی-پیست مستقیم متن سوالات")
        tx_t = st.text_input("عنوان آزمون متنی:", key="tx_t")
        tx_sub = st.selectbox("درس:", FIFTH_GRADE_SUBJECTS, key="tx_sub")
        tx_dur = st.number_input("زمان (دقیقه):", value=30, key="tx_dur")
        
        sample_paste = "سوال ۱: حاصل کسر ۲/۵ + ۳/۱۰ کدام است؟ | گزینه ۱: ۷/۱۰ | گزینه ۲: ۵/۱۵ | گزینه ۳: ۱/۲ | گزینه ۴: ۴/۱۰ | پاسخ صحیح: ۱\nسوال ۲: کدام‌یک تغییر شیمیایی است؟ | گزینه ۱: ذوب یخ | گزینه ۲: تبخیر آب | گزینه ۳: سوختن چوب | گزینه ۴: خرد کردن کاغذ | پاسخ صحیح: ۳"
        pasted_txt = st.text_area("متن سوالات را پیست کنید (با | جدا کنید):", value=sample_paste, height=180)
        
        if st.button("🚀 ساخت آزمون از متن کپی شده"):
            if tx_t.strip() and pasted_txt.strip():
                lines = pasted_txt.strip().split("\n")
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)", (tx_t.strip(), tx_sub, tx_dur, datetime.date.today().strftime("%Y/%m/%d")))
                    qid = cursor.lastrowid
                    cnt = 0
                    for line in lines:
                        if not line.strip(): continue
                        parts = [p.strip() for p in line.split("|")]
                        qtxt = parts[0]
                        o1 = o2 = o3 = o4 = ""
                        corr = 1
                        for p in parts[1:]:
                            if 'گزینه ۱' in p or 'گزینه 1' in p: o1 = p.split(":")[-1].strip()
                            elif 'گزینه ۲' in p or 'گزینه 2' in p: o2 = p.split(":")[-1].strip()
                            elif 'گزینه ۳' in p or 'گزینه 3' in p: o3 = p.split(":")[-1].strip()
                            elif 'گزینه ۴' in p or 'گزینه 4' in p: o4 = p.split(":")[-1].strip()
                            elif 'پاسخ صحیح' in p or 'گزینه صحیح' in p:
                                try: corr = int(p.split(":")[-1].strip())
                                except: corr = 1
                        cursor.execute("INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option) VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?)", (qid, qtxt, o1, o2, o3, o4, corr))
                        cnt += 1
                    conn.commit()
                st.success(f"آزمون متنی با {cnt} سوال ایجاد شد.")

    with tab_q_json:
        st.subheader("📥 بارگذاری از فایل JSON")
        uploaded_json = st.file_uploader("انتخاب فایل JSON:", type=["json"])
        if uploaded_json is not None:
            try:
                data = json.load(uploaded_json)
                if st.button("🚀 انتشار آزمون از JSON"):
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)", (data.get('title', 'آزمون JSON'), data.get('subject', 'ریاضی'), data.get('duration_minutes', 60), datetime.date.today().strftime("%Y/%m/%d")))
                        qid = cursor.lastrowid
                        for q in data.get('questions', []):
                            cursor.execute("INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (qid, q.get('question_type', 'mcq'), q.get('question_text', ''), q.get('option_1', ''), q.get('option_2', ''), q.get('option_3', ''), q.get('option_4', ''), q.get('correct_option', 1), q.get('model_answer', ''), q.get('explanation', '')))
                        conn.commit()
                    st.success("آزمون JSON منتشر شد.")
            except Exception as e:
                st.error(f"خطا در پردازش JSON: {e}")

    with tab_q_manage:
        st.subheader("🗑️ مدیریت و حذف آزمون‌ها")
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id AS 'شناسه', title AS 'عنوان آزمون', subject AS 'درس', duration_minutes AS 'زمان', created_at AS 'تاریخ' FROM quizzes ORDER BY id DESC", conn)
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True, hide_index=True)
            q_del_id = st.selectbox("انتخاب آزمون جهت حذف:", quizzes_df['شناسه'].tolist(), key="q_del_id")
            if st.button("🗑️ حذف کامل این آزمون"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM quizzes WHERE id = ?", (q_del_id,))
                    conn.commit()
                st.success("آزمون حذف گردید.")
                st.rerun()

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
        st_list = [f"{row['id']} - {row['full_name']} (کد ملی: {row['national_id']} | گروه: {row['student_group']})" for _, row in students_df.iterrows()]
        col1, col2 = st.columns(2)
        with col1:
            selected_st_str = st.selectbox("نام دانش‌آموز (خود را انتخاب کنید):", st_list)
        with col2:
            quiz_name = st.selectbox("انتخاب آزمون آنلاین:", quizzes_df['title'].tolist())
            
        s_id = int(selected_st_str.split(" - ")[0])
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
                
            student_mcq_ans = {}
            student_essay_ans = {}
            
            st.markdown("---")
            with st.form("take_quiz_form_v57"):
                for idx, q in enumerate(questions):
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
                photo = st.camera_input("لطفاً چهره خود را جلوی دوربین تنظیم کرده و عکس بگیرید:")
                
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
# 7. DASHBOARD & 3 INDEPENDENT OFFICIAL PDF REPORTS
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد تحلیلی و ۳ گزارش رسمی PDF (پوشه کار دانش‌آموز)")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("هیچ دانش‌آموزی در سیستم ثبت نشده است.")
    else:
        st_list = [f"{row['id']} - {row['full_name']} (کد ملی: {row['national_id']} | گروه: {row['student_group']})" for _, row in students_df.iterrows()]
        selected_st_str = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار و گزارشات:", st_list)
        s_id = int(selected_st_str.split(" - ")[0])
        st_info = students_df[students_df['id'] == s_id].iloc[0]
        
        # Privacy Pin Guard
        if not st.session_state['is_teacher_logged_in']:
            real_pin = str(st_info['pin_code']).strip() if st_info['pin_code'] else '1234'
            st.info("🔒 جهت حفظ حریم خصوصی، مشاهده پرونده مستلزم ورود رمز ۴ رقمی اختصاصی دانش‌آموز می‌باشد.")
            input_pin = st.text_input("🔑 رمز ۴ رقمی اختصاصی دانش‌آموز را وارد کنید:", type="password", key="port_pin_guard")
            if input_pin.strip() != real_pin:
                st.warning("⚠️ لطفاً رمز اختصاصی ۴ رقمی دانش‌آموز را وارد نمایید.")
                st.stop()
            else:
                st.success("🔓 احراز هویت دانش‌آموز موفقیت‌آمیز بود.")
                
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg_str = f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون"
            
            df_e = safe_read_sql("SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,))
            df_b = safe_read_sql("SELECT behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ' FROM behaviors WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,))
            df_q = safe_read_sql("""
                SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات تستی', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت'
                FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.id DESC
            """, conn, params=(s_id,))

        st.markdown(f"""
        <div class="card-box">
            <h3 style="margin:0; color:#60a5fa !important;">پرونده تحصیلی: <b>{st_info['full_name']}</b></h3>
            <p style="margin-top:8px; margin-bottom:0;">
                <b>کد ملی:</b> {st_info['national_id']} | <b>گروه آموزشی:</b> {st_info['student_group']} | <b>شماره اولیا:</b> {st_info['parent_phone']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with c2: st.metric("موارد رفتاری ثبت‌شده:", beh_count)
        with c3: st.metric("میانگین درصد آزمون آنلاین:", quiz_avg_str)
        
        st.markdown("---")
        
        # ---------------------------------------------------------
        # 3 INDEPENDENT REPORTS WITH ONLINE PREVIEW & PDF DOWNLOAD
        # ---------------------------------------------------------
        st.subheader("📥 صدور و دانلود ۳ گزارش رسمی PDF مستقل (با پیش‌نمایش آنلاین):")
        
        rep_tab1, rep_tab2, rep_tab3 = st.tabs([
            "🌟 ۱. گزارش پایش رفتاری", 
            "📊 ۲. گزارش تحلیلی آزمون‌ها", 
            "🎓 ۳. کارنامه جامع تحصیلی"
        ])
        
        # Report 1: Behavioral
        with rep_tab1:
            st.markdown("#### 🌟 پیش‌نمایش آنلاین گزارش پایش رفتاری و انضباطی")
            if not df_b.empty:
                st.dataframe(df_b, use_container_width=True, hide_index=True)
                last_b = df_b.iloc[0]
                b_type_str = last_b['نوع']
                b_title_str = last_b['عنوان']
                b_desc_str = last_b['شرح']
                b_date_str = last_b['تاریخ']
            else:
                st.info("سوابق رفتاری ثبت نشده است. گزارش با الگوی پایه آماده گردیده است.")
                b_type_str, b_title_str, b_desc_str, b_date_str = "تشویق / رفتار مثبت 🟢", "انضباط و مشارکت عالی", "حضور فعال در فعالیت‌های گروهی کلاسی", curr_shamsi
                
            pdf_b_bytes = generate_behavior_pdf(st_info['full_name'], st_info['national_id'], st_info['student_group'], b_type_str, b_title_str, b_desc_str, b_date_str)
            st.download_button(
                "📥 دانلود فایل رسمی PDF گزارش رفتاری (جهت پرینت)",
                data=pdf_b_bytes,
                file_name=f"behavior_report_{st_info['full_name']}.pdf",
                mime="application/pdf"
            )

        # Report 2: Online Exams & Progress Chart
        with rep_tab2:
            st.markdown("#### 📊 پیش‌نمایش آنلاین گزارش آزمون‌ها و نمودار رشد نمرات")
            if not df_q.empty:
                st.dataframe(df_q, use_container_width=True, hide_index=True)
                st.markdown("##### 📈 نمودار روند صعودی / نزولی نمرات آزمون‌ها:")
                df_chart = df_q[['عنوان آزمون', 'درصد ٪']].iloc[::-1]
                st.line_chart(df_chart.set_index('عنوان آزمون'))
                quizzes_list_data = df_q.to_dict(orient='records')
            else:
                st.info("نتیجه آزمون آنلاینی ثبت نشده است.")
                quizzes_list_data = []
                
            pdf_q_bytes = generate_exams_pdf(st_info['full_name'], st_info['national_id'], st_info['student_group'], quizzes_list_data, quiz_avg_str)
            st.download_button(
                "📥 دانلود فایل رسمی PDF گزارش آزمون‌ها (جهت پرینت)",
                data=pdf_q_bytes,
                file_name=f"exams_report_{st_info['full_name']}.pdf",
                mime="application/pdf"
            )

        # Report 3: Comprehensive Portfolio
        with rep_tab3:
            st.markdown("#### 🎓 پیش‌نمایش آنلاین کارنامه جامع تحصیلی و پوشه کار نهایی")
            
            with st.expander("👁️ مشاهده برگه رسمی کارنامه آنلاین (نمایش مستقیم درون سامانه)", expanded=True):
                st.markdown(f"""
                <div style="background:#ffffff; color:#0f172a; padding:25px; border-radius:12px; border:2px solid #2563eb; line-height:1.8;">
                    <div style="text-align:center; border-bottom:2px solid #2563eb; padding-bottom:12px; margin-bottom:15px;">
                        <h3 style="color:#1e3a8a !important; margin:0;">جمهوری اسلامی ایران - وزارت آموزش و پرورش</h3>
                        <h4 style="color:#1e3a8a !important; margin:4px 0;">دبستان پسرانه شهید مطهری مهران - پایه پنجم</h4>
                        <h4 style="color:#2563eb !important; margin:0;">کارنامه جامع تحصیلی و پوشه کار دیجیتال (سال تحصیلی ۱۴۰۴-۱۴۰۵)</h4>
                    </div>
                    <p style="color:#0f172a !important;"><b>نام دانش‌آموز:</b> {st_info['full_name']} | <b>کد ملی:</b> {st_info['national_id']} | <b>گروه آموزشی:</b> {st_info['student_group']}</p>
                    <p style="color:#0f172a !important;"><b>خلاصه عملکرد:</b> تعداد ارزشیابی توصیفی: {eval_count} | موارد رفتاری: {beh_count} | میانگین آزمون‌ها: {quiz_avg_str}</p>
                    <hr style="border-top:1px solid #cbd5e1;">
                    <h5 style="color:#1e40af !important;">📝 آخرین سوابق ارزشیابی کیفی-توصیفی ۷ درس:</h5>
                """, unsafe_allow_html=True)
                
                if not df_e.empty:
                    st.dataframe(df_e, use_container_width=True, hide_index=True)
                    evals_list_data = df_e.to_dict(orient='records')
                else:
                    st.info("ارزشیابی توصیفی ثبت نشده است.")
                    evals_list_data = []
                    
                st.markdown(f"""
                    <div style="background:#eff6ff; padding:15px; border-radius:8px; border-right:5px solid #2563eb; margin-top:15px;">
                        <h5 style="color:#1e40af !important; margin:0;">💡 تحلیل جامع تربیتی و آموزشی آموزگار (سید موسی حیدری):</h5>
                        <p style="color:#0f172a !important; margin-top:6px; margin-bottom:0;">
                            دانش‌آموز محترم در کلاس و آزمون‌های آنلاین مشارکتی عالی دارد. تمرین مستمر کسرها و ریاضی در منزل توصیه می‌شود.
                        </p>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-top:30px; text-align:center; font-weight:bold; color:#0f172a;">
                        <div>آموزگار پایه پنجم: سید موسی حیدری</div>
                        <div>مدیریت دبستان شهید مطهری مهران</div>
                        <div>رویت و امضای اولیای محترم</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            pdf_p_bytes = generate_portfolio_pdf(st_info['full_name'], st_info['national_id'], st_info['student_group'], eval_count, beh_count, quiz_avg_str, evals_list_data)
            st.download_button(
                "📥 دانلود فایل رسمی PDF کارنامه جامع تحصیلی (جهت پرینت و بایگانی)",
                data=pdf_p_bytes,
                file_name=f"comprehensive_portfolio_{st_info['full_name']}.pdf",
                mime="application/pdf"
            )


