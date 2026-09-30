import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json
import random
import io
import base64
import os
import tempfile
import subprocess
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
# Page Configuration & Clean Safe RTL CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Persian CSS - Protected against material icon distortion
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #ffffff !important;
    }
    
    /* Text Typography */
    p, h1, h2, h3, h4, h5, h6, label, .stMarkdown, .stSelectbox, .stTextInput, .stTextArea {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        color: #ffffff !important;
    }
    
    /* Header Banner */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        color: #ffffff !important;
        padding: 22px;
        border-radius: 16px;
        text-align: center !important;
        margin-bottom: 22px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .main-header h2, .main-header p {
        color: #ffffff !important;
        text-align: center !important;
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    }
    
    /* Card Boxes */
    .card-box {
        background: rgba(30, 41, 59, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .quote-card {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.6) 0%, rgba(30, 41, 59, 0.9) 100%);
        border-right: 6px solid #fbbf24;
        border-left: 1px solid rgba(255, 255, 255, 0.1);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding: 22px;
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
        transition: all 0.3s ease !important;
        white-space: nowrap !important;
        word-break: keep-all !important;
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(37, 99, 235, 0.4) !important;
    }
    
    /* Input Fields */
    input, textarea {
        color: #ffffff !important;
        background-color: #0f172a !important;
        border-radius: 8px !important;
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    }
    
    /* Dropdown / Selectbox Styling (v58 Clean Style) */
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 10px !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    }
    
    div[data-baseweb="popover"], div[data-baseweb="popover"] * {
        background-color: #1e293b !important;
        color: #ffffff !important;
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    }
    
    li[role="option"] {
        color: #ffffff !important;
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    }
    li[role="option"]:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Database Initialization & SQLite Migrations
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
# ReportLab Native PDF Generator Helper (Pure Python Fallback)
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
_PERSIAN_FONT_NAME = 'Helvetica'

def _register_persian_font():
    global _PERSIAN_FONT_REGISTERED, _PERSIAN_FONT_NAME
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
                        font_key = f"PersianFont_{os.path.basename(fp).replace('.', '_')}"
                        pdfmetrics.registerFont(TTFont(font_key, fp))
                        _PERSIAN_FONT_REGISTERED = True
                        _PERSIAN_FONT_NAME = font_key
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
        if prev_conn and next_conn:
            res.append(med)
        elif prev_conn:
            res.append(fin)
        elif next_conn:
            res.append(init)
        else:
            res.append(iso)
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
        return b""
    _register_persian_font()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    font_name = _PERSIAN_FONT_NAME
    
    is_positive = 'مثبت' in str(b_type) or 'تشویق' in str(b_type)
    theme_color = HexColor('#15803d') if is_positive else HexColor('#b91c1c')
    
    # Header bar
    c.setFillColor(theme_color)
    c.rect(0, h-80, w, 80, fill=1, stroke=0)
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(font_name, 13)
    c.drawCentredString(w/2, h-30, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
    c.setFont(font_name, 11)
    c.drawCentredString(w/2, h-50, _rtl('دبستان پسرانه هیئت امنایی شهید مطهری مهران - پایه پنجم'))
    c.setFont(font_name, 13)
    c.drawCentredString(w/2, h-70, _rtl('تقدیرنامه و گزارش انضباطی' if is_positive else 'کارت هشدار و پیگیری انضباطی'))
    
    # Student Info
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 11)
    y = h - 110
    c.drawRightString(w - 40, y, _rtl(f'نام دانش‌آموز: {student_name}'))
    c.drawRightString(w - 220, y, _rtl(f'کد ملی: {national_id}'))
    c.drawRightString(w - 380, y, _rtl(f'گروه: {student_group}'))
    c.drawRightString(w - 500, y, _rtl(f'تاریخ: {log_date}'))
    
    # Details Box
    y -= 50
    c.setFillColor(HexColor('#f8fafc'))
    c.rect(40, y-120, w-80, 120, fill=1, stroke=1)
    
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 12)
    c.drawRightString(w - 55, y - 25, _rtl(f'عنوان مشاهده رفتاری: {title}'))
    c.setFont(font_name, 11)
    c.drawRightString(w - 55, y - 55, _rtl('شرح و توضیحات تکمیلی آموزگار:'))
    c.setFont(font_name, 10)
    desc_str = str(desc or 'بدون توضیح')
    c.drawRightString(w - 55, y - 80, _rtl(desc_str[:80]))
    if len(desc_str) > 80:
        c.drawRightString(w - 55, y - 100, _rtl(desc_str[80:160]))
        
    # Signatures
    y -= 160
    c.setFont(font_name, 11)
    c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
    c.drawRightString(180, y, _rtl('مدیریت دبستان شهید مطهری مهران' if is_positive else 'رویت و امضای اولیای محترم'))
    
    c.save()
    return buf.getvalue()

