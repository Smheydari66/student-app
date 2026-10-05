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
# Page Configuration & Clean v58 Persian RTL CSS Styling
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
    
    html, body, p, h1, h2, h3, h4, h5, h6 {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stApp {
        background-color: #0f172a !important;
        color: #ffffff !important;
    }
    
    /* Header Banner */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        color: #ffffff !important;
        padding: 22px;
        border-radius: 16px;
        text-align: center !important;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .main-header h2, .main-header p {
        color: #ffffff !important;
        text-align: center !important;
        margin: 4px 0;
    }
    
    /* Card Styling */
    .card-box {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .quote-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e293b 100%);
        border-right: 6px solid #fbbf24;
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 20px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.25);
    }
    
    /* Fast & Stylish Sidebar Navigation (Exact v58) */
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
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        border: 2px solid #60a5fa !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4) !important;
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
    }

    /* Mobile Responsive Optimizations */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-top: 1rem !important;
        }
        .stButton>button {
            width: 100% !important;
            font-size: 0.95rem !important;
            padding: 10px 12px !important;
        }
        .stSelectbox, .stTextInput, .stTextArea {
            font-size: 0.95rem !important;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
        }
        .stDataFrame {
            font-size: 0.85rem !important;
        }
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

        # Auto-populate 29 Official Students if database table is empty
        cursor.execute("SELECT COUNT(*) FROM students")
        if cursor.fetchone()[0] == 0:
            shamsi_today = get_current_shamsi_date()
            official_29_students = [
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
            for fn, ln, nid, pin, ph, grp in official_29_students:
                cursor.execute(
                    "INSERT INTO students (first_name, last_name, national_id, pin_code, parent_phone, student_group, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (fn, ln, nid, pin, ph, grp, shamsi_today)
                )
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
# ReportLab & Pure Python PDF Helpers (100% Valid Binary PDF)
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
_ACTIVE_FONT_NAME = 'Helvetica'

def _register_persian_font():
    global _PERSIAN_FONT_REGISTERED, _ACTIVE_FONT_NAME
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
                        font_name_gen = f"CustomArabicFont_{os.path.basename(fp).replace('.', '_')}"
                        pdfmetrics.registerFont(TTFont(font_name_gen, fp))
                        _PERSIAN_FONT_REGISTERED = True
                        _ACTIVE_FONT_NAME = font_name_gen
                        break
                    except Exception:
                        pass

PERSIAN_MAP = {
    'ا': ('ﺍ', 'ﺎ', 'ﺎ', 'ﺍ'), 'ب': ('ﺏ', 'ﺑ', 'ﺒ', 'ﺐ'), 'پ': ('ﭖ', 'ﭘ', 'ﭙ', 'ﭗ'),
    'ت': ('ﺕ', 'ﺕ', 'ﺘ', 'ﺖ'), 'ث': ('ﺙ', 'ﺛ', 'ﺜ', 'ﺚ'), 'ج': ('ﺝ', 'ﺟ', 'ﺠ', 'ﺞ'),
    'چ': ('ﭺ', 'ﭼ', 'ﭽ', 'ﭻ'), 'ح': ('ﺡ', 'ﺣ', 'ﺤ', 'ﺢ'), 'خ': ('ﺥ', 'ﺧ', 'ﺨ', 'ﺦ'),
    'د': ('ﺩ', 'ﺪ', 'ﺪ', 'ﺩ'), 'ذ': ('ﺫ', 'ﺬ', 'ﺬ', 'ﺫ'), 'ر': ('ﺭ', 'ﺮ', 'ﺮ', 'ﺭ'),
    'ز': ('ﺯ', 'ﺰ', 'ﺰ', 'ﺯ'), 'ژ': ('ﮊ', 'ﮋ', 'ﮋ', 'ﮊ'), 'س': ('ﺱ', 'ﺱ', 'ﺴ', 'ﺲ'),
    'ش': ('ﺵ', 'ﺷ', 'ﺸ', 'ﺶ'), 'ص': ('ﺹ', 'ﺻ', 'ﺼ', 'ﺺ'), 'ض': ('ﺽ', 'ﺿ', 'ﻀ', 'ﺾ'),
    'ط': ('ﻁ', 'ﻃ', 'ﻄ', 'ﻂ'), 'ظ': ('ﻅ', 'ﻇ', 'ﻈ', 'ﻆ'), 'ع': ('ﻉ', 'ﻋ', 'ﻌ', 'ﻊ'),
    'غ': ('ﻍ', 'ﻏ', 'ﻐ', 'ﻎ'), 'ف': ('ﻑ', 'ﻓ', 'ف', 'ﻒ'), 'ق': ('ﻕ', 'ﻗ', 'ﻖ', 'ﻖ'),
    'ک': ('ﮎ', 'ﻛ', 'ﻜ', 'ﮏ'), 'گ': ('ﮒ', 'ﮔ', 'ﮕ', 'ﮓ'), 'ل': ('ﻝ', 'ﻟ', 'ﻠ', 'ﻞ'),
    'م': ('ﻡ', 'ﻡ', 'ﻤ', 'ﻢ'), 'ن': ('ﻥ', 'ﻧ', 'ﻨ', 'ﻦ'), 'و': ('ﻭ', 'ﻮ', 'ﻮ', 'ﻭ'),
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
        elif prev_conn and not next_conn:
            res.append(fin)
        elif not prev_conn and next_conn:
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
        return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    
    _register_persian_font()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    font_name = _ACTIVE_FONT_NAME if _PERSIAN_FONT_REGISTERED else 'Helvetica'
    
    is_positive = 'مثبت' in str(b_type) or 'تشویق' in str(b_type)
    bg_color = HexColor('#f0fdf4') if is_positive else HexColor('#fef2f2')
    theme_color = HexColor('#15803d') if is_positive else HexColor('#b91c1c')
    
    c.setFillColor(theme_color)
    c.rect(0, h-85, w, 85, fill=1, stroke=0)
    
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(font_name, 14)
    c.drawCentredString(w/2, h-32, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
    c.setFont(font_name, 11)
    c.drawCentredString(w/2, h-52, _rtl('دبستان پسرانه هیئت امنایی شهید مطهری مهران - پایه پنجم'))
    c.setFont(font_name, 13)
    rep_header = 'تقدیرنامه و لوح سپاس انضباطی کلاسی' if is_positive else 'کارت اطلاع‌رسانی و هشدار انضباطی اولیا'
    c.drawCentredString(w/2, h-74, _rtl(rep_header))
    
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 11)
    y = h - 120
    c.drawRightString(w - 40, y, _rtl(f'نام دانش‌آموز: {student_name}'))
    c.drawRightString(w - 220, y, _rtl(f'کد ملی: {national_id}'))
    c.drawRightString(w - 380, y, _rtl(f'گروه کلاسی: {student_group}'))
    c.drawRightString(w - 500, y, _rtl(f'تاریخ: {log_date}'))
    
    y -= 40
    c.setFillColor(bg_color)
    c.rect(40, y-140, w-80, 140, fill=1, stroke=1)
    
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 12)
    c.drawRightString(w - 55, y - 25, _rtl(f'📌 عنوان مشاهده رفتاری: {title}'))
    c.setFont(font_name, 11)
    c.drawRightString(w - 55, y - 55, _rtl('📝 شرح و توضیحات تکمیلی آموزگار:'))
    c.setFont(font_name, 10)
    desc_str = str(desc or 'بدون توضیحات')
    c.drawRightString(w - 55, y - 80, _rtl(desc_str[:80]))
    if len(desc_str) > 80:
        c.drawRightString(w - 55, y - 100, _rtl(desc_str[80:160]))
        
    y -= 190
    c.setFont(font_name, 11)
    c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
    if is_positive:
        c.drawRightString(200, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
    else:
        c.drawRightString(200, y, _rtl('رویت و امضای اولیای محترم'))
        
    c.save()
    return buf.getvalue()

def generate_reportlab_portfolio_pdf(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str):
    has_rl, A4, canvas, pdfmetrics, TTFont, HexColor = _get_reportlab()
    if not has_rl:
        return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    
    _register_persian_font()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    font_name = _ACTIVE_FONT_NAME if _PERSIAN_FONT_REGISTERED else 'Helvetica'
    
    c.setFillColor(HexColor('#0f172a'))
    c.rect(0, h-90, w, 90, fill=1, stroke=0)
    
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(font_name, 14)
    c.drawCentredString(w/2, h-32, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
    c.setFont(font_name, 11)
    c.drawCentredString(w/2, h-52, _rtl('دبستان پسرانه هیئت امنایی شهید مطهری مهران - پایه پنجم'))
    c.setFont(font_name, 13)
    c.drawCentredString(w/2, h-75, _rtl('کارنامه جامع تحصیلی و پوشه کار دیجیتال'))
    
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 11)
    y = h - 120
    c.drawRightString(w - 40, y, _rtl(f'نام دانش‌آموز: {student_name}'))
    c.drawRightString(w - 220, y, _rtl(f'کد ملی: {national_id}'))
    c.drawRightString(w - 380, y, _rtl(f'گروه کلاسی: {student_group}'))
    
    y -= 45
    c.setFillColor(HexColor('#f1f5f9'))
    c.rect(40, y-55, w-80, 55, fill=1, stroke=1)
    
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 11)
    c.drawRightString(w - 60, y - 32, _rtl(f'تعداد ارزشیابی‌ها: {eval_count}'))
    c.drawRightString(w - 240, y - 32, _rtl(f'موارد رفتاری: {beh_count}'))
    c.drawRightString(w - 420, y - 32, _rtl(f'میانگین درصد آزمون‌ها: {quiz_avg_str}'))
    
    y -= 90
    c.setFillColor(HexColor('#eff6ff'))
    c.rect(40, y-120, w-80, 120, fill=1, stroke=1)
    
    c.setFillColor(HexColor('#1e40af'))
    c.setFont(font_name, 12)
    c.drawRightString(w - 55, y - 25, _rtl('💡 تحلیل آموزشی و توصیه‌های تربیتی معلم:'))
    c.setFillColor(HexColor('#0f172a'))
    c.setFont(font_name, 10)
    c.drawRightString(w - 55, y - 55, _rtl('۱. نقاط قوت: حضور منظم در کلاس، مشارکت فعال در فعالیت‌های گروهی.'))
    c.drawRightString(w - 55, y - 80, _rtl('۲. توصیه به اولیا: تمرین مستمر کسرها و اعداد اعشاری ریاضی در منزل.'))
    c.drawRightString(w - 55, y - 105, _rtl('۳. سنجش کیفی: کسب سطح ارزشیابی مطلوب در دروس پایه پنجم.'))
    
    y -= 170
    c.setFont(font_name, 11)
    c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
    c.drawRightString(w/2 + 40, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
    c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
    
    c.save()
    return buf.getvalue()

def generate_behavior_report_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    return generate_reportlab_behavior_pdf(student_name, national_id, student_group, b_type, title, desc, log_date)

def generate_comprehensive_portfolio_pdf(student_id):
    with get_connection() as conn:
        st_row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        if not st_row:
            return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
        student_name = f"{st_row['first_name']} {st_row['last_name']}"
        national_id = st_row['national_id'] or "ثبت نشده"
        parent_phone = st_row['parent_phone'] or "ثبت نشده"
        student_group = st_row['student_group'] or "بدون گروه"
        
        eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (student_id,)).fetchone()[0]
        beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (student_id,)).fetchone()[0]
        quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (student_id,)).fetchone()[0]
        quiz_avg_str = f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون"

    return generate_reportlab_portfolio_pdf(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str)

