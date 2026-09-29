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
# Page Configuration & Clean Persian RTL CSS Styling (v58 Exact)
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Persian / RTL CSS Styling & Fixes (Safe v58 Theme)
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    /* Global Typography & Font (Safe - No Wildcard div/span) */
    html, body, [class*="st-"], .stMarkdown, p, button, input, select, textarea, label, h1, h2, h3, h4, h5, h6 {
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
    
    /* Fast & Stylish Sidebar Radio Navigation (v58 Signature Menu) */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-left: 2px solid #1e293b !important;
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: #ffffff !important;
        padding: 12px 16px !important;
        border-radius: 10px !important;
        margin-bottom: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: #2563eb !important;
        border-color: #60a5fa !important;
        transform: translateX(-3px);
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        border: 2px solid #60a5fa !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4) !important;
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.02rem !important;
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
    
    /* BaseWeb Selectbox & Dropdown Popover Styling */
    input, select, textarea {
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
# Database Initialization & Auto Schema Migration
# ---------------------------------------------------------
DB_FILE = "class_management.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Students Table
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
        
        # Evaluations Table
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
        
        # Behaviors Table
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
        
        # Quizzes Table
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
        
        # Questions Table
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
        
        # Quiz Results Table
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
        
        # Teacher Auth Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_auth (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            password TEXT NOT NULL
        )
        """)
        cursor.execute("INSERT OR IGNORE INTO teacher_auth (id, password) VALUES (1, '1234')")
        
        # Migrations for existing databases
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

# Safe Read Helper
def safe_read_sql(query, conn, params=None):
    try:
        return pd.read_sql_query(query, conn, params=params)
    except Exception:
        init_db()
        try:
            return pd.read_sql_query(query, conn, params=params)
        except Exception:
            return pd.DataFrame()

# ---------------------------------------------------------
# Default Quiz Seeder
# ---------------------------------------------------------
def seed_default_quiz():
    with get_connection() as conn:
        q_count = conn.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]
        if q_count == 0:
            shamsi_today = get_current_shamsi_date()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                ("آزمون جامع ریاضی و علوم پایه پنجم (مهرماه)", "ریاضی", 20, shamsi_today)
            )
            quiz_id = cursor.lastrowid
            
            sample_questions = [
                ("عدد ۵,۴۳۲,۱۰۹ شامل چند میلیون است؟", "۵ میلیون", "۴ میلیون", "۵۰ میلیون", "۵۴ میلیون", 1, "مقام میلیون رقم ۵ می‌باشد."),
                ("کدام کسر با ۳/۴ مساوی است؟", "۶/۸", "۵/۶", "۹/۱۲", "الف و ج صحیح است", 4, "با ضرب صورت و مخرج در ۲ یا ۳ کسرهای مساوی ساخته می‌شوند."),
                ("واحد اصلی اندازه‌گیری حجم چیست؟", "متر مربع", "متر مکعب", "لیتر", "ب و ج", 4, "متر مکعب و لیتر واحدهای حجم هستند."),
                ("نقش اصلی گلبول‌های قرمز در خون چیست؟", "دفاع از بدن", "اکسیژن‌رسانی", "انعقاد خون", "تغذیه سلول‌ها", 2, "گلبول قرمز حاوی هموگلوبین برای حمل اکسیژن است."),
                ("کدام گزینه از مصادیق تغییر شیمیایی است؟", "تبخیر آب", "پختن نان", "ذوب یخ", "خرد کردن چوب", 2, "پختن نان تغییر شیمیایی است و جنس ماده تغییر می‌کند.")
            ]
            
            for q_text, o1, o2, o3, o4, corr, exp in sample_questions:
                cursor.execute(
                    "INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, explanation) VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?, ?)",
                    (quiz_id, q_text, o1, o2, o3, o4, corr, exp)
                )
            conn.commit()

seed_default_quiz()

# ---------------------------------------------------------
# ReportLab Native PDF & Chart Helper Functions
# ---------------------------------------------------------
def generate_chart_b64(quiz_titles, quiz_pcts, eval_counts):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.2), facecolor='#ffffff')
        
        if quiz_titles:
            ax1.barh(quiz_titles, quiz_pcts, color='#2563eb', edgecolor='#1e3a8a')
            ax1.set_xlim(0, 100)
            ax1.set_title('درصد آزمون‌های آنلاین', fontsize=10, fontweight='bold', color='#1e3a8a')
            ax1.grid(axis='x', linestyle='--', alpha=0.5)
        else:
            ax1.text(0.5, 0.5, 'آزمونی ثبت نشده است', ha='center', va='center', fontsize=9, color='#64748b')
            ax1.set_axis_off()

        labels = list(eval_counts.keys())
        values = list(eval_counts.values())
        colors_pie = ['#16a34a', '#2563eb', '#eab308', '#dc2626']
        
        if sum(values) > 0:
            ax2.pie(values, labels=labels, autopct='%1.0f%%', colors=colors_pie, startangle=90, textprops={'fontsize': 8})
            ax2.set_title('توزیع ارزشیابی‌های کیفی', fontsize=10, fontweight='bold', color='#1e3a8a')
        else:
            ax2.text(0.5, 0.5, 'ارزشیابی ثبت نشده است', ha='center', va='center', fontsize=9, color='#64748b')
            ax2.set_axis_off()

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        return io.BytesIO(buf.getvalue())
    except Exception:
        return None

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

def generate_reportlab_behavior_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    has_rl, A4, canvas, pdfmetrics, TTFont, HexColor = _get_reportlab()
    if not has_rl:
        return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    
    _register_persian_font()
    font_name = 'PersianFont' if _PERSIAN_FONT_REGISTERED else 'Helvetica'
    
    is_positive = 'مثبت' in str(b_type) or 'تشویق' in str(b_type)
    theme_color = HexColor('#15803d') if is_positive else HexColor('#b91c1c')
    bg_color = HexColor('#f0fdf4') if is_positive else HexColor('#fef2f2')
    report_title = 'تقدیرنامه و لوح سپاس انضباطی کلاسی' if is_positive else 'کارت اطلاع‌رسانی و هشدار انضباطی اولیا'
    
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    
    # Header
    c.setFillColor(theme_color)
    c.rect(0, h-85, w, 85, fill=1, stroke=0)
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(font_name, 14)
    c.drawCentredString(w/2, h-35, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
    c.setFont(font_name, 11)
    c.drawCentredString(w/2, h-55, _rtl('دبستان پسرانه هیئت امنایی شهید مطهری مهران'))
    c.setFont(font_name, 12)
    c.drawCentredString(w/2, h-75, _rtl(report_title))
    
    # Body Box
    y = h - 130
    c.setFillColor(bg_color)
    c.rect(40, y-260, w-80, 260, fill=1, stroke=1)
    
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 11)
    c.drawRightString(w - 60, y - 30, _rtl(f'نام دانش‌آموز: {student_name}'))
    c.drawRightString(w - 240, y - 30, _rtl(f'کد ملی: {national_id}'))
    c.drawRightString(w - 400, y - 30, _rtl(f'تاریخ ثبت: {log_date}'))
    
    c.drawRightString(w - 60, y - 70, _rtl(f'عنوان مشاهده رفتاری: {title}'))
    c.drawRightString(w - 60, y - 100, _rtl('توضیحات آموزگار:'))
    c.setFont(font_name, 10)
    c.drawRightString(w - 60, y - 125, _rtl(str(desc)[:80]))
    if len(str(desc)) > 80:
        c.drawRightString(w - 60, y - 145, _rtl(str(desc)[80:160]))
        
    # Signatures
    y -= 320
    c.setFont(font_name, 11)
    c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
    if is_positive:
        c.drawRightString(180, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
    else:
        c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
        
    c.save()
    return buf.getvalue()

def generate_reportlab_portfolio_pdf(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str):
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
    c.rect(0, h-90, w, 90, fill=1, stroke=0)
    
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(font_name, 14)
    c.drawCentredString(w/2, h-35, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
    c.setFont(font_name, 11)
    c.drawCentredString(w/2, h-55, _rtl('دبستان پسرانه هیئت امنایی شهید مطهری مهران - پایه پنجم'))
    c.setFont(font_name, 13)
    c.drawCentredString(w/2, h-78, _rtl('کارنامه جامع تحصیلی و پوشه کار دیجیتال'))
    
    # Student Info
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 11)
    y = h - 130
    c.drawRightString(w - 40, y, _rtl(f'نام دانش‌آموز: {student_name}'))
    c.drawRightString(w - 220, y, _rtl(f'کد ملی: {national_id}'))
    c.drawRightString(w - 380, y, _rtl(f'گروه کلاسی: {student_group}'))
    
    # Summary Box
    y -= 50
    c.setFillColor(HexColor('#f1f5f9'))
    c.rect(40, y-60, w-80, 60, fill=1, stroke=1)
    
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 11)
    c.drawRightString(w - 60, y - 35, _rtl(f'تعداد ارزشیابی‌ها: {eval_count}'))
    c.drawRightString(w - 240, y - 35, _rtl(f'موارد رفتاری: {beh_count}'))
    c.drawRightString(w - 420, y - 35, _rtl(f'میانگین درصد آزمون‌ها: {quiz_avg_str}'))
    
    # Analysis & Advice Box
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
    
    # Signatures
    y -= 180
    c.setFont(font_name, 11)
    c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
    c.drawRightString(w/2 + 40, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
    c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
    
    c.save()
    return buf.getvalue()

def generate_behavior_report_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    return generate_reportlab_behavior_pdf(student_name, national_id, student_group, b_type, title, desc, log_date)

def generate_portfolio_report_html(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str):
    shamsi_today = get_current_shamsi_date()
    return f"""
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 2px solid #3b82f6; border-radius: 14px; padding: 20px; color: #ffffff; margin-bottom: 20px;">
        <div style="text-align: center; border-bottom: 2px solid #3b82f6; padding-bottom: 12px; margin-bottom: 15px;">
            <h3 style="color: #60a5fa; margin: 0;">جمهوری اسلامی ایران - وزارت آموزش و پرورش</h3>
            <h4 style="color: #f1f5f9; margin: 5px 0;">دبستان پسرانه هیئت امنایی شهید مطهری مهران - پایه پنجم</h4>
            <h4 style="color: #fbbf24; margin: 5px 0;">📄 کارنامه جامع تحصیلی و پوشه کار دیجیتال</h4>
        </div>
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; background: rgba(255,255,255,0.08); padding: 12px; border-radius: 8px; font-size: 0.95rem; margin-bottom: 15px;">
            <div><b>نام دانش‌آموز:</b> {student_name}</div>
            <div><b>کد ملی:</b> {national_id}</div>
            <div><b>گروه کلاسی:</b> {student_group}</div>
            <div><b>شماره اولیا:</b> {parent_phone}</div>
            <div><b>تاریخ صدور:</b> {shamsi_today}</div>
        </div>
        <div style="display: flex; justify-content: space-around; background: rgba(37,99,235,0.2); padding: 12px; border-radius: 8px; text-align: center; font-size: 1rem; border: 1px solid #2563eb;">
            <div>📌 <b>ارزشیابی‌های درسی:</b> {eval_count} مورد</div>
            <div>🌟 <b>مشاهدات رفتاری:</b> {beh_count} مورد</div>
            <div>✏️ <b>میانگین درصد آزمون:</b> {quiz_avg_str}</div>
        </div>
    </div>
    """

def generate_comprehensive_portfolio_pdf(student_id):
    with get_connection() as conn:
        st_row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        if not st_row:
            return b""
        student_name = f"{st_row['first_name']} {st_row['last_name']}"
        national_id = st_row['national_id'] or "ثبت نشده"
        parent_phone = st_row['parent_phone'] or "ثبت نشده"
        student_group = st_row['student_group'] or "بدون گروه"
        
        eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (student_id,)).fetchone()[0]
        beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (student_id,)).fetchone()[0]
        quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (student_id,)).fetchone()[0]
        quiz_avg_str = f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون"

    return generate_reportlab_portfolio_pdf(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str)

# Helper Functions & Constants
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
        df = safe_read_sql("SELECT id, first_name || ' ' || last_name AS full_name, national_id, pin_code, parent_phone, student_group, notes FROM students", conn)
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
    st.session_state['excel_upload_key'] = 1

# ---------------------------------------------------------
# HEADER BANNER & AUTHENTICATION BAR
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین</h2>
    <p>دبستان پسرانه هیئت امنایی شهید مطهری مهران | سال تحصیلی ۱۴۰۴-۱۴۰۵</p>
    <p style="font-size: 0.9rem; opacity: 0.9; margin-top: 5px;">👨‍🏫 آموزگار پایه پنجم: <b>سید موسی حیدری</b></p>
</div>
""", unsafe_allow_html=True)