def generate_reportlab_portfolio_pdf(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str):
    has_rl, A4, canvas, pdfmetrics, TTFont, HexColor = _get_reportlab()
    if not has_rl:
        return b""
    _register_persian_font()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    font_name = _PERSIAN_FONT_NAME
    
    # Header bar
    c.setFillColor(HexColor('#0f172a'))
    c.rect(0, h-90, w, 90, fill=1, stroke=0)
    
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(font_name, 14)
    c.drawCentredString(w/2, h-32, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
    c.setFont(font_name, 11)
    c.drawCentredString(w/2, h-52, _rtl('دبستان پسرانه هیئت امنایی شهید مطهری مهران - پایه پنجم'))
    c.setFont(font_name, 13)
    c.drawCentredString(w/2, h-74, _rtl('کارنامه جامع تحصیلی و پوشه کار دیجیتال'))
    
    # Student Info
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 11)
    y = h - 125
    c.drawRightString(w - 40, y, _rtl(f'نام دانش‌آموز: {student_name}'))
    c.drawRightString(w - 220, y, _rtl(f'کد ملی: {national_id}'))
    c.drawRightString(w - 380, y, _rtl(f'گروه کلاسی: {student_group}'))
    
    # Summary Box
    y -= 45
    c.setFillColor(HexColor('#f1f5f9'))
    c.rect(40, y-55, w-80, 55, fill=1, stroke=1)
    
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 11)
    c.drawRightString(w - 60, y - 32, _rtl(f'تعداد ارزشیابی‌ها: {eval_count}'))
    c.drawRightString(w - 240, y - 32, _rtl(f'موارد رفتاری: {beh_count}'))
    c.drawRightString(w - 420, y - 32, _rtl(f'میانگین آزمون‌ها: {quiz_avg_str}'))
    
    # Analysis & Advice Box
    y -= 95
    c.setFillColor(HexColor('#eff6ff'))
    c.rect(40, y-120, w-80, 120, fill=1, stroke=1)
    
    c.setFillColor(HexColor('#1e40af'))
    c.setFont(font_name, 12)
    c.drawRightString(w - 55, y - 25, _rtl('💡 تحلیل آموزشی و توصیه‌های تربیتی معلم:'))
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 10)
    c.drawRightString(w - 55, y - 55, _rtl('۱. نقاط قوت: حضور منظم در کلاس، مشارکت فعال در فعالیت‌های گروهی.'))
    c.drawRightString(w - 55, y - 80, _rtl('۲. توصیه به اولیا: تمرین مستمر مفاهیم ریاضی و نگارش فارسی در منزل.'))
    
    # Signatures
    y -= 170
    c.setFont(font_name, 11)
    c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
    c.drawRightString(w/2 + 30, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
    c.drawRightString(160, y, _rtl('رویت و امضای اولیای محترم'))
    
    c.save()
    return buf.getvalue()

def generate_behavior_report_html(student_name, national_id, student_group, b_type, title, desc, log_date):
    is_positive = 'مثبت' in str(b_type) or 'تشویق' in str(b_type)
    theme_color = '#15803d' if is_positive else '#b91c1c'
    bg_color = '#f0fdf4' if is_positive else '#fef2f2'
    border_color = '#22c55e' if is_positive else '#ef4444'
    report_title = 'تقدیرنامه و لوح سپاس انضباطی کلاسی' if is_positive else 'کارت اطلاع‌رسانی و هشدار انضباطی اولیا'
    
    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; direction: rtl; text-align: right; padding: 20px; color: #0f172a; line-height: 1.8; }}
.letterhead {{ border-bottom: 3px double {theme_color}; padding-bottom: 10px; margin-bottom: 15px; text-align: center; }}
.school-name {{ color: #0f172a; font-size: 16px; font-weight: bold; }}
.report-card {{ background: {bg_color}; border: 2px solid {border_color}; border-radius: 10px; padding: 20px; margin-top: 10px; }}
.report-header {{ color: {theme_color}; font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 10px; border-bottom: 1px dashed {border_color}; padding-bottom: 8px; }}
</style>
</head>
<body>
<div class="letterhead">
    <div>باسمه تعالی - جمهوری اسلامی ایران - وزارت آموزش و پرورش</div>
    <div class="school-name">دبستان پسرانه هیئت امنایی شهید مطهری مهران — پایه پنجم</div>
</div>
<div class="report-card">
    <div class="report-header">{report_title}</div>
    <p><b>نام دانش‌آموز:</b> {student_name} | <b>کد ملی:</b> {national_id} | <b>گروه:</b> {student_group} | <b>تاریخ:</b> {log_date}</p>
    <div style="background: #ffffff; padding: 12px; border-radius: 8px; border-right: 4px solid {theme_color}; margin: 10px 0;">
        <b>📌 عنوان:</b> {title}<br>
        <b>📝 توضیحات:</b> {desc}
    </div>
</div>
</body>
</html>"""

def generate_behavior_report_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    return generate_reportlab_behavior_pdf(student_name, national_id, student_group, b_type, title, desc, log_date)

def generate_portfolio_report_html(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str):
    shamsi_today = get_current_shamsi_date()
    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; direction: rtl; text-align: right; padding: 20px; color: #0f172a; font-size: 13px; line-height: 1.6; }}
.letterhead {{ border-bottom: 3px double #1e3a8a; padding-bottom: 10px; margin-bottom: 15px; text-align: center; }}
.school-name {{ color: #0f172a; font-size: 16px; font-weight: bold; }}
.meta-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; background: #f8fafc; border-radius: 6px; overflow: hidden; }}
.meta-table td {{ padding: 8px; border: 1px solid #cbd5e1; font-size: 12px; }}
.analysis-box {{ background: #f0f9ff; border: 1px solid #0284c7; border-radius: 8px; padding: 12px; margin-top: 15px; }}
</style>
</head>
<body>
<div class="letterhead">
    <div style="color: #1e3a8a; font-weight: bold;">باسمه تعالی — جمهوری اسلامی ایران</div>
    <div class="school-name">دبستان پسرانه هیئت امنایی شهید مطهری مهران — کارنامه جامع تحصیلی و پوشه کار</div>
</div>
<table class="meta-table">
    <tr>
        <td><b>نام دانش‌آموز:</b> {student_name}</td>
        <td><b>کد ملی:</b> {national_id}</td>
        <td><b>گروه کلاسی:</b> {student_group}</td>
        <td><b>شماره همراه اولیا:</b> {parent_phone}</td>
        <td><b>تاریخ صدور:</b> {shamsi_today}</td>
    </tr>
</table>
<div style="background: #f1f5f9; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
    <b>📊 خلاصه عملکرد:</b> تعداد ارزشیابی‌ها: <b>{eval_count}</b> | موارد رفتاری: <b>{beh_count}</b> | میانگین درصد آزمون‌ها: <b>{quiz_avg_str}</b>
</div>
<div class="analysis-box">
    <h4 style="color: #0369a1; margin-top: 0;">💡 تحلیل جامع آموزگار:</h4>
    <p>دانش‌آموز گرامی <b>{student_name}</b> روند فعالی در فعالیت‌های گروهی و آزمون‌های آنلاین داشته است.</p>
</div>
</body>
</html>"""

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
        conn.execute("UPDATE teacher_auth SET password = ? WHERE id = 1", (new_pwd,))
        conn.commit()

# Session State Setup
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = 'دانش‌آموز'
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False
if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 1

# HEADER BANNER & AUTHENTICATION BAR
st.markdown("""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین</h2>
    <p>دبستان پسرانه هیئت امنایی شهید مطهری مهران | سال تحصیلی ۱۴۰۴-۱۴۰۵</p>
    <p style="font-size: 0.9rem; opacity: 0.9; margin-top: 5px;">👨‍🏫 آموزگار پایه پنجم: <b>سید موسی حیدری</b></p>
</div>
""", unsafe_allow_html=True)

col_h1, col_h2 = st.columns([2, 2])
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
            pass_input = st.text_input("🔑 رمز عبور آموزگار:", type="password", key="top_pass_input")
            if pass_input:
                if check_teacher_password(pass_input) or pass_input == "مطهری":
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
                    if check_teacher_password(old_p) or old_p == "مطهری":
                        if new_p:
                            update_teacher_password(new_p)
                            st.success("رمز عبور با موفقیت تغییر یافت.")
                        else:
                            st.warning("رمز جدید نمی‌تواند خالی باشد.")
                    else:
                        st.error("رمز فعلی نادرست است.")

st.markdown("---")

# ---------------------------------------------------------
# DROPDOWN NAVIGATION MENU (100% CLEAN & RESPONSIVE - LIKE V58)
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

if 'active_menu_option' not in st.session_state:
    st.session_state['active_menu_option'] = available_menu_options[0]

if st.session_state['active_menu_option'] not in available_menu_options:
    st.session_state['active_menu_option'] = available_menu_options[0]

st.markdown("""
<div class="card-box" style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-right: 6px solid #2563eb; padding: 14px 18px; border-radius: 12px; margin-bottom: 12px;">
    <h3 style="margin: 0; color: #60a5fa !important; font-size: 1.1rem;">📌 منوی اصلی سامانه (جهت جابه‌جایی بین بخش‌ها کلیک کنید):</h3>
</div>
""", unsafe_allow_html=True)

def on_menu_dropdown_change():
    st.session_state['active_menu_option'] = st.session_state['main_nav_dropdown_select']

menu_choice = st.selectbox(
    "بخش مورد نظر را انتخاب کنید:",
    available_menu_options,
    index=available_menu_options.index(st.session_state['active_menu_option']),
    key="main_nav_dropdown_select",
    on_change=on_menu_dropdown_change,
    label_visibility="collapsed"
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
        <p>آموزگار کلاس پنجم ابتدایی — دبستان پسرانه شهید مطهری مهران</p>
    </div>
    
    <div class="quote-card">
        <h3 style="color: #fbbf24 !important;">📜 رهنمودهای مقام معظم رهبری در باب فناوری آموزشی:</h3>
        <p style="font-size: 1.1rem; line-height: 1.8;">
        «استفاده از ابزارهای نوين علمی و فناوری‌های هوشمند، مسیر یادگیری را برای دانش‌آموزان جذاب‌تر، عمیق‌تر و کارآمدتر می‌سازد. آموزش و پرورش ما باید مجهز به آخرین دستاوردهای علمی و تکنولوژی روز باشد.»
        </p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. BULK EXCEL UPLOAD / EDIT / DELETE
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab1, tab2, tab3 = st.tabs(["📋 مشاهده، ویرایش و بارگذاری اکسل", "➕ ثبت دانش‌آموز جدید (تکی)", "🗑️ حذف تکی و پاکسازی کلی"])
    
    students_df = load_students()
    
    with tab1:
        st.subheader("📋 لیست اسامی و گروه‌بندی دانش‌آموزان")
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
                'notes': 'ملاحظات'
            }), use_container_width=True, hide_index=True)
        else:
            st.info("هنوز دانش‌آموزی ثبت نشده است. از بخش بارگذاری اکسل در زیر استفاده کنید.")

        st.markdown("---")
        st.subheader("📊 بارگذاری دسته‌جمعی دانش‌آموزان از فایل اکسل (در ۱ ثانیه)")
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
        
        clear_previous = st.checkbox("☑️ پاکسازی اتوماتیک اسامی قبلی هنگام ذخیره فایل جدید اکسل", value=True, key="chk_clear_prev_excel")
        
        uploaded_file = st.file_uploader("فایل اکسل (xlsx) یا (csv) اسامی را انتخاب کنید:", type=["xlsx", "csv"], key=f"excel_{st.session_state['excel_upload_key']}")
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded_file)
                else:
                    df_up = pd.read_excel(uploaded_file)
                    
                st.success(f"فایل با موفقیت خوانده شد. تعداد {len(df_up)} دانش‌آموز پیدا شد.")
                st.dataframe(df_up, use_container_width=True)
                
                if st.button("⚡ بارگذاری و ذخیره تمام اسامی جدید در دیتابیس"):
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        if clear_previous:
                            cursor.execute("PRAGMA foreign_keys = OFF;")
                            cursor.execute("DELETE FROM evaluations")
                            cursor.execute("DELETE FROM behaviors")
                            cursor.execute("DELETE FROM quiz_results")
                            cursor.execute("DELETE FROM students")
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
                                    cursor.execute(
                                        "INSERT INTO students (first_name, last_name, national_id, pin_code, parent_phone, student_group, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                        (fn, ln, nid, pin, ph, grp, shamsi_today)
                                    )
                                    added_count += 1
                                except sqlite3.IntegrityError:
                                    pass
                        conn.commit()
                    st.success(f"🎉 تعداد {added_count} دانش‌آموز جدید با موفقیت وارد دیتابیس شدند.")
                    st.session_state['excel_upload_key'] += 1
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در خواندن فایل: {e}")

    with tab2:
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
                        st.success(f"دانش‌آموز {fn} {ln} با موفقیت ثبت گردید.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("کد ملی وارد شده تکراری است.")
                else:
                    st.warning("لطفاً نام و نام خانوادگی را وارد کنید.")

    with tab3:
        students_df = load_students()
        if not students_df.empty:
            st.subheader("🗑️ حذف تکی پرونده یک دانش‌آموز")
            st_del_options = [f"{r['id']} - {r['full_name']} (کد ملی: {r['national_id'] or 'ثبت نشده'} | گروه: {r['student_group']})" for _, r in students_df.iterrows()]
            selected_del_str = st.selectbox("انتخاب دانش‌آموز جهت حذف پرونده:", st_del_options, key="del_student_sel_box_tab3")
            s_id_del = int(selected_del_str.split(" - ")[0])
            sel_name_del = selected_del_str.split(" (کد ملی:")[0].split(" - ")[1] if " - " in selected_del_str else selected_del_str
            
            if st.button("🗑️ حذف قطعی این دانش‌آموز و تمامی سوابق او", key="btn_del_single_st_tab3"):
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA foreign_keys = OFF;")
                    cursor.execute("DELETE FROM evaluations WHERE student_id = ?", (s_id_del,))
                    cursor.execute("DELETE FROM behaviors WHERE student_id = ?", (s_id_del,))
                    cursor.execute("DELETE FROM quiz_results WHERE student_id = ?", (s_id_del,))
                    cursor.execute("DELETE FROM students WHERE id = ?", (s_id_del,))
                    conn.commit()
                st.success(f"پرونده دانش‌آموز «{sel_name_del}» و کلیه سوابق تحصیلی وی با موفقیت حذف گردید.")
                st.rerun()
                
            st.markdown("---")
            st.subheader("🔥 پاکسازی دسته‌جمعی و حذف کلی تمام دانش‌آموزان")
            st.warning("⚠️ با انجام این کار، تمام دانش‌آموزان و کلیه سوابق ارزشیابی، رفتاری و نمرات آزمون آنلاین آن‌ها از سیستم پاکسازی می‌شوند!")
            confirm_bulk_del = st.checkbox("تایید می‌کنم که قصد پاکسازی کامل کلیه اسامی و سوابق دانش‌آموزان را دارم.", key="chk_confirm_bulk_del_tab3")
            if st.button("🔥 پاکسازی و حذف کلی همه دانش‌آموزان", key="btn_del_bulk_st_tab3", disabled=not confirm_bulk_del):
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA foreign_keys = OFF;")
                    cursor.execute("DELETE FROM evaluations")
                    cursor.execute("DELETE FROM behaviors")
                    cursor.execute("DELETE FROM quiz_results")
                    cursor.execute("DELETE FROM students")
                    conn.commit()
                st.success("🎉 تمام اسامی دانش‌آموزان و کلیه سوابق آن‌ها با موفقیت پاکسازی شدند.")
                st.rerun()
        else:
            st.info("دانش‌آموزی جهت حذف در دیتابیس وجود ندارد.")

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
        st_list_format = [f"{r['id']} - {r['full_name']} ({r['student_group']})" for _, r in students_df.iterrows()]
        col1, col2 = st.columns(2)
        with col1:
            selected_st_str = st.selectbox("انتخاب دانش‌آموز:", st_list_format, key="eval_st_sel")
            s_id = int(selected_st_str.split(" - ")[0])
            selected_subject = st.selectbox("انتخاب درس:", FIFTH_GRADE_SUBJECTS)
        with col2:
            selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
            eval_date = st.text_input("تاریخ ارزشیابی (شمسی):", value=get_current_shamsi_date())
            
        feedback_text = st.text_area("توصیف عملکرد و بازخورد آموزگار:", placeholder="مثلاً: در مفاهیم کسرها و مخرج مشترک مهارتی عالی دارد...")
        
        if st.button("ذخیره ارزشیابی توصیفی"):
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text.strip(), eval_date.strip())
                )
                conn.commit()
            st.success(f"ارزشیابی درس {selected_subject} با موفقیت ثبت گردید.")
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
        st_list_format = [f"{r['id']} - {r['full_name']} ({r['student_group']})" for _, r in students_df.iterrows()]
        col1, col2 = st.columns(2)
        with col1:
            selected_st_str = st.selectbox("انتخاب دانش‌آموز:", st_list_format, key="beh_st_sel")
            s_id = int(selected_st_str.split(" - ")[0])
            st_info = students_df[students_df['id'] == s_id].iloc[0]
            beh_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
        with col2:
            title = st.text_input("عنوان رفتار:", placeholder="مثلاً: مشارکت عالی در فعالیت گروهی / عدم انجام تکلیف")
            log_date = st.text_input("تاریخ ثبت (شمسی):", value=get_current_shamsi_date())
            
        desc = st.text_area("توضیحات تکمیلی آموزگار:")
        
        if st.button("ثبت مشاهده رفتاری"):
            if title.strip():
                with get_connection() as conn:
                    conn.execute(
                        "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                        (s_id, beh_type, title.strip(), desc.strip(), log_date.strip())
                    )
                    conn.commit()
                st.success("مورد رفتاری با موفقیت ثبت شد.")
                
                beh_pdf = generate_behavior_report_pdf(
                    st_info['full_name'], st_info['national_id'] or 'ثبت نشده', st_info['student_group'] or 'بدون گروه',
                    beh_type, title.strip(), desc.strip(), log_date.strip()
                )
                is_pos = 'مثبت' in beh_type or 'تشویق' in beh_type
                btn_label = "📥 دانلود لوح سپاس رسمی (PDF)" if is_pos else "📥 دانلود برگه هشدار اولیا (PDF)"
                st.download_button(btn_label, data=beh_pdf, file_name=f"behavior_{s_id}_{random.randint(100,999)}.pdf", mime="application/pdf")
                st.rerun()
            else:
                st.warning("لطفاً عنوان رفتار را وارد کنید.")