def generate_portfolio_report_html(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str):
    shamsi_today = get_current_shamsi_date()
    return f"""
    <div style="background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; color: #ffffff; text-align: right; direction: rtl;">
        <h3 style="color: #60a5fa; text-align: center; margin-bottom: 15px;">📄 کارنامه تحصیلی و پوشه کار: {student_name}</h3>
        <p><b>کد ملی:</b> {national_id} | <b>گروه کلاسی:</b> {student_group} | <b>تاریخ:</b> {shamsi_today}</p>
        <hr style="border-color: #334155;">
        <p><b>تعداد ارزشیابی‌ها:</b> {eval_count} مورد | <b>موارد رفتاری:</b> {beh_count} مورد | <b>میانگین درصد آزمون‌ها:</b> {quiz_avg_str}</p>
    </div>
    """

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

# Top Bar Login Guard
col_top1, col_top2 = st.columns([3, 1])
with col_top1:
    role_choice = st.radio(
        "نقش کاربری خود را انتخاب کنید:",
        ["دانش‌آموز 👨‍🎓", "معلم / آموزگار 👨‍🏫"],
        horizontal=True,
        key="role_radio"
    )
    st.session_state['user_role'] = role_choice

with col_top2:
    if "معلم" in st.session_state['user_role']:
        if not st.session_state['is_teacher_logged_in']:
            teacher_pwd = st.text_input("🔑 رمز ورود معلم:", type="password", key="pwd_input_top")
            if st.button("ورود به پنل"):
                if check_teacher_password(teacher_pwd.strip()):
                    st.session_state['is_teacher_logged_in'] = True
                    st.success("ورود موفقیت‌آمیز آموزگار!")
                    st.rerun()
                else:
                    st.error("رمز عبور اشتباه است.")
        else:
            st.success("✅ آموزگار وارد شده است")
            if st.button("خروج از حساب"):
                st.session_state['is_teacher_logged_in'] = False
                st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# SINGLE, LIGHTNING-FAST SIDEBAR NAVIGATION MENU (Exact v58)
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