col_top1, col_top2 = st.columns([2, 1])

with col_top1:
    st.session_state['user_role'] = st.radio(
        "نقش کاربری جهت ورود به سامانه:",
        ["دانش‌آموز / اولیا 👨‍🎓", "آموزگار پایه پنجم 👨‍🏫"],
        horizontal=True,
        key="role_radio"
    )

with col_top2:
    if st.session_state['user_role'] == "آموزگار پایه پنجم 👨‍🏫":
        if not st.session_state['is_teacher_logged_in']:
            with st.form("teacher_login_form"):
                pwd_input = st.text_input("🔑 رمز ورود معلم:", type="password", placeholder="رمز عبور پیش‌فرض: 1234")
                if st.form_submit_button("ورود به پنل معلم"):
                    if check_teacher_password(pwd_input.strip()):
                        st.session_state['is_teacher_logged_in'] = True
                        st.success("ورود موفقیت‌آمیز آموزگار!")
                        st.rerun()
                    else:
                        st.error("رمز عبور اشتباه است.")
        else:
            st.success("🟢 پنل آموزگار فعال است.")
            if st.button("خروج از حساب معلم"):
                st.session_state['is_teacher_logged_in'] = False
                st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# SIDEBAR NAVIGATION (v58 Exact Radio Menu)