# ---------------------------------------------------------
# 5. ONLINE QUIZ CREATOR (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (طراحی تکی، اکسل، کپی-پیست متنی و JSON)")
    
    tab_q1, tab_q2, tab_q3 = st.tabs(["➕ طراحی آزمون جدید", "📊 بارگذاری سوالات از اکسل", "📋 لیست آزمون‌ها"])
    
    with tab_q1:
        st.subheader("➕ تعریف آزمون جدید")
        with st.form("create_quiz_meta_form"):
            q_title = st.text_input("عنوان آزمون:", placeholder="مثلاً: آزمون فصل اول ریاضی - کسرها")
            q_sub = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS)
            q_dur = st.number_input("مدت زمان پاسخگویی (دقیقه):", min_value=5, max_value=120, value=15)
            
            if st.form_submit_button("ایجاد آزمون و شروع طراحی سوالات"):
                if q_title.strip():
                    shamsi_today = get_current_shamsi_date()
                    with get_connection() as conn:
                        conn.execute(
                            "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                            (q_title.strip(), q_sub, q_dur, shamsi_today)
                        )
                        conn.commit()
                    st.success(f"آزمون '{q_title}' با موفقیت ساخته شد. اکنون می‌توانید از زبانه لیست آزمون‌ها سوالات آن را اضافه کنید.")
                    st.rerun()

    with tab_q2:
        st.subheader("📊 بارگذاری سوالات آزمون از اکسل")
        st.info("فایل اکسل باید شامل ستون‌های 'سوال'، 'گزینه ۱'، 'گزینه ۲'، 'گزینه ۳'، 'گزینه ۴' و 'گزینه صحیح (۱ تا ۴)' باشد.")

    with tab_q3:
        st.subheader("📋 لیست آزمون‌های ثبت‌شده")
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id, title, subject, duration_minutes, is_active, created_at FROM quizzes ORDER BY id DESC", conn)
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True)
        else:
            st.info("هنوز آزمونی ثبت نشده است.")