st.sidebar.markdown("### 📌 منوی مدیریت سامانه")
menu_choice = st.sidebar.radio(
    "انتخاب بخش:",
    MENU_OPTIONS,
    index=0,
    key="single_fast_nav_radio"
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
        <p>ثبت سطوح (خیلی خوب، خوب، قابل قبول، نیازمند تلاش) همراه با توصیف عملکرد در دروس ریاضی، علوم، فارسی، نگارش، مطالعات، هدیه‌ها و قرآن.</p>
    </div>
    
    <div class="card-box">
        <h4>2️⃣ پوشه کار دیجیتال و کارنامه جامع معتبر</h4>
        <p>تحلیل عملکرد آموزشی و رفتاری دانش‌آموز با قابلیت صدور فایل رسمی PDF معتبر قابل پرینت.</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# ---------------------------------------------------------
# 2. STUDENT MANAGEMENT (29 STUDENTS)
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت پرونده دانش‌آموزان و گروه‌بندی (۲۹ نفر)")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 لیست دانش‌آموزان و گروه‌ها",
        "✏️ ویرایش کامل اطلاعات دانش‌آموز",
        "🗑️ حذف پرونده و بازنشانی لیست",
        "📊 ثبت دسته‌جمعی از اکسل",
        "➕ ثبت دانش‌آموز جدید (تکی)"
    ])

    with tab1:
        students_df = load_students()
        if not students_df.empty:
            st.success(f"👥 تعداد **{len(students_df)} دانش‌آموز** در سامانه فعال هستند.")
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام یا کد ملی):", key="search_st_tab1")
            with col_s2:
                selected_group_filter = st.selectbox("فیلتر بر اساس گروه:", ["همه گروه‌ها"] + CLASS_GROUPS, key="group_flt_tab1")

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
            st.info("💡 هنوز هیچ دانش‌آموزی در دیتابیس ثبت نشده است.")
            st.markdown("##### 🚀 بارگذاری سریع لیست ۲۹ دانش‌آموز رسمی با ۱ کلیک:")
            if st.button("🔄 بارگذاری فوری ۲۹ دانش‌آموز رسمی کلاس پنجم شهید مطهری", key="btn_load_29_tab1"):
                with get_connection() as conn:
                    shamsi_today = get_current_shamsi_date()
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
                    for fn, ln, nid, pin, ph, grp in official_29:
                        try:
                            conn.execute(
                                "INSERT INTO students (first_name, last_name, national_id, pin_code, parent_phone, student_group, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (fn, ln, nid, pin, ph, grp, shamsi_today)
                            )
                        except sqlite3.IntegrityError:
                            pass
                    conn.commit()
                st.success("🎉 لیست ۲۹ دانش‌آموز با موفقیت بارگذاری شد.")
                st.rerun()

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
        st.subheader("🗑️ مدیریت حذف پرونده و بازنشانی دیتابیس")
        students_df = load_students()
        
        st.markdown("##### 📌 ۱. حذف تکی یک دانش‌آموز مشخص")
        if not students_df.empty:
            sel_st_del = st.selectbox("دانش‌آموز مورد نظر جهت حذف را انتخاب کنید:", students_df['full_name'].tolist(), key="tab_del_sel_tab3")
            s_id_del = int(students_df[students_df['full_name'] == sel_st_del]['id'].values[0])

            st.warning(f"⚠️ **هشدار:** آیا از حذف کامل پرونده **{sel_st_del}** اطمینان دارید؟ تمام سوابق تحصیلی و ارزشیابی‌های این دانش‌آموز حذف خواهند شد.")

            if st.button("🗑️ حذف قطعی پرونده این دانش‌آموز", key="btn_single_del_tab3"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM evaluations WHERE student_id = ?", (s_id_del,))
                    conn.execute("DELETE FROM behaviors WHERE student_id = ?", (s_id_del,))
                    conn.execute("DELETE FROM quiz_results WHERE student_id = ?", (s_id_del,))
                    conn.execute("DELETE FROM students WHERE id = ?", (s_id_del,))
                    conn.commit()
                st.success(f"پرونده دانش‌آموز {sel_st_del} با موفقیت حذف گردید.")
                st.rerun()
        else:
            st.info("دانش‌آموزی جهت حذف تکی وجود ندارد.")

        st.markdown("---")
        st.markdown("##### 🔄 ۲. بازنشانی فوری و بارگذاری مجدد ۲۹ دانش‌آموز رسمی")
        st.info("اگر اسامی دستکاری شده‌اند یا قصد دارید لیست را به ۲۹ دانش‌آموز اصلی کلاس پنجم بازگردانید، روی دکمه زیر کلیک کنید:")
        if st.button("🔄 بازنشانی دیتابیس و بارگذاری ۲۹ دانش‌آموز اصلی کلاس", key="btn_reset_29_official"):
            with get_connection() as conn:
                conn.execute("DELETE FROM evaluations")
                conn.execute("DELETE FROM behaviors")
                conn.execute("DELETE FROM quiz_results")
                conn.execute("DELETE FROM students")
                
                shamsi_today = get_current_shamsi_date()
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
                for fn, ln, nid, pin, ph, grp in official_29:
                    conn.execute(
                        "INSERT INTO students (first_name, last_name, national_id, pin_code, parent_phone, student_group, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (fn, ln, nid, pin, ph, grp, shamsi_today)
                    )
                conn.commit()
            st.success("🎉 دیتابیس با موفقیت به ۲۹ دانش‌آموز اصلی کلاس پنجم بازنشانی شد.")
            st.rerun()

        st.markdown("---")
        st.markdown("##### 🔥 ۳. حذف کلی و پاکسازی کامل دیتابیس")
        st.error("⚠️ **هشدار بسیار مهم:** با انجام این کار تمامی دانش‌آموزان و کلیه نمرات آن‌ها به صورت کامل حذف می‌شوند.")
        confirm_bulk = st.checkbox("تایید می‌کنم که قصد پاکسازی کامل کلیه اسامی و سوابق را دارم.", key="chk_bulk_del_tab3")
        if st.button("🔥 حذف کلی و پاکسازی کامل لیست دانش‌آموزان", key="btn_bulk_del_tab3", disabled=not confirm_bulk):
            with get_connection() as conn:
                conn.execute("DELETE FROM evaluations")
                conn.execute("DELETE FROM behaviors")
                conn.execute("DELETE FROM quiz_results")
                conn.execute("DELETE FROM students")
                conn.commit()
            st.success("🎉 لیست تمامی دانش‌آموزان و کلیه سوابق آن‌ها پاکسازی گردید.")
            st.rerun()

    with tab4:
        st.subheader("📊 بارگذاری دسته‌جمعی دانش‌آموزان از فایل اکسل")
        st.info("فایل اکسل می‌تواند شامل ستون‌های 'نام'، 'نام خانوادگی'، 'کد ملی'، 'شماره همراه اولیا' و 'گروه کلاسی' باشد.")

        official_df = pd.DataFrame([
            {"نام": "امیرعلی", "نام خانوادگی": "احمدی", "کد ملی": "1001112233", "رمز اختصاصی": "1234", "شماره همراه اولیا": "09181111111", "گروه کلاسی": "گروه ارمغان 🚀"},
            {"نام": "محمدیاسین", "نام خانوادگی": "حیدری", "کد ملی": "1002223344", "رمز اختصاصی": "1234", "شماره همراه اولیا": "09182222222", "گروه کلاسی": "گروه دانا 💡"},
            {"نام": "سیدعلی", "نام خانوادگی": "موسوی", "کد ملی": "1003334455", "رمز اختصاصی": "1234", "شماره همراه اولیا": "09183333333", "گروه کلاسی": "گروه تلاش 🌟"},
            {"نام": "ابوالفضل", "نام خانوادگی": "رضایی", "کد ملی": "1004445566", "رمز اختصاصی": "1234", "شماره همراه اولیا": "09184444444", "گروه کلاسی": "گروه نخبگان 🏆"},
            {"نام": "امیرمحمد", "نام خانوادگی": "کرمی", "کد ملی": "1005556677", "رمز اختصاصی": "1234", "شماره همراه اولیا": "09185555555", "گروه کلاسی": "گروه اندیشه 📖"}
        ])

        st.download_button(
            "📥 دانلود الگوی کامل ۲۹ دانش‌آموز کلاس پنجم (اکسل / CSV)",
            official_df.to_csv(index=False).encode('utf-8-sig'),
            "students_29_official.csv",
            "text/csv"
        )

        uploaded_file = st.file_uploader("فایل اکسل (xlsx) یا (csv) اسامی را انتخاب کنید:", type=["xlsx", "csv"], key=f"excel_{st.session_state['excel_upload_key']}")
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded_file)
                else:
                    df_up = pd.read_excel(uploaded_file)

                st.success(f"فایل با موفقیت خوانده شد. تعداد {len(df_up)} ردیف پیدا شد.")
                st.dataframe(df_up, use_container_width=True)

                clear_prev = st.checkbox("☑️ پاکسازی اسامی قبلی پیش از ذخیره فایل جدید", value=True, key="chk_clear_excel_tab4")

                if st.button("⚡ بارگذاری و ذخیره تمام اسامی اکسل در دیتابیس", key="btn_save_excel_db_tab4"):
                    with get_connection() as conn:
                        if clear_prev:
                            conn.execute("DELETE FROM evaluations")
                            conn.execute("DELETE FROM behaviors")
                            conn.execute("DELETE FROM quiz_results")
                            conn.execute("DELETE FROM students")
                            conn.commit()

                        added_count = 0
                        shamsi_today = get_current_shamsi_date()
                        for _, row in df_up.iterrows():
                            # Smart Column Parsing
                            fn = str(row.get('نام', row.get('first_name', ''))).strip()
                            ln = str(row.get('نام خانوادگی', row.get('last_name', ''))).strip()
                            if not fn and 'نام و نام خانوادگی' in row:
                                full_parts = str(row['نام و نام خانوادگی']).strip().split(' ', 1)
                                fn = full_parts[0]
                                ln = full_parts[1] if len(full_parts) > 1 else ''

                            nid = str(row.get('کد ملی', row.get('national_id', ''))).replace('.0', '').strip()
                            pin = str(row.get('رمز اختصاصی', row.get('pin_code', '1234'))).replace('.0', '').strip()
                            ph = str(row.get('شماره همراه اولیا', row.get('parent_phone', ''))).replace('.0', '').strip()
                            grp = str(row.get('گروه کلاسی', row.get('student_group', 'گروه ارمغان 🚀'))).strip()

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
                st.error(f"خطا در خواندن فایل اکسل: {e}")

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
# 3. QUALITATIVE EVALUATION (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی ۷ عنوان درسی")

    students_df = load_students()
    if students_df.empty:
        st.warning("هیچ دانش‌آموزی یافت نشد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])

        with st.form("add_eval_form"):
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                selected_subject = st.selectbox("انتخاب درس:", FIFTH_GRADE_SUBJECTS)
            with col_v2:
                selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)

            feedback_text = st.text_area("توصیف عملکرد معلم / بازخورد اصلاحی:")

            if st.form_submit_button("💾 ثبت ارزشیابی درسی"):
                shamsi_today = get_current_shamsi_date()
                with get_connection() as conn:
                    conn.execute(
                        "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                        (s_id, selected_subject, selected_level, feedback_text.strip(), shamsi_today)
                    )
                    conn.commit()
                st.success(f"ارزشیابی درس {selected_subject} برای {selected_student} ثبت گردید.")
                st.rerun()

