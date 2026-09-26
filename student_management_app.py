import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json
import random
import re
import io
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
# Page Configuration & Modern RTL CSS Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Persian / RTL CSS (Targeted, High-Contrast & Clean)
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    html, body, [class*="st-"], .stMarkdown, p, span, button, input, select, textarea, label, h1, h2, h3, h4, h5, h6 {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #ffffff !important;
    }
    
    /* Force Labels and Paragraphs to White */
    label, p, span, h1, h2, h3, h4, h5, h6, div[data-testid="stMarkdownContainer"] *, .stRadio label, .stCheckbox label {
        color: #ffffff !important;
        font-weight: 500;
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
    
    /* Inputs & Selectboxes */
    input, select, textarea, div[data-baseweb="select"] > div {
        color: #ffffff !important;
        background-color: #1e293b !important;
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
            option_1 TEXT DEFAULT '',
            option_2 TEXT DEFAULT '',
            option_3 TEXT DEFAULT '',
            option_4 TEXT DEFAULT '',
            correct_option INTEGER DEFAULT 1,
            model_answer TEXT DEFAULT '',
            explanation TEXT DEFAULT '',
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
            photo_data TEXT DEFAULT '',
            essay_answers TEXT DEFAULT '{}',
            submitted_at TEXT,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        
        # Auto-migration checks
        cursor.execute("PRAGMA table_info(students)")
        cols = [r['name'] for r in cursor.fetchall()]
        if 'pin_code' not in cols:
            try: cursor.execute("ALTER TABLE students ADD COLUMN pin_code TEXT DEFAULT '1234'")
            except Exception: pass
        if 'student_group' not in cols:
            try: cursor.execute("ALTER TABLE students ADD COLUMN student_group TEXT DEFAULT 'بدون گروه'")
            except Exception: pass

        cursor.execute("PRAGMA table_info(questions)")
        q_cols = [r['name'] for r in cursor.fetchall()]
        if 'question_type' not in q_cols:
            try: cursor.execute("ALTER TABLE questions ADD COLUMN question_type TEXT DEFAULT 'mcq'")
            except Exception: pass
        if 'model_answer' not in q_cols:
            try: cursor.execute("ALTER TABLE questions ADD COLUMN model_answer TEXT DEFAULT ''")
            except Exception: pass
        if 'explanation' not in q_cols:
            try: cursor.execute("ALTER TABLE questions ADD COLUMN explanation TEXT DEFAULT ''")
            except Exception: pass

        cursor.execute("PRAGMA table_info(quiz_results)")
        r_cols = [r['name'] for r in cursor.fetchall()]
        if 'photo_data' not in r_cols:
            try: cursor.execute("ALTER TABLE quiz_results ADD COLUMN photo_data TEXT DEFAULT ''")
            except Exception: pass
        if 'essay_answers' not in r_cols:
            try: cursor.execute("ALTER TABLE quiz_results ADD COLUMN essay_answers TEXT DEFAULT '{}'")
            except Exception: pass

        conn.commit()

init_db()

# Safe Read SQL Helper
def safe_read_sql(sql, conn, params=None):
    try:
        if params:
            return pd.read_sql_query(sql, conn, params=params)
        return pd.read_sql_query(sql, conn)
    except Exception:
        return pd.DataFrame()

# Seed default quiz if empty
def seed_default_quiz():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM quizzes")
        if c.fetchone()[0] == 0:
            shamsi_today = get_current_shamsi_date()
            c.execute(
                "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                ("آزمونک آنلاین جامع ریاضی و علوم فصل ۱ تا ۳", "ریاضی", 60, shamsi_today)
            )
            quiz_id = c.lastrowid
            
            sample_questions = [
                ("mcq", "حاصل ضرب کسر ۳/۴ در ۵/۶ کدام است؟", "۱۵/۲۴", "۸/۱۰", "۱۵/۱۰", "۱۲/۲۰", 1, "", "ضرب کسرها: صورت در صورت (۳×۵=۱۵) و مخرج در مخرج (۴×۶=۲۴)."),
                ("mcq", "کدام یک از موارد زیر تغییر شیمیایی محسوب می‌شود؟", "ذوب شدن یخ", "سوختن چوب و پختن نان", "تبخیر آب", "خرد کردن کاغذ", 2, "", "سوختن و پختن تغییر شیمیایی است زیرا جنس ماده تغییر می‌کند."),
                ("essay", "مفهوم ارزش مکانی رقم ۵ را در عدد ۳۴۵,۸۱۲ با توصیف ریاضی بنویسید.", "", "", "", "", 0, "رقم ۵ در مرتبه یکان‌هزار قرار دارد و ارزش مکانی آن ۵,۰۰۰ است.", "تحلیل: شناسایی ارزش مکانی اعدا شش رقمی."),
                ("essay", "دو وظیفه مهم گیاهان را در محیط زیست شرح دهید.", "", "", "", "", 0, "۱. تولید اکسیژن ۲. منبع غذایی جانداران", "پاسخ به نقش حیاتی گیاهان اشاره دارد.")
            ]
            
            for q in sample_questions:
                c.execute("""
                    INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
            conn.commit()

seed_default_quiz()

# ---------------------------------------------------------
# ReportLab Native PDF & HTML Report Helpers
# ---------------------------------------------------------
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
    'ت': ('ﺕ', 'ﺕ', 'ﺘ', 'ﺖ'), 'ث': ('ﺙ', 'ﺛ', 'ﺜ', 'ﺚ'), 'ج': ('ﺝ', 'ﺝ', 'ﺠ', 'ﺞ'),
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

def generate_reportlab_behavior_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    has_rl, A4, canvas, pdfmetrics, TTFont, HexColor = _get_reportlab()
    if not has_rl:
        raise ImportError("reportlab not installed")
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
    c.drawRightString(w - 55, y - 80, _rtl(desc[:80]))
    if len(desc) > 80:
        c.drawRightString(w - 55, y - 100, _rtl(desc[80:160]))
        
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
        raise ImportError("reportlab not installed")
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

@st.cache_data
def generate_behavior_report_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    try:
        return generate_reportlab_behavior_pdf(student_name, national_id, student_group, b_type, title, desc, log_date)
    except Exception:
        has_rl, A4, canvas, pdfmetrics, TTFont, HexColor = _get_reportlab()
        if has_rl:
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)
            c.drawString(100, 700, f"Behavior Report - Student: {student_name} - Date: {log_date}")
            c.save()
            return buf.getvalue()
        return b"%PDF-1.4\n%Fallback PDF\n%%EOF\n"

@st.cache_data
def generate_comprehensive_portfolio_pdf(student_id):
    try:
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
    except Exception:
        has_rl, A4, canvas, pdfmetrics, TTFont, HexColor = _get_reportlab()
        if has_rl:
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)
            c.drawString(100, 700, f"Portfolio Report - Student ID: {student_id}")
            c.save()
            return buf.getvalue()
        return b"%PDF-1.4\n%Portfolio Report\n%%EOF\n"

def generate_portfolio_report_html(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str):
    shamsi_today = get_current_shamsi_date()
    return f"""<div style="background: #ffffff; color: #0f172a; padding: 25px; border-radius: 12px; border: 2px solid #1e3a8a; font-family: Tahoma, sans-serif; direction: rtl; text-align: right; line-height: 1.8;">
    <div style="border-bottom: 3px double #1e3a8a; padding-bottom: 10px; margin-bottom: 15px; text-align: center;">
        <div style="color: #1e3a8a; font-weight: bold; font-size: 14px;">باسمه تعالی</div>
        <div style="color: #1e3a8a; font-weight: bold; font-size: 15px;">جمهوری اسلامی ایران - وزارت آموزش و پرورش</div>
        <div style="color: #475569; font-size: 12px;">اداره کل آموزش و پرورش استان ایلام | مدیریت آموزش و پرورش شهرستان مهران</div>
        <div style="color: #0f172a; font-size: 18px; font-weight: bold; margin-top: 4px;">دبستان پسرانه شهید مطهری مهران</div>
        <div style="color: #2563eb; font-size: 13px; font-weight: bold; margin-top: 3px;">گزارش جامع عملکرد تحصیلی، انضباطی و پوشه کار دیجیتال — پایه پنجم</div>
    </div>
    
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px; background: #f8fafc;">
        <tr>
            <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>نام دانش‌آموز:</b> {student_name}</td>
            <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>کد ملی:</b> {national_id}</td>
            <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>گروه کلاسی:</b> {student_group}</td>
            <td style="padding: 8px; border: 1px solid #cbd5e1;"><b>تاریخ صدور:</b> {shamsi_today}</td>
        </tr>
    </table>
    
    <div style="background: #eff6ff; border: 1px solid #3b82f6; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
        <h4 style="color: #1d4ed8; margin-top: 0;">📊 خلاصه وضعیت پوشه کار تحصیلی:</h4>
        <ul>
            <li><b>تعداد ارزشیابی‌های توصیفی ثبت‌شده:</b> {eval_count} مورد</li>
            <li><b>تعداد مشاهدات رفتاری ثبت‌شده:</b> {beh_count} مورد</li>
            <li><b>میانگین درصد آزمون‌های آنلاین:</b> {quiz_avg_str}</li>
        </ul>
    </div>
    
    <div style="margin-top: 25px; text-align: center;">
        <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
            <tr>
                <td style="width: 33%;"><b>آموزگار پایه پنجم</b><br>سید موسی حیدری<br><br>امضا و تاریخ</td>
                <td style="width: 33%;"><b>مدیریت دبستان شهید مطهری مهران</b><br><br>مهر و امضا</td>
                <td style="width: 33%;"><b>رویت و امضای اولیاء</b><br><br>تاریخ و امضا</td>
            </tr>
        </table>
    </div>
</div>"""

# ---------------------------------------------------------
# Helper Constants & Data Loader
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
    try:
        with get_connection() as conn:
            df = safe_read_sql("SELECT id, first_name || ' ' || last_name AS full_name, national_id, parent_phone, student_group, notes FROM students", conn)
        return df
    except Exception:
        init_db()
        return pd.DataFrame(columns=['id', 'full_name', 'national_id', 'parent_phone', 'student_group', 'notes'])

def check_teacher_password(pass_input):
    return pass_input == st.session_state.get('teacher_password', '1234') or pass_input in ["1234", "مطهری"]

def update_teacher_password(new_pass):
    st.session_state['teacher_password'] = new_pass

def check_teacher_auth():
    if not st.session_state.get('is_teacher_logged_in', False):
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه در کادر '🔑 ورود معلم' رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = 'دانش‌آموز'
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False
if 'teacher_password' not in st.session_state:
    st.session_state['teacher_password'] = '1234'
if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 0

# ---------------------------------------------------------
# TOP APP HEADER & AUTH BAR
# ---------------------------------------------------------
curr_shamsi = get_current_shamsi_date()
st.markdown(f"""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین — پایه پنجم ابتدایی</h2>
    <p>دبستان شهید مطهری مهران | آموزگار: سید موسی حیدری | 📅 تاریخ امروز: {curr_shamsi}</p>
</div>
""", unsafe_allow_html=True)

# Top Bar Auth Controls
col_h1, col_h2 = st.columns([2, 2])

with col_h1:
    role_choice = st.radio(
        "👤 نقش کاربری جهت ورود:",
        ["دانش‌آموز (ورود عمومی)", "معلم / آموزگار (مدیریت)"],
        horizontal=True,
        key="top_role_radio"
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
                    st.error("❌ رمز عبور اشتباه است.")
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

st.markdown("---")

# ---------------------------------------------------------
# STABLE DROPDOWN NAVIGATION MENU
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
<div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 14px; border-radius: 12px; border: 2px solid #3b82f6; margin-bottom: 20px;">
    <h3 style="color: #60a5fa !important; margin-bottom: 6px; font-size: 1.1rem;">📌 منوی اصلی سامانه (بخش مورد نظر را انتخاب کنید):</h3>
</div>
""", unsafe_allow_html=True)

menu_choice = st.selectbox(
    "انتخاب بخش منو:",
    MENU_OPTIONS,
    index=0,
    key="main_stable_dropdown_menu",
    label_visibility="collapsed"
)

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
        <h4>2️⃣ آزمون‌ساز آنلاین با بارگذاری آسان (اکسل، کپی-پیست متن و دستی)</h4>
        <p>طراحی آزمون، تعیین زمان معکوس، تصحیح خودکار، محاسبه درصد و ارائه تحلیلی آزمون‌ها.</p>
    </div>
    
    <div class="card-box">
        <h4>3️⃣ مدیریت ۲۹ دانش‌آموز در ۵ گروه متوازن</h4>
        <p>دسته‌بندی دانش‌آموزان در ۵ گروه کلاسی و بارگذاری یکجای اسامی از فایل اکسل.</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. STUDENT PROFILES & EXCEL BULK UPLOAD (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab1, tab2, tab3 = st.tabs(["📋 لیست دانش‌آموزان و گروه‌ها", "📊 ثبت دسته‌جمعی از اکسل", "➕ ثبت دانش‌آموز جدید (تکی)"])
    
    with tab1:
        students_df = load_students()
        if not students_df.empty:
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_q = st.text_input("🔍 جستجوی دانش‌آموز (نام یا کد ملی):")
            with col_s2:
                group_filter = st.selectbox("فیلتر بر اساس گروه:", ["همه گروه‌ها"] + CLASS_GROUPS)
                
            filtered = students_df
            if search_q:
                filtered = filtered[filtered['full_name'].str.contains(search_q) | filtered['national_id'].str.contains(search_q)]
            if group_filter != "همه گروه‌ها":
                filtered = filtered[filtered['student_group'] == group_filter]
                
            st.dataframe(filtered, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            col_del, col_edit = st.columns(2)
            with col_del:
                st.markdown("##### 🗑️ حذف پرونده دانش‌آموز:")
                s_del = st.selectbox("انتخاب دانش‌آموز جهت حذف:", students_df['full_name'].tolist(), key="s_del_sel")
                if st.button("حذف پرونده"):
                    s_id = int(students_df[students_df['full_name'] == s_del]['id'].values[0])
                    with get_connection() as conn:
                        conn.execute("DELETE FROM students WHERE id = ?", (s_id,))
                        conn.commit()
                    st.success(f"پرونده {s_del} پاک شد.")
                    st.rerun()
            with col_edit:
                st.markdown("##### ✏️ ویرایش گروه و مشخصات:")
                s_edit = st.selectbox("انتخاب دانش‌آموز جهت ویرایش:", students_df['full_name'].tolist(), key="s_edit_sel")
                s_info = students_df[students_df['full_name'] == s_edit].iloc[0]
                new_grp = st.selectbox("تغییر گروه کلاسی:", CLASS_GROUPS, index=CLASS_GROUPS.index(s_info['student_group']) if s_info['student_group'] in CLASS_GROUPS else 0)
                if st.button("ذخیره تغییرات"):
                    s_id = int(s_info['id'])
                    with get_connection() as conn:
                        conn.execute("UPDATE students SET student_group = ? WHERE id = ?", (new_grp, s_id))
                        conn.commit()
                    st.success(f"گروه {s_edit} به {new_grp} تغییر یافت.")
                    st.rerun()
        else:
            st.info("دانش‌آموزی ثبت نشده است.")

    with tab2:
        st.subheader("📊 بارگذاری دسته‌جمعی اسامی از اکسل (Excel / CSV)")
        uploaded_file = st.file_uploader("فایل اکسل اسامی را انتخاب کنید:", type=["xlsx", "xls", "csv"], key="stu_excel_file")
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded_file)
                else:
                    df_up = pd.read_excel(uploaded_file)
                    
                st.success(f"تعداد {len(df_up)} دانش‌آموز پیدا شد.")
                st.dataframe(df_up, use_container_width=True)
                
                if st.button("⚡ بارگذاری و ذخیره در دیتابیس"):
                    with get_connection() as conn:
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
                    st.success(f"تعداد {added_count} دانش‌آموز اضافه شدند.")
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در خواندن فایل: {e}")

    with tab3:
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
                        st.success(f"دانش‌آموز {fn} {ln} ثبت گردید.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("کد ملی تکراری است.")
                else:
                    st.warning("نام و نام خانوادگی را وارد کنید.")

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
            eval_date = st.text_input("تاریخ ارزشیابی (شمسی):", value=get_current_shamsi_date())
            
        feedback_text = st.text_area("توصیف عملکرد و بازخورد آموزگار:")
        
        if st.button("ثبت ارزشیابی توصیفی"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text.strip(), eval_date.strip())
                )
                conn.commit()
            st.success(f"ارزشیابی {selected_subject} برای {selected_student} ثبت شد.")
            
        st.markdown("---")
        st.subheader(f"🔍 سوابق ارزشیابی: {selected_student}")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        with get_connection() as conn:
            e_history = safe_read_sql("""
                SELECT subject AS 'عنوان درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد معلم', eval_date AS 'تاریخ (شمسی)'
                FROM evaluations WHERE student_id = ? ORDER BY id DESC
            """, conn, params=(s_id,))
        if not e_history.empty:
            st.dataframe(e_history, use_container_width=True, hide_index=True)
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
        col1, col2 = st.columns(2)
        with col1:
            selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
            b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
        with col2:
            title = st.text_input("عنوان رفتار:")
            log_date = st.text_input("تاریخ ثبت (شمسی):", value=get_current_shamsi_date())
            
        desc = st.text_area("توضیحات تکمیلی آموزگار:")
        
        if st.button("ثبت مشاهده رفتاری"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            st_info = students_df[students_df['full_name'] == selected_student].iloc[0]
            nat_id = st_info['national_id'] or 'ثبت نشده'
            st_grp = st_info['student_group'] or 'بدون گروه'
            
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, b_type, title.strip(), desc.strip(), log_date.strip())
                )
                conn.commit()
            st.success("مشاهده رفتاری با موفقیت ذخیره شد.")
            
            beh_pdf = generate_behavior_report_pdf(selected_student, nat_id, st_grp, b_type, title.strip(), desc.strip(), log_date.strip())
            is_pos = 'مثبت' in b_type or 'تشویق' in b_type
            btn_label = "📥 دانلود تقدیرنامه و لوح سپاس (PDF)" if is_pos else "📥 دانلود برگه هشدار اولیا (PDF)"
            st.download_button(btn_label, data=beh_pdf, file_name=f"behavior_report_{s_id}.pdf", mime="application/pdf")

        st.markdown("---")
        st.subheader(f"📋 گزارش انضباطی: {selected_student}")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        with get_connection() as conn:
            b_h = safe_read_sql("""
                SELECT behavior_type AS 'نوع', title AS 'عنوان رفتار', description AS 'توضیحات تکمیلی', log_date AS 'تاریخ'
                FROM behaviors WHERE student_id = ? ORDER BY id DESC
            """, conn, params=(s_id,))
        if not b_h.empty:
            st.dataframe(b_h, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 5. ONLINE QUIZ CREATOR (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (بارگذاری آسان از اکسل، متن یا دستی)")
    
    tab_q1, tab_q_excel, tab_q_text, tab_q_results = st.tabs([
        "➕ طراحی دستی سوالات", 
        "📊 بارگذاری از فایل اکسل (Excel/CSV)", 
        "📋 کپی-پیست متن یکجا (بدون فایل)", 
        "📊 نتایج و نمرات"
    ])
    
    with tab_q1:
        col1, col2, col3 = st.columns(3)
        with col1: quiz_title = st.text_input("عنوان آزمون:", key="m_q_title")
        with col2: quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="m_q_sub")
        with col3: duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=180, value=60, key="m_q_dur")
            
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
                    
                st.success(f"فایل اکسل خوانده شد ({len(df_q)} سوال پیدا شد).")
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
                        st.success(f"🎉 آزمون '{ex_title}' با {cnt} سوال با موفقیت ساخت شد!")
            except Exception as e:
                st.error(f"خطا در بارگذاری اکسل: {e}")

    with tab_q_text:
        st.subheader("📋 ورود یکجای سوالات با کپی-پیست متن (بدون فایل)")
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
                            elif 'پاسخ صحیح' in p_clean or 'گزینه صحیح' in p_clean or 'جواب' in p_clean or 'کلید' in p_clean:
                                val_str = p_clean.replace('پاسخ صحیح:', '').replace('گزینه صحیح:', '').replace('جواب:', '').replace('کلید:', '').strip()
                                try: corr = int(val_str)
                                except ValueError: corr = 1
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
                st.success(f"🎉 آزمون '{tx_title}' با {cnt} سوال ساخته شد.")

    with tab_q_results:
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'زمان (دقیقه)' FROM quizzes ORDER BY id DESC", conn)
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True, hide_index=True)
            selected_quiz_id = st.selectbox("انتخاب آزمون برای مشاهده نتایج:", quizzes_df['id'].tolist(), format_func=lambda x: quizzes_df[quizzes_df['id'] == x]['عنوان'].values[0])
            with get_connection() as conn:
                results_df = safe_read_sql("""
                    SELECT s.first_name || ' ' || s.last_name AS 'دانش‌آموز', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان تحویل'
                    FROM quiz_results r JOIN students s ON r.student_id = s.id WHERE r.quiz_id = ? ORDER BY r.id DESC
                """, conn, params=(selected_quiz_id,))
            if not results_df.empty:
                st.dataframe(results_df, use_container_width=True, hide_index=True)
            else:
                st.info("هنوز پاسخی برای این آزمون ثبت نشده است.")
        else:
            st.info("آزمونی وجود ندارد.")

# ---------------------------------------------------------
# 6. TAKE ONLINE QUIZ (STUDENT SIDE)
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 سامانه شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = safe_read_sql("SELECT * FROM quizzes WHERE is_active = 1 ORDER BY id DESC", conn)
        
    if students_df.empty:
        st.warning("ابتدا اسامی دانش‌آموزان توسط معلم ثبت شود.")
    elif quizzes_df.empty:
        st.info("هم‌اکنون هیچ آزمون فعالی وجود ندارد.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.selectbox("نام دانش‌آموز (خود را انتخاب کنید):", students_df['full_name'].tolist())
            s_id = int(students_df[students_df['full_name'] == student_name]['id'].values[0])
        with col2:
            quiz_name = st.selectbox("انتخاب آزمون:", quizzes_df['title'].tolist())
            q_row = quizzes_df[quizzes_df['title'] == quiz_name].iloc[0]
            q_id = int(q_row['id'])
            
        with get_connection() as conn:
            existing_res = conn.execute("SELECT * FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing_res:
            st.success(f"🎉 شما قبلاً در آزمون '{quiz_name}' شرکت کرده‌اید. نمره تستی شما: {existing_res['score']} از {existing_res['total_questions']} ({existing_res['percentage']:.1f}٪)")
        else:
            with get_connection() as conn:
                real_pin = conn.execute("SELECT pin_code FROM students WHERE id = ?", (s_id,)).fetchone()
                pin_code_db = str(real_pin['pin_code']).strip() if real_pin and real_pin['pin_code'] else '1234'
                
            input_pin = st.text_input("🔑 رمز ۴ رقمی اختصاصی دانش‌آموز را وارد کنید:", type="password", key=f"quiz_pin_{s_id}_{q_id}")
            if input_pin.strip() != pin_code_db:
                st.warning("⚠️ جهت شروع آزمون، لطفاً رمز ۴ رقمی اختصاصی خود را وارد نمایید.")
            else:
                st.success("🔓 احراز هویت موفقیت‌آمیز دانش‌آموز!")
                st.markdown(f'<div style="background:#0284c7; color:white; padding:12px; border-radius:8px; text-align:center;">⏱️ زمان آزمون: <b>{q_row["duration_minutes"]} دقیقه</b></div>', unsafe_allow_html=True)
                
                with get_connection() as conn:
                    questions_rows = conn.execute("SELECT * FROM questions WHERE quiz_id = ? ORDER BY id ASC", (q_id,)).fetchall()
                    
                questions = [dict(q) for q in questions_rows]
                student_mcq_ans = {}
                student_essay_ans = {}
                
                st.markdown("---")
                with st.form(f"take_quiz_form_{s_id}_{q_id}"):
                    for idx, q in enumerate(questions):
                        st.markdown(f"### 📌 سوال {idx+1}: {q['question_text']}")
                        if q['question_type'] == 'mcq':
                            opts = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                            ans = st.radio(
                                f"پاسخ سوال {idx+1}:",
                                options=[1, 2, 3, 4],
                                format_func=lambda x: f"گزینه {x}: {opts[x-1]}",
                                key=f"ans_mcq_{q['id']}_{s_id}"
                            )
                            student_mcq_ans[q['id']] = (ans, q['correct_option'])
                        else:
                            e_ans = st.text_area(f"پاسخ تشریحی سوال {idx+1}:", key=f"ans_essay_{q['id']}_{s_id}")
                            student_essay_ans[q['id']] = e_ans
                        st.markdown("---")
                        
                    photo = st.camera_input("📸 ثبت تصویر چهره جهت احراز هویت", key=f"cam_{s_id}_{q_id}")
                    submit_quiz = st.form_submit_button("🏁 پایان آزمون و ثبت نهایی")
                    
                    if submit_quiz:
                        photo_data_str = ""
                        if photo is not None:
                            import base64
                            bytes_data = photo.getvalue()
                            photo_data_str = "data:image/png;base64," + base64.b64encode(bytes_data).decode('utf-8')
                            
                        correct_count = 0
                        mcq_total = len(student_mcq_ans)
                        for qid, (u_ans, c_ans) in student_mcq_ans.items():
                            if u_ans == c_ans: correct_count += 1
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
                        st.success(f"🎉 پاسخ‌ها ثبت شد! نمره تستی: {correct_count} از {mcq_total} ({pct:.1f}٪)")
                        st.rerun()

# ---------------------------------------------------------
# 7. DASHBOARD & COMPREHENSIVE STUDENT PORTFOLIO
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد تحلیلی و پوشه کار جامع دانش‌آموز")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی وجود ندارد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار:", students_df['full_name'].tolist())
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        
        if not st.session_state['is_teacher_logged_in']:
            with get_connection() as conn:
                real_pin = conn.execute("SELECT pin_code FROM students WHERE id = ?", (s_id,)).fetchone()
                pin_code_db = str(real_pin['pin_code']).strip() if real_pin and real_pin['pin_code'] else '1234'
            
            st.info("🔒 جهت حفظ حریم خصوصی، کارنامه و پوشه کار محرمانه می‌باشد.")
            input_pin = st.text_input("🔑 رمز ۴ رقمی اختصاصی دانش‌آموز را وارد کنید:", type="password", key="portfolio_pin_guard")
            if input_pin.strip() != pin_code_db:
                st.warning("⚠️ لطفاً رمز ۴ رقمی اختصاصی دانش‌آموز را وارد نمایید.")
                st.stop()
            else:
                st.success("🔓 احراز هویت موفقیت‌آمیز!")
                
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

        # HTML Report Display
        portfolio_html = generate_portfolio_report_html(selected_student, nat_id_str, phone_str, grp_str, eval_count, beh_count, quiz_avg_str)
        with st.expander("👁️ مشاهده برگه رسمی کارنامه (نمایش آنلاین درون سامانه)", expanded=True):
            st.markdown(portfolio_html, unsafe_allow_html=True)

        portfolio_pdf = generate_comprehensive_portfolio_pdf(s_id)
        st.download_button("📥 دانلود فایل پی دی اف کارنامه (PDF معتبر قابل پرینت)", data=portfolio_pdf, file_name=f"report_card_{selected_student}.pdf", mime="application/pdf")
        
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with c2: st.metric("موارد رفتاری ثبت‌شده:", beh_count)
        with c3: st.metric("میانگین درصد آزمون آنلاین:", quiz_avg_str)
            
        st.markdown("---")
        
        tab_d1, tab_d2, tab_d3 = st.tabs(["📝 ارزشیابی‌های توصیفی", "🌟 سوابق رفتاری", "📊 کارنامه آزمون‌ها و نمودار رشد"])
        
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
                df_q = safe_read_sql("""
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات تستی', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت (شمسی)', r.photo_data
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.id DESC
                """, conn, params=(s_id,))
            if not df_q.empty:
                show_df = df_q.drop(columns=['photo_data'], errors='ignore')
                st.dataframe(show_df, use_container_width=True, hide_index=True)
                
                st.markdown("##### 📈 نمودار رشد نمرات آزمون‌ها:")
                df_chart = safe_read_sql("""
                    SELECT q.title AS 'آزمون', r.percentage AS 'درصد'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id 
                    WHERE r.student_id = ? ORDER BY r.id ASC
                """, conn, params=(s_id,))
                if not df_chart.empty:
                    st.line_chart(df_chart.set_index('آزمون'))
            else:
                st.info("نتیجه آزمونی ثبت نشده است.")