# ---------------------------------------------------------
if st.session_state['is_teacher_logged_in']:
    MENU_OPTIONS = [
        "1️⃣ 🏠 معرفی سامانه و اهداف آموزشی",
        "2️⃣ 👨‍🎓 مدیریت پرونده دانش‌آموزان و گروه‌ها",
        "3️⃣ 📝 ارزشیابی توصیفی و کیفی دروس",
        "4️⃣ 🌟 ثبت مشاهدات رفتاری و انضباطی",
        "5️⃣ ✏️ طراحی و مدیریت آزمون‌های آنلاین",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع"
    ]
else:
    MENU_OPTIONS = [
        "1️⃣ 🏠 معرفی سامانه و اهداف آموزشی",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع"
    ]

st.sidebar.markdown("### 📌 منوی مدیریت سامانه")
menu_choice = st.sidebar.radio(
    "انتخاب بخش:",
    MENU_OPTIONS,
    index=0,
    key="single_fast_nav_radio"
)

# Teacher Auth Guard Helper
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
        <p>این سامانه بوم‌سازی‌شده جهت تسهیل مدیریت امور آموزشی، ثبت ارزشیابی‌های کیفی-توصیفی ۷ عنوان درسی، پیگیری رفتاری و برگزاری آزمون‌های آنلاین با تصحیح هوشمند برای دانش‌آموزان پایه پنجم دبستان شهید مطهری مهران طراحی گردیده است.</p>
    </div>
    """, unsafe_allow_html=True)
    
    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        st.info("📊 **ثبت ارزشیابی ۷ درس:** ریاضی، علوم، فارسی، نگارش، مطالعات، هدیه‌ها و قرآن")
    with c_m2:
        st.success("📱 **آزمون آنلاین هوشمند:** برگزاری آزمون‌های تستی با کارنامه آنی دانش‌آموز")
    with c_m3:
        st.warning("📋 **پوشه کار دیجیتال:** صدور کارنامه جامع و گزارش‌های رسمی PDF")

# ---------------------------------------------------------
# 2. STUDENT MANAGEMENT PAGE (STUDENTS & GROUPS)
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت پرونده دانش‌آموزان و گروه‌بندی (۲۹ نفر)")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 لیست دانش‌آموزان و گروه‌ها",
        "✏️ ویرایش کامل اطلاعات دانش‌آموز",
        "🗑️ حذف پرونده دانش‌آموز",
        "📊 ثبت دسته‌جمعی از اکسل",
        "➕ ثبت دانش‌آموز جدید (تکی)"
    ])

    with tab1:
        students_df = load_students()
        if not students_df.empty:
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام یا کد ملی):")
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
                'pin_code': 'رمز ۴ رقمی',
                'parent_phone': 'شماره همراه اولیا',
                'student_group': 'گروه کلاسی',
                'notes': 'ملاحظات پرونده'
            }), use_container_width=True, hide_index=True)
        else:
            st.info("هنوز هیچ دانش‌آموزی ثبت نشده است. از زبانه 'ثبت دسته‌جمعی از اکسل' استفاده کنید.")

    with tab2:
        st.subheader("✏️ ویرایش کامل مشخصات دانش‌آموز")
        students_df = load_students()
        if not students_df.empty:
            sel_st_edit = st.selectbox("دانش‌آموز مورد نظر جهت ویرایش را انتخاب کنید:", students_df['full_name'].tolist(), key="tab_edit_sel")
            s_row = students_df[students_df['full_name'] == sel_st_edit].iloc[0]
            s_id = int(s_row['id'])

            with get_connection() as conn:
                full_rec = conn.execute("SELECT * FROM students WHERE id = ?", (s_id,)).fetchone()

            with st.form("edit_student_full_form"):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    e_fn = st.text_input("نام:*", value=full_rec['first_name'])
                    e_nid = st.text_input("کد ملی:", value=full_rec['national_id'] or "")
                    e_grp = st.selectbox("گروه کلاسی:", CLASS_GROUPS, index=CLASS_GROUPS.index(full_rec['student_group']) if full_rec['student_group'] in CLASS_GROUPS else 0)
                with col_e2:
                    e_ln = st.text_input("نام خانوادگی:*", value=full_rec['last_name'])
                    e_pin = st.text_input("رمز ۴ رقمی اختصاصی:", value=full_rec['pin_code'] or "1234")
                    e_ph = st.text_input("شماره همراه اولیا:", value=full_rec['parent_phone'] or "")

                e_notes = st.text_area("ملاحظات پرونده / آموزشی / پزشکی:", value=full_rec['notes'] or "")

                if st.form_submit_button("💾 ذخیره تغییرات ویرایش‌یافته"):
                    if e_fn.strip() and e_ln.strip():
                        with get_connection() as conn:
                            conn.execute("""
                                UPDATE students 
                                SET first_name = ?, last_name = ?, national_id = ?, pin_code = ?, parent_phone = ?, student_group = ?, notes = ?
                                WHERE id = ?
                            """, (e_fn.strip(), e_ln.strip(), e_nid.strip(), e_pin.strip(), e_ph.strip(), e_grp, e_notes.strip(), s_id))
                            conn.commit()
                        st.success(f"اطلاعات دانش‌آموز '{e_fn} {e_ln}' با موفقیت ویرایش شد.")
                        st.rerun()
                    else:
                        st.error("نام و نام خانوادگی نمی‌تواند خالی باشد.")
        else:
            st.info("دانش‌آموزی برای ویرایش وجود ندارد.")

    with tab3:
        st.subheader("🗑️ حذف تکی و دسته‌جمعی پرونده دانش‌آموزان")
        students_df = load_students()
        if not students_df.empty:
            st.markdown("##### 📌 ۱. حذف تکی یک دانش‌آموز")
            student_options = [f"{row['id']} - {row['full_name']} ({row['national_id'] or 'بدون کد ملی'})" for _, row in students_df.iterrows()]
            sel_st_del_str = st.selectbox("دانش‌آموز مورد نظر جهت حذف را انتخاب کنید:", student_options, key="tab_del_sel_str")
            s_id_del = int(sel_st_del_str.split(" - ")[0])
            st_name_only = sel_st_del_str.split(" - ")[1].split(" (")[0]

            st.warning(f"⚠️ **هشدار:** آیا از حذف کامل پرونده **{st_name_only}** اطمینان دارید؟ تمام سوابق تحصیلی، ارزشیابی‌ها، موارد رفتاری و نمرات آزمون‌های این دانش‌آموز نیز حذف خواهند شد.")

            if st.button("🗑️ حذف قطعی پرونده این دانش‌آموز", key="btn_single_del_exec"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM evaluations WHERE student_id = ?", (s_id_del,))
                    conn.execute("DELETE FROM behaviors WHERE student_id = ?", (s_id_del,))
                    conn.execute("DELETE FROM quiz_results WHERE student_id = ?", (s_id_del,))
                    conn.execute("DELETE FROM students WHERE id = ?", (s_id_del,))
                    conn.commit()
                st.success(f"🎉 پرونده دانش‌آموز {st_name_only} با موفقیت و به‌طور کامل پاکسازی گردید.")
                st.rerun()

            st.markdown("---")
            st.markdown("##### 🔥 ۲. حذف دسته‌جمعی / کلی تمامی دانش‌آموزان")
            st.error("⚠️ **هشدار بسیار مهم:** این عملیات غیرقابل بازگشت است و تمام دانش‌آموزان ثبت‌شده همراه با کلیه نمرات، ارزشیابی‌ها و سوابق رفتاری به صورت یکجا پاکسازی خواهند شد.")
            confirm_bulk = st.checkbox("تایید می‌کنم که قصد پاکسازی کامل کلیه اسامی و سوابق دانش‌آموزان را دارم.", key="chk_bulk_del")
            if st.button("🔥 حذف کلی و پاکسازی کامل لیست دانش‌آموزان", key="btn_bulk_del", disabled=not confirm_bulk):
                with get_connection() as conn:
                    conn.execute("DELETE FROM evaluations")
                    conn.execute("DELETE FROM behaviors")
                    conn.execute("DELETE FROM quiz_results")
                    conn.execute("DELETE FROM students")
                    conn.commit()
                st.success("🎉 لیست تمامی دانش‌آموزان و کلیه سوابق آن‌ها با موفقیت به طور کامل پاکسازی گردید.")
                st.rerun()
        else:
            st.info("دانش‌آموزی جهت حذف وجود ندارد.")

    with tab4:
        st.subheader("📊 بارگذاری دسته‌جمعی ۲۹ دانش‌آموز از فایل اکسل (در ۱ ثانیه)")
        
        # Fast Database Purge Box
        st.markdown("""
        <div style="background: rgba(220, 38, 38, 0.15); border: 1px solid #ef4444; border-radius: 10px; padding: 15px; margin-bottom: 18px;">
            <h5 style="color: #fca5a5; margin-top: 0;">💥 پاکسازی دیتابیس پیش از بارگذاری اکسل جدید:</h5>
            <p style="font-size: 0.9rem; color: #f8fafc;">اگر قصد دارید تمام اسامی و سوابق قبلی را پاک کنید تا فایل جدید ۲۹ دانش‌آموز جایگزین شود، از دکمه زیر استفاده کنید:</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("💥 پاکسازی فوری تمام دانش‌آموزان قبلی", key="btn_purge_before_excel"):
            with get_connection() as conn:
                conn.execute("DELETE FROM evaluations")
                conn.execute("DELETE FROM behaviors")
                conn.execute("DELETE FROM quiz_results")
                conn.execute("DELETE FROM students")
                conn.commit()
            st.success("🎉 تمامی دانش‌آموزان قبلی با موفقیت پاکسازی شدند. اکنون فایل اکسل جدید را آپلود کنید.")
            st.rerun()

        st.info("فایل اکسل باید شامل ستون‌های 'نام'، 'نام خانوادگی'، 'کد ملی'، 'شماره همراه اولیا' و 'گروه کلاسی' باشد.")

        sample_df = pd.DataFrame([
            {"نام": "امیرعلی", "نام خانوادگی": "احمدی", "کد ملی": "1001112233", "رمز اختصاصی": "1234", "شماره همراه اولیا": "09181111111", "گروه کلاسی": "گروه ارمغان 🚀"},
            {"نام": "محمدیاسین", "نام خانوادگی": "حیدری", "کد ملی": "1002223344", "رمز اختصاصی": "1234", "شماره همراه اولیا": "09182222222", "گروه کلاسی": "گروه دانا 💡"}
        ])

        st.download_button(
            "📥 دانلود فایل اکسل الگوی اسامی دانش‌آموزان",
            sample_df.to_csv(index=False).encode('utf-8-sig'),
            "students_template.csv",
            "text/csv"
        )

        clear_existing_chk = st.checkbox("☑️ پاکسازی و حذف کامل اسامی قبلی پیش از ذخیره اسامی اکسل جدید", value=True, key="chk_auto_clear_excel")

        uploaded_file = st.file_uploader("فایل اکسل (xlsx) یا (csv) اسامی را انتخاب کنید:", type=["xlsx", "csv"], key=f"excel_{st.session_state['excel_upload_key']}")
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded_file)
                else:
                    df_up = pd.read_excel(uploaded_file)

                st.success(f"فایل با موفقیت خوانده شد. تعداد {len(df_up)} دانش‌آموز پیدا شد.")
                st.dataframe(df_up, use_container_width=True)

                if st.button("⚡ بارگذاری و ذخیره تمام اسامی در دیتابیس", key="btn_save_excel_db"):
                    with get_connection() as conn:
                        if clear_existing_chk:
                            conn.execute("DELETE FROM evaluations")
                            conn.execute("DELETE FROM behaviors")
                            conn.execute("DELETE FROM quiz_results")
                            conn.execute("DELETE FROM students")
                            conn.commit()

                        added_count = 0
                        shamsi_today = get_current_shamsi_date()
                        for _, row in df_up.iterrows():
                            fn = str(row.get('نام', '')).strip()
                            ln = str(row.get('نام خانوادگی', '')).strip()
                            nid = str(row.get('کد ملی', '')).strip()
                            pin = str(row.get('رمز اختصاصی', '1234')).strip()
                            ph = str(row.get('شماره همراه اولیا', '')).strip()
                            grp = str(row.get('گروه کلاسی', 'گروه ارمغان 🚀')).strip()

                            if fn and ln:
                                try:
                                    conn.execute(
                                        "INSERT INTO students (first_name, last_name, national_id, pin_code, parent_phone, student_group, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                        (fn, ln, nid, pin, ph, grp, shamsi_today)
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

    with tab5:
        with st.form("add_single_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                fn = st.text_input("نام:*")
                nid = st.text_input("کد ملی دانش‌آموز:")
                grp = st.selectbox("گروه کلاسی:", CLASS_GROUPS)
            with col2:
                ln = st.text_input("نام خانوادگی:*")
                pin = st.text_input("رمز ۴ رقمی اختصاصی:", value="1234")
                ph = st.text_input("شماره همراه اولیا:")
            notes = st.text_area("توضیحات تکمیلی:")

            if st.form_submit_button("ثبت دانش‌آموز"):
                if fn.strip() and ln.strip():
                    try:
                        shamsi_today = get_current_shamsi_date()
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO students (first_name, last_name, national_id, pin_code, parent_phone, student_group, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (fn.strip(), ln.strip(), nid.strip(), pin.strip(), ph.strip(), grp, notes.strip(), shamsi_today)
                            )
                            conn.commit()
                        st.success(f"دانش‌آموز {fn} {ln} با موفقیت ثبت شد.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("کد ملی تکراری است.")
                else:
                    st.warning("لطفاً نام و نام خانوادگی را وارد کنید.")

# ---------------------------------------------------------
# 3. QUALITATIVE EVALUATION (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی توصیفی و کیفی ۷ درس پایه پنجم")
    
    students_df = load_students()
    if students_df.empty:
        st.info("دانش‌آموزی ثبت نشده است.")
    else:
        with st.form("eval_form"):
            col_ev1, col_e2 = st.columns(2)
            with col_ev1:
                selected_student = st.selectbox("انتخاب دانش‌آموز:*", students_df['full_name'].tolist())
                selected_subject = st.selectbox("انتخاب درس:*", FIFTH_GRADE_SUBJECTS)
            with col_e2:
                selected_level = st.selectbox("سطح عملکرد توصیفی:*", EVALUATION_LEVELS)
                eval_date = st.text_input("تاریخ ارزشیابی (شمسی):", value=get_current_shamsi_date())
                
            feedback_text = st.text_area("توصیف عملکرد معلم و توصیه‌های آموزشی:")
            
            if st.form_submit_button("💾 ثبت ارزشیابی کیفی"):
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
# 4. BEHAVIORAL LOGS & PRAISE / WARNING (TEACHER ONLY)
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
                        st.success("مورد رفتاری با موفقیت ثبت شد.")
                        st.rerun()
                    else:
                        st.error("لطفاً عنوان را وارد کنید.")
                        
        with col_b2:
            st.subheader("📄 پیش‌نمایش و صدور PDF تشویق / هشدار")
            selected_student_p = st.selectbox("انتخاب دانش‌آموز برای صدور برگه:", students_df['full_name'].tolist(), key="b_preview_st")
            s_id_p = int(students_df[students_df['full_name'] == selected_student_p]['id'].values[0])
            
            with get_connection() as conn:
                st_info = conn.execute("SELECT * FROM students WHERE id = ?", (s_id_p,)).fetchone()
                nat_id = st_info['national_id'] or 'ثبت نشده'
                st_grp = st_info['student_group'] or 'بدون گروه'
                
                b_records = conn.execute("SELECT * FROM behaviors WHERE student_id = ? ORDER BY id DESC LIMIT 1", (s_id_p,)).fetchone()
                
            if b_records:
                st.markdown(f"**آخرین مورد ثبت‌شده:** {b_records['behavior_type']} - {b_records['title']}")
                beh_pdf = generate_behavior_report_pdf(
                    selected_student_p, nat_id, st_grp,
                    b_records['behavior_type'], b_records['title'], b_records['description'] or '', b_records['log_date']
                )
                is_pos = 'مثبت' in b_records['behavior_type'] or 'تشویق' in b_records['behavior_type']
                btn_label = "📥 دانلود تقدیرنامه رسمی (PDF)" if is_pos else "📥 دانلود برگه هشدار اولیا (PDF)"
                st.download_button(btn_label, data=beh_pdf, file_name=f"behavior_report_{s_id_p}_{random.randint(100,999)}.pdf", mime="application/pdf")
            else:
                st.info("مورد رفتاری برای این دانش‌آموز ثبت نشده است.")

# ---------------------------------------------------------
# 5. ONLINE QUIZ MANAGEMENT (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ طراحی و مدیریت آزمون‌های آنلاین پنجم")
    
    q_tab1, q_tab2 = st.tabs(["📝 طراحی آزمون جدید", "📋 مدیریت آزمون‌های موجود"])
    
    with q_tab1:
        st.subheader("➕ ساخت آزمون جدید")
        with st.form("create_quiz_form"):
            q_title = st.text_input("عنوان آزمون:* (مثلاً: آزمون علوم فصل اول)")
            q_subj = st.selectbox("درس مربوطه:*", FIFTH_GRADE_SUBJECTS)
            q_dur = st.number_input("مدت زمان (دقیقه):", min_value=5, max_value=60, value=15)
            
            if st.form_submit_button("🔨 ایجاد آزمون"):
                if q_title.strip():
                    with get_connection() as conn:
                        conn.execute(
                            "INSERT INTO quizzes (title, subject, duration_minutes, created_at) VALUES (?, ?, ?, ?)",
                            (q_title.strip(), q_subj, q_dur, get_current_shamsi_date())
                        )
                        conn.commit()
                    st.success(f"آزمون '{q_title}' ساخت شد. اکنون سوالات را اضافه کنید.")
                    st.rerun()
                else:
                    st.error("عنوان آزمون الزامی است.")

    with q_tab2:
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT * FROM quizzes ORDER BY id DESC", conn)
            
        if not quizzes_df.empty:
            sel_quiz_title = st.selectbox("انتخاب آزمون جهت مدیریت سوالات:", quizzes_df['title'].tolist())
            q_row = quizzes_df[quizzes_df['title'] == sel_quiz_title].iloc[0]
            q_id = int(q_row['id'])
            
            with st.form(f"add_q_form_{q_id}"):
                st.markdown(f"##### ➕ افزودن سوال تستی به: **{sel_quiz_title}**")
                q_text = st.text_area("متن سوال:*")
                c1, c2 = st.columns(2)
                with c1:
                    op1 = st.text_input("گزینه ۱:*")
                    op3 = st.text_input("گزینه ۳:*")
                with c2:
                    op2 = st.text_input("گزینه ۲:*")
                    op4 = st.text_input("گزینه ۴:*")
                    
                corr_op = st.selectbox("گزینه صحیح:*", [1, 2, 3, 4])
                expl = st.text_input("توضیح پاسخ تشریحی:")
                
                if st.form_submit_button("💾 ثبت سوال"):
                    if q_text.strip() and op1.strip() and op2.strip():
                        with get_connection() as conn:
                            conn.execute("""
                                INSERT INTO questions (quiz_id, question_text, option_1, option_2, option_3, option_4, correct_option, explanation)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (q_id, q_text.strip(), op1.strip(), op2.strip(), op3.strip(), op4.strip(), corr_op, expl.strip()))
                            conn.commit()
                        st.success("سوال با موفقیت اضافه شد.")
                        st.rerun()
                    else:
                        st.error("لطفاً متن سوال و حداقل گزینه‌های ۱ و ۲ را وارد کنید.")
        else:
            st.info("هنوز آزمونی ساخته نشده است.")

# ---------------------------------------------------------
# 6. STUDENT ONLINE QUIZ TAKING (STUDENT ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین (ویژه دانش‌آموزان)")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = safe_read_sql("SELECT * FROM quizzes WHERE is_active = 1 ORDER BY id DESC", conn)
        
    if students_df.empty or quizzes_df.empty:
        st.warning("آزمون فعالی یا دانش‌آموزی در سامانه وجود ندارد.")
    else:
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            selected_student_q = st.selectbox("نام دانش‌آموز:*", students_df['full_name'].tolist(), key="q_take_st")
            s_id_q = int(students_df[students_df['full_name'] == selected_student_q]['id'].values[0])
        with col_q2:
            selected_quiz_q = st.selectbox("آزمون آنلاین:*", quizzes_df['title'].tolist(), key="q_take_quiz")
            q_id_q = int(quizzes_df[quizzes_df['title'] == selected_quiz_q]['id'].values[0])
            
        with get_connection() as conn:
            questions_df = safe_read_sql("SELECT * FROM questions WHERE quiz_id = ?", conn, params=(q_id_q,))
            
        if questions_df.empty:
            st.info("این آزمون هنوز سوالی ندارد.")
        else:
            st.success(f"تعداد {len(questions_df)} سوال تستی برای این آزمون بارگذاری گردید.")
            
            with st.form(f"quiz_taking_form_{s_id_q}_{q_id_q}"):
                user_answers = {}
                for idx, row in questions_df.iterrows():
                    st.markdown(f"**سوال {idx+1}: {row['question_text']}**")
                    options = [row['option_1'], row['option_2'], row['option_3'], row['option_4']]
                    user_answers[row['id']] = st.radio(
                        f"پاسخ سوال {idx+1}:",
                        options,
                        key=f"q_ans_{row['id']}"
                    )
                    st.markdown("---")
                    
                if st.form_submit_button("🏁 ثبت نهایی آزمون و مشاهده کارنامه"):
                    correct_count = 0
                    total_q = len(questions_df)
                    for idx, row in questions_df.iterrows():
                        selected_text = user_answers[row['id']]
                        corr_idx = int(row['correct_option']) - 1
                        corr_text = [row['option_1'], row['option_2'], row['option_3'], row['option_4']][corr_idx]
                        if selected_text == corr_text:
                            correct_count += 1
                            
                    score_pct = (correct_count / total_q) * 100
                    shamsi_today = get_current_shamsi_date()
                    
                    with get_connection() as conn:
                        conn.execute("""
                            INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, submitted_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (q_id_q, s_id_q, correct_count, total_q, score_pct, shamsi_today))
                        conn.commit()
                        
                    st.balloons()
                    st.success(f"🎉 آزمون با موفقیت ثبت شد! نمره‌ی شما: {correct_count} از {total_q} (درصد: {score_pct:.1f}٪)")

# ---------------------------------------------------------
# 7. PORTFOLIO & COMPREHENSIVE DASHBOARD
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد تحلیلی و پوشه کار جامع دانش‌آموز")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی وجود ندارد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار:", students_df['full_name'].tolist())
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        
        # Privacy & Security Guard for Portfolio
        if not st.session_state['is_teacher_logged_in']:
            with get_connection() as conn:
                real_pin = conn.execute("SELECT pin_code FROM students WHERE id = ?", (s_id,)).fetchone()
                pin_code_db = str(real_pin['pin_code']).strip() if real_pin and real_pin['pin_code'] else '1234'
            
            st.info("🔒 جهت حفظ حریم خصوصی و کرامت دانش‌آموزان، کارنامه و پوشه کار محرمانه می‌باشد.")
            input_pin = st.text_input("🔑 رمز ۴ رقمی اختصاصی دانش‌آموز را وارد کنید:", type="password", key="portfolio_pin_guard")
            if input_pin.strip() != pin_code_db:
                st.warning("⚠️ برای مشاهده کارنامه، لطفاً رمز ۴ رقمی اختصاصی دانش‌آموز را به درستی وارد کنید.")
                st.stop()
            else:
                st.success("🔓 احراز هویت موفقیت‌آمیز دانش‌آموز!")
                
        # Export & Display Comprehensive Report Card
        st.markdown(f"### 📄 پوشه کار و کارنامه تحصیلی: **{selected_student}**")
        
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg_str = f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون"
            st_row = conn.execute("SELECT * FROM students WHERE id = ?", (s_id,)).fetchone()
            nat_id_str = st_row['national_id'] if st_row and st_row['national_id'] else 'ثبت نشده'
            phone_str = st_row['parent_phone'] if st_row and st_row['parent_phone'] else 'ثبت نشده'
            grp_str = st_row['student_group'] if st_row and st_row['student_group'] else 'بدون گروه'

        # Render HTML Report Card directly INSIDE the App Page
        portfolio_html = generate_portfolio_report_html(selected_student, nat_id_str, phone_str, grp_str, eval_count, beh_count, quiz_avg_str)
        st.markdown(portfolio_html, unsafe_allow_html=True)

        portfolio_pdf = generate_comprehensive_portfolio_pdf(s_id)
        st.download_button("📥 دانلود فایل پی دی اف کارنامه (PDF معتبر قابل پرینت)", data=portfolio_pdf, file_name=f"report_card_{selected_student}.pdf", mime="application/pdf")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with c2:
            st.metric("موارد رفتاری ثبت‌شده:", beh_count)
        with c3:
            st.metric("میانگین درصد آزمون آنلاین:", quiz_avg_str)

        st.markdown("---")

        tab_d1, tab_d2, tab_d3 = st.tabs(["📝 ارزشیابی‌های توصیفی", "🌟 سوابق رفتاری", "📊 کارنامه آزمون‌ها"])

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

                st.markdown("##### 📥 صدور گزارش PDF رسمی برای موارد رفتاری فوق:")
                st_info = students_df[students_df['full_name'] == selected_student].iloc[0]
                nat_id = st_info['national_id'] or 'ثبت نشده'
                st_grp = st_info['student_group'] or 'بدون گروه'

                for _, b_row in df_b.iterrows():
                    col_b1, col_b2 = st.columns([3, 1])
                    with col_b1:
                        st.markdown(f"🔹 **{b_row['نوع']}** — {b_row['عنوان رفتار']} ({b_row['تاریخ (شمسی)']})")
                    with col_b2:
                        single_pdf = generate_behavior_report_pdf(
                            selected_student, nat_id, st_grp,
                            b_row['نوع'], b_row['عنوان رفتار'], b_row['توضیحات تکمیلی'], b_row['تاریخ (شمسی)']
                        )
                        is_pos = 'مثبت' in b_row['نوع'] or 'تشویق' in b_row['نوع']
                        btn_txt = "📥 PDF تقدیرنامه" if is_pos else "📥 PDF هشدار"
                        st.download_button(btn_txt, data=single_pdf, file_name=f"behavior_{b_row['id']}.pdf", mime="application/pdf", key=f"dl_b_{b_row['id']}")
            else:
                st.info("مورد رفتاری ثبت نشده است.")

        with tab_d3:
            with get_connection() as conn:
                df_q = safe_read_sql("SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره', r.total_questions AS 'کل سوالات', r.percentage AS 'درصد ٪', r.submitted_at AS 'تاریخ ثبت' FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.id DESC", conn, params=(s_id,))
            if not df_q.empty:
                st.dataframe(df_q, use_container_width=True, hide_index=True)
            else:
                st.info("آزمون آنلاینی ثبت نشده است.")