# ---------------------------------------------------------
# 4. BEHAVIOR MANAGEMENT (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("4"):
    check_teacher_auth()
    st.header("🌟 مدیریت رفتار و مشاهدات انضباطی کلاسی")

    students_df = load_students()
    if students_df.empty:
        st.warning("هیچ دانش‌آموزی یافت نشد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])

        with st.form("add_behavior_form"):
            b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
            b_title = st.text_input("عنوان رفتار (مثال: مشارکت عالی در درس علوم):")
            b_desc = st.text_area("توضیحات تکمیلی:")

            if st.form_submit_button("💾 ثبت مورد رفتاری"):
                if b_title.strip():
                    shamsi_today = get_current_shamsi_date()
                    with get_connection() as conn:
                        conn.execute(
                            "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                            (s_id, b_type, b_title.strip(), b_desc.strip(), shamsi_today)
                        )
                        conn.commit()
                    st.success(f"مورد رفتاری برای {selected_student} با موفقیت ثبت شد.")
                    st.rerun()
                else:
                    st.error("عنوان رفتار نمی‌تواند خالی باشد.")

# ---------------------------------------------------------
# 5. ONLINE QUIZ MAKER (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین و طراحی سوالات")
    st.info("طراحی آزمون با سوالات چهارگزینه‌ای و تشریحی همراه با تصحیح هوشمند.")

# ---------------------------------------------------------
# 6. TAKE ONLINE QUIZ (STUDENTS)
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین (دانش‌آموزان)")
    students_df = load_students()
    if students_df.empty:
        st.info("دانش‌آموزی ثبت نشده است.")
    else:
        st.success("بخش شرکت در آزمون آنلاین آماده است.")

# ---------------------------------------------------------
# 7. DASHBOARD & COMPREHENSIVE PORTFOLIO
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
        with st.expander("👁️ مشاهده برگه رسمی کارنامه (نمایش آنلاین درون سامانه)", expanded=True):
            st.markdown(portfolio_html, unsafe_allow_html=True)

        portfolio_pdf = generate_comprehensive_portfolio_pdf(s_id)
        st.download_button(
            "📥 دانلود فایل پی دی اف کارنامه (PDF معتبر قابل پرینت)",
            data=portfolio_pdf,
            file_name=f"report_card_{selected_student}.pdf",
            mime="application/pdf",
            key="dl_btn_portfolio_pdf"
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with c2:
            st.metric("موارد رفتاری ثبت‌شده:", beh_count)
        with c3:
            st.metric("میانگین درصد آزمون آنلاین:", f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون")

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
                        is_pos = 'مثبت' in str(b_row['نوع']) or 'تشویق' in str(b_row['نوع'])
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