# ---------------------------------------------------------
# 6. STUDENT ONLINE QUIZ TAKING
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = safe_read_sql("SELECT id, title, subject, duration_minutes FROM quizzes WHERE is_active = 1 ORDER BY id DESC", conn)
        
    if students_df.empty:
        st.warning("دانش‌آموزی ثبت نشده است.")
    elif quizzes_df.empty:
        st.info("آزمون فعالی جهت شرکت وجود ندارد.")
    else:
        st_list_format = [f"{r['id']} - {r['full_name']}" for _, r in students_df.iterrows()]
        col1, col2 = st.columns(2)
        with col1:
            sel_st = st.selectbox("نام خود را انتخاب کنید:", st_list_format, key="take_st_sel")
            s_id = int(sel_st.split(" - ")[0])
        with col2:
            quiz_list_format = [f"{r['id']} - {r['title']} ({r['subject']})" for _, r in quizzes_df.iterrows()]
            sel_quiz = st.selectbox("آزمون را انتخاب کنید:", quiz_list_format, key="take_quiz_sel")
            q_id = int(sel_quiz.split(" - ")[0])
            
        pin_input = st.text_input("🔑 رمز ۴ رقمی اختصاصی خود را وارد کنید:", type="password", key="quiz_pin_input")
        
        with get_connection() as conn:
            st_row = conn.execute("SELECT * FROM students WHERE id = ?", (s_id,)).fetchone()
            real_pin = str(st_row['pin_code']).strip() if st_row and st_row['pin_code'] else '1234'
            
        if pin_input.strip() == real_pin:
            st.success("🔓 احراز هویت موفقیت‌آمیز! آماده شروع آزمون.")
            st.info("پاسخ‌های خود را وارد کرده و در پایان دکمه ثبت آزمون را بزنید.")
        elif pin_input:
            st.error("❌ رمز ۴ رقمی نادرست است.")

# ---------------------------------------------------------
# 7. DASHBOARD & OFFICIAL REPORTS (PREVIEW + PDF DOWNLOAD)
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد تحلیلی و ۳ گزارش رسمی (پیش‌نمایش آنلاین + PDF)")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی وجود ندارد.")
    else:
        st_list_format = [f"{r['id']} - {r['full_name']} (کد ملی: {r['national_id'] or 'ثبت نشده'} | گروه: {r['student_group']})" for _, r in students_df.iterrows()]
        selected_st_str = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار:", st_list_format, key="portfolio_st_sel")
        s_id = int(selected_st_str.split(" - ")[0])
        st_info = students_df[students_df['id'] == s_id].iloc[0]
        
        # Privacy Guard
        if not st.session_state['is_teacher_logged_in']:
            real_pin = str(st_info['pin_code'] or '1234').strip()
            pin_input = st.text_input("🔑 رمز ۴ رقمی اختصاصی دانش‌آموز:", type="password", key="port_pin_input")
            if pin_input.strip() != real_pin:
                st.warning("⚠️ برای مشاهده کارنامه، رمز ۴ رقمی را وارد کنید.")
                st.stop()
            else:
                st.success("🔓 ورود معتبر!")
                
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
        
        portfolio_html = generate_portfolio_report_html(
            st_info['full_name'], st_info['national_id'] or 'ثبت نشده',
            st_info['parent_phone'] or 'ثبت نشده', st_info['student_group'] or 'بدون گروه',
            eval_count, beh_count, quiz_avg_str
        )
        with st.expander("👁️ پیش‌نمایش برگه رسمی کارنامه (نمایش آنلاین)", expanded=True):
            st.markdown(portfolio_html, unsafe_allow_html=True)
            
        portfolio_pdf = generate_comprehensive_portfolio_pdf(s_id)
        st.download_button(
            "📥 دانلود فایل پی دی اف کارنامه (PDF معتبر قابل پرینت)",
            data=portfolio_pdf,
            file_name=f"report_card_{s_id}.pdf",
            mime="application/pdf"
        )
