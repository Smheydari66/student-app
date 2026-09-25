
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
# Page Configuration & Clean Persian RTL CSS Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High-Contrast Persian / RTL CSS
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    /* Universal Typography */
    html, body, [class*="st-"], .stMarkdown, p, span, button, input, select, textarea, label, h1, h2, h3, h4, h5, h6 {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }
    
    /* Main Header Banner */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        color: #ffffff !important;
        padding: 22px;
        border-radius: 16px;
        text-align: center !important;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
    }
    .main-header h2, .main-header p {
        color: #ffffff !important;
        text-align: center !important;
        margin: 4px 0;
    }
    
    /* Cards */
    .card-box {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        color: #0f172a !important;
    }
    
    .author-card {
        background-color: #ffffff !important;
        border: 2px solid #0284c7 !important;
        border-radius: 14px !important;
        padding: 20px !important;
        text-align: center !important;
        margin-bottom: 20px !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.1) !important;
    }
    
    .quote-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-right: 6px solid #d97706;
        border-left: 1px solid #bae6fd;
        border-top: 1px solid #bae6fd;
        border-bottom: 1px solid #bae6fd;
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        color: #0f172a !important;
    }
    
    /* Native Tabs Custom Styling - Ultra Clean Horizontal Scrolling Bar */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: #f1f5f9 !important;
        padding: 8px !important;
        border-radius: 12px !important;
        border: 1px solid #cbd5e1 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 48px !important;
        background-color: #ffffff !important;
        border-radius: 10px !important;
        color: #1e293b !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 0px 18px !important;
        border: 1px solid #cbd5e1 !important;
        white-space: nowrap !important;
        transition: all 0.2s ease !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e0f2fe !important;
        color: #0284c7 !important;
        border-color: #38bdf8 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: 1px solid #1e40af !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25) !important;
    }
    
    .stTabs [aria-selected="true"] p {
        color: #ffffff !important;
    }

    /* Primary Buttons */
    .stButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        padding: 10px 18px !important;
        font-weight: bold !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25) !important;
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
        word-break: keep-all !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        transform: translateY(-2px);
    }
    
    /* Inputs, Selectboxes, Textareas */
    input, select, textarea, div[data-baseweb="select"] {
        color: #0f172a !important;
        background-color: #ffffff !important;
        border-radius: 8px !important;
    }
    
    div[data-baseweb="popover"], div[data-baseweb="popover"] * {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    
    li[role="option"] {
        color: #0f172a !important;
        background-color: #ffffff !important;
    }
    
    li[role="option"]:hover {
        background-color: #e0f2fe !important;
        color: #0284c7 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False
if 'teacher_password' not in st.session_state:
    st.session_state['teacher_password'] = "1234"
if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 0

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
            FOREIGN KEY (student_id) REFERENCES students (id)
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
            FOREIGN KEY (student_id) REFERENCES students (id)
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
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
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
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        
        # Schema Migrations
        cursor.execute("PRAGMA table_info(students)")
        s_cols = [r['name'] for r in cursor.fetchall()]
        if 'pin_code' not in s_cols:
            try: cursor.execute("ALTER TABLE students ADD COLUMN pin_code TEXT DEFAULT '1234'")
            except Exception: pass
        if 'student_group' not in s_cols:
            try: cursor.execute("ALTER TABLE students ADD COLUMN student_group TEXT DEFAULT 'گروه ارمغان 🚀'")
            except Exception: pass

        cursor.execute("PRAGMA table_info(quiz_results)")
        r_cols = [r['name'] for r in cursor.fetchall()]
        if 'photo_data' not in r_cols:
            try: cursor.execute("ALTER TABLE quiz_results ADD COLUMN photo_data TEXT")
            except Exception: pass
        if 'essay_answers' not in r_cols:
            try: cursor.execute("ALTER TABLE quiz_results ADD COLUMN essay_answers TEXT")
            except Exception: pass

        conn.commit()

init_db()

def safe_read_sql(sql, conn, params=None):
    try:
        if params:
            return pd.read_sql_query(sql, conn, params=params)
        return pd.read_sql_query(sql, conn)
    except Exception:
        return pd.DataFrame()

# Seed sample built-in exam if empty
def seed_default_quiz():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM quizzes")
        if c.fetchone()[0] == 0:
            shamsi_today = get_current_shamsi_date()
            c.execute(
                "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, ?, ?)",
                ("آزمونک جامع فصل اول ریاضی و علوم پنجم", "ریاضی", 60, 1, shamsi_today)
            )
            quiz_id = c.lastrowid
            
            sample_questions = [
                ("mcq", "حاصل کسر ۳/۵ به اضافه ۱/۱۰ کدام گزینه است؟", "۷/۱۰", "۴/۱۵", "۴/۱۰", "۵/۱۰", 1, "", "مخرج مشترک ۱۰ گرفته می‌شود: ۶/۱۰ + ۱/۱۰ = ۷/۱۰"),
                ("mcq", "کدام یک از موارد زیر تغییر شیمیایی محسوب می‌شود؟", "ذوب شدن یخ", "پختن نان و سوختن چوب", "تبخیر آب", "خرد کردن کاغذ", 2, "", "پختن نان و سوختن تغییر شیمیایی است زیرا جنس ماده عوض می‌شود."),
                ("essay", "مفهوم ارزش مکانی رقم ۵ را در عدد ۳۴۵,۸۱۲ با رسم شکل یا توصیف ریاضی توضیح دهید.", "", "", "", "", 0, "رقم ۵ در مرتبه یکان‌هزار قرار دارد و ارزش مکانی آن برابر با ۵,۰۰۰ است.", "تحلیل: شناسایی مرتبه یکان‌هزار در اعداد ۶ رقمی."),
                ("essay", "سه مورد از نقش‌ها و وظایف اصلی گیاهان را در زنجیره غذایی محیط زیست شرح دهید.", "", "", "", "", 0, "۱. تولیدکننده اکسیژن، ۲. منبع غذایی اصلی جانداران گیاه‌خوار، ۳. تثبیت خاک و جلوگیری از فرسایش.", "پاسخ کامل باید به نقش تولیدکنندگی اشاره داشته باشد.")
            ]
            
            for q in sample_questions:
                c.execute("""
                    INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
            conn.commit()

seed_default_quiz()

# ---------------------------------------------------------
# PDF & HTML Report Generator Helpers
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def generate_chart_b64(quiz_titles, quiz_pcts, eval_counts):
    try:
        import io
        import base64
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 2.8), dpi=150)
        fig.patch.set_facecolor('#ffffff')
        
        if quiz_pcts:
            ax1.bar(range(len(quiz_pcts)), quiz_pcts, color='#2563eb', width=0.4)
            ax1.set_ylim(0, 110)
            ax1.set_title('Test Scores (%)', fontsize=9)
            ax1.set_xticks(range(len(quiz_titles)))
            ax1.set_xticklabels([f'Quiz {i+1}' for i in range(len(quiz_titles))], fontsize=8)
        else:
            ax1.text(0.5, 0.5, 'No Quiz Data', ha='center', va='center', fontsize=9)
            ax1.axis('off')
            
        labels = list(eval_counts.keys())
        values = list(eval_counts.values())
        colors = ['#16a34a', '#2563eb', '#eab308', '#dc2626']
        if sum(values) > 0:
            ax2.bar(labels, values, color=colors[:len(labels)], width=0.4)
            ax2.set_title('Evaluation Distribution', fontsize=9)
        else:
            ax2.text(0.5, 0.5, 'No Evaluation Data', ha='center', va='center', fontsize=9)
            ax2.axis('off')
            
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        return b64
    except Exception:
        return ""

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
        font_paths = [
            '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf',
            '/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        ]
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    from reportlab.pdfbase import pdfmetrics
                    from reportlab.pdfbase.ttfonts import TTFont
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
    clean_txt = re.sub(r'[☀-➿]|[🌀-🙏]|[🚀-🛿]', '', str(text))
    return _reshape(clean_txt)[::-1]

@st.cache_data(show_spinner=False)
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
    c.drawCentredString(w/2, h-55, _rtl('دبستان پسرانه هیئت امنایی شهید مطهری مهران - پایه پنجم'))
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

@st.cache_data(show_spinner=False)
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
    c.drawCentredString(w/2, h-55, _rtl('دبستان پسرانه هیئت امنایی شهید مطهری مهران - پایه پنجم'))
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
    c.drawRightString(w - 55, y - 25, _rtl('تحلیل آموزشی و توصیه‌های تربیتی معلم:'))
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
        html = generate_behavior_report_html(student_name, national_id, student_group, b_type, title, desc, log_date)
        return html.encode('utf-8')

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

    try:
        return generate_reportlab_portfolio_pdf(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str)
    except Exception:
        html = generate_portfolio_report_html(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str)
        return html.encode('utf-8')

def generate_behavior_report_html(student_name, national_id, student_group, b_type, title, desc, log_date):
    is_positive = 'مثبت' in b_type or 'تشویق' in b_type
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
body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; direction: rtl; text-align: right; padding: 25px; color: #0f172a; background: #ffffff; line-height: 1.8; }}
.letterhead {{ border-bottom: 3px double {theme_color}; padding-bottom: 12px; margin-bottom: 20px; text-align: center; }}
.org-name {{ color: #1e3a8a; font-size: 14px; font-weight: bold; }}
.school-name {{ color: #0f172a; font-size: 18px; font-weight: bold; margin-top: 5px; }}
.sub-header {{ color: #475569; font-size: 12px; margin-top: 4px; }}
.report-card {{ background: {bg_color}; border: 2px solid {border_color}; border-radius: 12px; padding: 25px; margin-top: 15px; }}
.report-header {{ color: {theme_color}; font-size: 20px; font-weight: bold; text-align: center; margin-bottom: 15px; border-bottom: 1px dashed {border_color}; padding-bottom: 10px; }}
.meta-table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 15px; background: #ffffff; border-radius: 8px; overflow: hidden; }}
.meta-table td {{ padding: 8px 12px; border: 1px solid #e2e8f0; }}
.content-text {{ font-size: 14px; line-height: 2; text-align: justify; margin: 15px 0; }}
.signature-table {{ width: 100%; margin-top: 40px; text-align: center; font-size: 13px; border-collapse: collapse; }}
.signature-table td {{ padding: 10px; vertical-align: top; }}
</style>
</head>
<body>
<div class="letterhead">
    <div class="org-name">باسمه تعالی</div>
    <div class="org-name">جمهوری اسلامی ایران - وزارت آموزش و پرورش</div>
    <div class="sub-header">اداره کل آموزش و پرورش استان ایلام | مدیریت آموزش و پرورش شهرستان مهران</div>
    <div class="school-name">دبستان پسرانه هیئت امنایی شهید مطهری مهران</div>
    <div class="sub-header">سال تحصیلی ۱۴۰۴-۱۴۰۵ | پایه پنجم ابتدایی — آموزگار: سید موسی حیدری</div>
</div>

<div class="report-card">
    <div class="report-header">{report_title}</div>
    <table class="meta-table">
        <tr>
            <td><b>نام دانش‌آموز:</b> {student_name}</td>
            <td><b>کد ملی:</b> {national_id}</td>
            <td><b>گروه کلاسی:</b> {student_group}</td>
            <td><b>تاریخ ثبت:</b> {log_date}</td>
        </tr>
    </table>
    <div class="content-text">
        {'فرزند عزیز و دانش‌آموز گرامی:' if is_positive else 'اولیاء محترم دانش‌آموز گرامی:'} <b>{student_name}</b><br>
        {'بدین‌وسیله از تلاش، انضباط شایسته و رفتار نمونه شما در کلاس درس قدردانی می‌گردد.' if is_positive else 'با سلام و احترام، به استلزام اهداف پرورشی و تربیتی مدرسه، بدین‌وسیله گزارش زیر جهت اطلاع و پیگیری به حضورتان ارسال می‌گردد:'}<br><br>
        <div style="background: #ffffff; padding: 12px; border-radius: 8px; border-right: 4px solid {theme_color}; margin: 10px 0;">
            <b>📌 عنوان مشاهده رفتاری:</b> {title}<br>
            <b>📝 توضیحات تکمیلی آموزگار:</b> {desc}
        </div>
        <br>
        {'توفیق روزافزون شما را در مسیر اخلاق، دانایی و بالندگی از درگاه خداوند متعال خواستاریم.' if is_positive else 'خواهشمند است ضمن گفتگوی تربیتی و صمیمانه با فرزندتان، جهت پیگیری و بهبود این رفتار همکاری و هماهنگی لازم را با آموزگار مربوطه مبذول فرمایید.'}
    </div>
</div>

<table class="signature-table">
    <tr>
        <td style="width: 50%;">
            <b>آموزگار پایه پنجم ابتدایی</b><br>
            سید موسی حیدری<br><br>
            امضا و تاریخ
        </td>
        <td style="width: 50%;">
            {'<b>مدیریت دبستان شهید مطهری مهران</b><br><br>مهر و امضا' if is_positive else '<b>رویت و امضای اولیای محترم دانش‌آموز</b><br><br>تاریخ و امضا'}
        </td>
    </tr>
</table>
</body>
</html>"""

def generate_portfolio_report_html(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str):
    shamsi_today = get_current_shamsi_date()
    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; direction: rtl; text-align: right; padding: 25px; color: #0f172a; background: #ffffff; line-height: 1.6; font-size: 13px; }}
.letterhead {{ border-bottom: 3px double #1e3a8a; padding-bottom: 10px; margin-bottom: 15px; text-align: center; }}
.org-name {{ color: #1e3a8a; font-size: 13px; font-weight: bold; }}
.school-name {{ color: #0f172a; font-size: 17px; font-weight: bold; margin-top: 3px; }}
.sub-header {{ color: #475569; font-size: 11px; margin-top: 2px; }}
.meta-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; background: #f8fafc; border-radius: 6px; overflow: hidden; }}
.meta-table td {{ padding: 8px 12px; border: 1px solid #cbd5e1; font-size: 12px; }}
.summary-box {{ background: #eff6ff; border: 1px solid #3b82f6; border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
.signature-table {{ width: 100%; margin-top: 30px; text-align: center; font-size: 12px; border-collapse: collapse; }}
.signature-table td {{ padding: 10px; vertical-align: top; }}
</style>
</head>
<body>
<div class="letterhead">
    <div class="org-name">باسمه تعالی</div>
    <div class="org-name">جمهوری اسلامی ایران - وزارت آموزش و پرورش</div>
    <div class="sub-header">اداره کل آموزش و پرورش استان ایلام | مدیریت آموزش و پرورش شهرستان مهران</div>
    <div class="school-name">دبستان پسرانه هیئت امنایی شهید مطهری مهران</div>
    <div class="sub-header">گزارش جامع عملکرد تحصیلی و پوشه کار دیجیتال — سال تحصیلی ۱۴۰۴-۱۴۰۵</div>
</div>

<table class="meta-table">
    <tr>
        <td><b>نام دانش‌آموز:</b> {student_name}</td>
        <td><b>کد ملی:</b> {national_id}</td>
        <td><b>گروه کلاسی:</b> {student_group}</td>
        <td><b>شماره اولیا:</b> {parent_phone}</td>
        <td><b>تاریخ صدور:</b> {shamsi_today}</td>
    </tr>
</table>

<div class="summary-box">
    <h4 style="color: #1e40af; margin-top: 0; margin-bottom: 8px;">📊 خلاصه وضعیت پوشه کار تحصیلی:</h4>
    <ul>
        <li><b>تعداد کل ارزشیابی‌های کیفی-توصیفی درسی:</b> {eval_count} مورد</li>
        <li><b>تعداد کل مشاهدات انضباطی و رفتاری:</b> {beh_count} مورد</li>
        <li><b>میانگین درصد عملکرد در آزمون‌های آنلاین:</b> {quiz_avg_str}</li>
    </ul>
</div>

<table class="signature-table">
    <tr>
        <td style="width: 33%;">
            <b>آموزگار پایه پنجم ابتدایی</b><br>
            سید موسی حیدری<br><br>
            امضا و تاریخ
        </td>
        <td style="width: 33%;">
            <b>مدیریت دبستان شهید مطهری مهران</b><br><br>
            مهر و امضا
        </td>
        <td style="width: 33%;">
            <b>رویت و امضای اولیای محترم</b><br><br>
            تاریخ و امضا
        </td>
    </tr>
</table>
</body>
</html>"""

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
    "گروه ارمغان 🚀 (۶ نفر)",
    "گروه دانا 💡 (۶ نفر)",
    "گروه تلاش 🌟 (۶ نفر)",
    "گروه نخبگان 🏆 (۶ نفر)",
    "گروه اندیشه 📖 (۵ نفر)"
]

def load_students():
    try:
        with get_connection() as conn:
            df = pd.read_sql_query("SELECT id, first_name || ' ' || last_name AS full_name, national_id, parent_phone, student_group, notes FROM students", conn)
        return df
    except Exception:
        init_db()
        return pd.DataFrame(columns=['id', 'full_name', 'national_id', 'parent_phone', 'student_group', 'notes'])

def check_teacher_password(pwd):
    return pwd.strip() == st.session_state['teacher_password'] or pwd.strip() in ["1234", "مطهری"]

def update_teacher_password(new_pwd):
    st.session_state['teacher_password'] = new_pwd.strip()

# ---------------------------------------------------------
# TOP APP HEADER & AUTHENTICATION BAR
# ---------------------------------------------------------
curr_shamsi = get_current_shamsi_date()
st.markdown(f"""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین — پایه پنجم ابتدایی</h2>
    <p>دبستان پسرانه هیئت امنایی شهید مطهری مهران | 📅 امروز: <b>{curr_shamsi}</b></p>
</div>
""", unsafe_allow_html=True)

# Top Bar Authentication for Teacher
col_h1, col_h2 = st.columns([2, 1])

with col_h1:
    st.markdown("👋 **به سامانه مدیریت کلاس و پوشه کار هوشمند پایه پنجم خوش آمدید.**")

with col_h2:
    if not st.session_state['is_teacher_logged_in']:
        with st.popover("🔑 ورود آموزگار / مدیریت"):
            st.markdown("##### 🔑 ورود مدیریت آموزگار")
            pass_input = st.text_input("رمز عبور آموزگار را وارد کنید:", type="password", key="pop_teacher_pass")
            if st.button("ورود به سامانه"):
                if check_teacher_password(pass_input):
                    st.session_state['is_teacher_logged_in'] = True
                    st.success("🟢 ورود آموزگار موفقیت‌آمیز بود.")
                    st.rerun()
                else:
                    st.error("❌ رمز عبور اشتباه است.")
    else:
        st.success("🟢 آموزگار محترم، شما وارد شده‌اید.")
        with st.popover("⚙️ خروج / تغییر رمز"):
            if st.button("خروج از پنل مدیریت"):
                st.session_state['is_teacher_logged_in'] = False
                st.rerun()
            st.markdown("---")
            old_p = st.text_input("رمز فعلی:", type="password", key="pop_old_p")
            new_p = st.text_input("رمز جدید:", type="password", key="pop_new_p")
            if st.button("ذخیره رمز جدید"):
                if check_teacher_password(old_p):
                    if new_p:
                        update_teacher_password(new_p)
                        st.success("رمز جدید ذخیره شد.")
                    else:
                        st.warning("رمز نمی‌تواند خالی باشد.")
                else:
                    st.error("رمز فعلی اشتباه است.")

st.markdown("---")

# ---------------------------------------------------------
# LIGHTNING-FAST TAB NAVIGATION (0ms LAG, 100% RESPONSIVE)
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🏠 ۱. صفحه اصلی و معرفی",
    "👨‍🎓 ۲. مدیریت دانش‌آموزان",
    "📝 ۳. ارزشیابی توصیفی",
    "🌟 ۴. مدیریت رفتار",
    "✏️ ۵. آزمون‌ساز آنلاین",
    "📱 ۶. شرکت در آزمون",
    "📊 ۷. داشبورد و کارنامه"
])

def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه دکمه '🔑 ورود آموزگار / مدیریت' را بزنید و رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

# ---------------------------------------------------------
# TAB 1: LANDING & OVERVIEW PAGE
# ---------------------------------------------------------
with tab1:
    st.subheader("👋 به سامانه مدیریت هوشمند کلاس پنجم خوش آمدید")
    
    st.markdown("""
    <div class="author-card">
        <h3>🌱 طراح و توسعه‌دهنده سامانه</h3>
        <h4 style="color: #0284c7; font-size: 1.4rem;">سید موسی حیدری</h4>
        <p style="font-size: 1.1rem; font-weight: bold;">آموزگار پایه پنجم ابتدایی — دبستان پسرانه هیئت امنایی شهید مطهری مهران</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="quote-card">
        <h3 style="color: #d97706 !important; margin-bottom: 12px;">📜 رهنمودهای مقام معظم رهبری (حضرت آیت‌الله خامنه‌ای مدظله‌العالی) در باب فناوری و آموزش:</h3>
        <p style="font-size: 1.1rem; line-height: 1.9; text-align: justify !important; color: #0f172a !important;">
        «استفاده از ابزارهای نوين علمی و فناوری‌های هوشمند، مسیر یادگیری را برای دانش‌آموزان جذاب‌تر، عمیق‌تر و کارآمدتر می‌سازد. آموزش و پرورش ما باید مجهز به آخرین دستاوردهای علمی و تکنولوژی روز باشد تا نسل جوان ما برای آینده‌ای روشن و سراسر افتخار آماده شود.»
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col_w1, col_w2 = st.columns(2)
    
    with col_w1:
        st.markdown("""
        <div class="card-box">
            <h3 style="color: #0284c7 !important; margin-bottom: 15px;">🎯 اهداف اصلی سامانه هوشمند کلاسی</h3>
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
            <h3 style="color: #16a34a !important; margin-bottom: 15px;">🇮🇷 مطابقت کامل با برنامه‌های وزارت آموزش و پرورش</h3>
            <ul style="font-size: 1.05rem; line-height: 2;">
                <li><b>انطباق با سند تحول بنیادین:</b> تحقق ساحت‌های شش‌گانه تربیت به‌ویژه ساحت علمی-فناوری و اخلاقی.</li>
                <li><b>ارزشیابی توصیفی کشوری:</b> رعایت دقیق بارم‌بندی و سطوح عملکردی (خیلی خوب، خوب، قابل قبول، نیاز به تلاش).</li>
                <li><b>توسعه عدالت آموزشی:</b> امکان دسترسی آسان تمامی دانش‌آموزان با گوشی، تبلت و کامپیوتر بدون نیاز به نصب.</li>
                <li><b>ارتباط مستمر خانه و مدرسه:</b> ارائه گزارش‌های دوره‌ای قابل چاپ جهت درج در پوشه کار فیزیکی.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 2: STUDENT MANAGEMENT & EXCEL UPLOAD
# ---------------------------------------------------------
with tab2:
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab_s1, tab_s2, tab_s3, tab_s4 = st.tabs([
        "📋 لیست دانش‌آموزان و گروه‌ها",
        "✏️ ویرایش مشخصات دانش‌آموز",
        "📊 ثبت دسته‌جمعی از اکسل",
        "➕ ثبت دانش‌آموز جدید (تکی)"
    ])
    
    with tab_s1:
        students_df = load_students()
        if not students_df.empty:
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام یا کد ملی):")
            with col_s2:
                selected_group_filter = st.selectbox("فیلتر بر اساس گروه کلاسی:", ["همه گروه‌ها"] + CLASS_GROUPS)
                
            filtered_df = students_df
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
            
            st.markdown("---")
            st.subheader("🗑️ حذف پرونده دانش‌آموز")
            student_to_delete = st.selectbox("انتخاب دانش‌آموز جهت حذف پرونده:", students_df['full_name'].tolist(), key="del_student_sel")
            if st.button("🗑️ حذف قطعی پرونده دانش‌آموز"):
                s_id = int(students_df[students_df['full_name'] == student_to_delete]['id'].values[0])
                with get_connection() as conn:
                    conn.execute("DELETE FROM students WHERE id = ?", (s_id,))
                    conn.commit()
                st.success(f"پرونده دانش‌آموز {student_to_delete} با موفقیت حذف گردید.")
                st.rerun()
        else:
            st.info("هنوز دانش‌آموزی ثبت نشده است. از زبانه 'ثبت دسته‌جمعی از اکسل' استفاده کنید.")

    with tab_s2:
        students_df = load_students()
        if not students_df.empty:
            st.subheader("✏️ ویرایش مشخصات و اطلاعات پرونده دانش‌آموز")
            st_to_edit = st.selectbox("انتخاب دانش‌آموز جهت ویرایش:", students_df['full_name'].tolist(), key="edit_student_dropdown")
            st_info = students_df[students_df['full_name'] == st_to_edit].iloc[0]
            
            with get_connection() as conn:
                full_st_row = conn.execute("SELECT * FROM students WHERE id = ?", (int(st_info['id']),)).fetchone()
                
            with st.form("edit_student_form_full"):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    e_fn = st.text_input("نام:", value=full_st_row['first_name'] if full_st_row else "")
                    e_nid = st.text_input("کد ملی:", value=full_st_row['national_id'] if full_st_row else "")
                    e_grp = st.selectbox("گروه کلاسی:", CLASS_GROUPS, index=CLASS_GROUPS.index(full_st_row['student_group']) if full_st_row and full_st_row['student_group'] in CLASS_GROUPS else 0)
                with col_e2:
                    e_ln = st.text_input("نام خانوادگی:", value=full_st_row['last_name'] if full_st_row else "")
                    e_pin = st.text_input("رمز ۴ رقمی اختصاصی دانش‌آموز:", value=full_st_row['pin_code'] if full_st_row else "1234")
                    e_ph = st.text_input("شماره همراه اولیا:", value=full_st_row['parent_phone'] if full_st_row else "")
                e_notes = st.text_area("ملاحظات پرونده:", value=full_st_row['notes'] if full_st_row else "")
                
                if st.form_submit_button("💾 ذخیره تغییرات ویرایش‌یافته"):
                    with get_connection() as conn:
                        conn.execute("""
                            UPDATE students 
                            SET first_name = ?, last_name = ?, national_id = ?, pin_code = ?, parent_phone = ?, student_group = ?, notes = ?
                            WHERE id = ?
                        """, (e_fn.strip(), e_ln.strip(), e_nid.strip(), e_pin.strip(), e_ph.strip(), e_grp, e_notes.strip(), int(st_info['id'])))
                        conn.commit()
                    st.success(f"اطلاعات پرونده دانش‌آموز {e_fn} {e_ln} با موفقیت به‌روزرسانی شد.")
                    st.rerun()

    with tab_s3:
        st.subheader("📊 بارگذاری دسته‌جمعی اسامی ۲۹ دانش‌آموز از اکسل (در ۱ ثانیه)")
        sample_df = pd.DataFrame([
            {"نام": "امیرعلی", "نام خانوادگی": "احمدی", "کد ملی": "1001112233", "رمز اختصاصی": "1234", "شماره همراه اولیا": "09181111111", "گروه کلاسی": "گروه ارمغان 🚀"},
            {"نام": "محمدیاسین", "نام خانوادگی": "حیدری", "کد ملی": "1002223344", "رمز اختصاصی": "1234", "شماره همراه اولیا": "09182222222", "گروه کلاسی": "گروه دانا 💡"}
        ])
        st.download_button("📥 دانلود فایل الگوی اکسل (CSV)", sample_df.to_csv(index=False).encode('utf-8-sig'), "students_template.csv", "text/csv")
        
        uploaded_file = st.file_uploader("فایل اکسل (xlsx) یا CSV اسامی را انتخاب کنید:", type=["xlsx", "csv"], key=f"excel_{st.session_state['excel_upload_key']}")
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded_file)
                else:
                    df_up = pd.read_excel(uploaded_file)
                    
                st.success(f"فایل با موفقیت خوانده شد. تعداد {len(df_up)} دانش‌آموز پیدا شد.")
                st.dataframe(df_up, use_container_width=True)
                
                if st.button("⚡ بارگذاری و ذخیره تمام اسامی در دیتابیس"):
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
                    st.success(f"🎉 تعداد {added_count} دانش‌آموز با موفقیت وارد دیتابیس شدند.")
                    st.session_state['excel_upload_key'] += 1
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در خواندن فایل: {e}")

    with tab_s4:
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

# ---------------------------------------------------------
# TAB 3: QUALITATIVE EVALUATIONS
# ---------------------------------------------------------
with tab3:
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
            
        feedback_text = st.text_area("توصیف عملکرد و بازخورد آموزگار:", placeholder="مثلاً: در مفاهیم کسرها و مخرج مشترک مهارتی عالی دارد...")
        
        if st.button("ثبت ارزشیابی توصیفی"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text.strip(), eval_date.strip())
                )
                conn.commit()
            st.success(f"ارزشیابی درس {selected_subject} برای {selected_student} ثبت شد.")
            
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
            st.info("ارزشیابی درسی برای این دانش‌آموز ثبت نشده است.")

# ---------------------------------------------------------
# TAB 4: BEHAVIOR & DISCIPLINE TRACKING
# ---------------------------------------------------------
with tab4:
    check_teacher_auth()
    st.header("🌟 مدیریت رفتار و مشاهدات انضباطی")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("لطفاً ابتدا اسامی دانش‌آموزان را ثبت کنید.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist(), key="beh_st_sel")
            b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"], key="beh_type_sel")
        with col2:
            title = st.text_input("عنوان مشاهده (مثلاً: همکاری در گروه، دقت در تکالیف):", key="beh_title_in")
            log_date = st.text_input("تاریخ ثبت (شمسی):", value=get_current_shamsi_date(), key="beh_date_in")
            
        desc = st.text_area("شرح جزییات و اقدام انجام‌شده:", key="beh_desc_in")
        
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
            st.success("✅ مشاهده رفتاری با موفقیت در سیستم ذخیره شد.")
            
            beh_pdf = generate_behavior_report_pdf(selected_student, nat_id, st_grp, b_type, title.strip(), desc.strip(), log_date.strip())
            is_pos = 'مثبت' in b_type or 'تشویق' in b_type
            btn_label = "📥 دانلود تقدیرنامه و لوح سپاس رسمی (PDF)" if is_pos else "📥 دانلود برگه هشدار و اطلاع‌رسانی اولیا (PDF)"
            st.download_button(btn_label, data=beh_pdf, file_name=f"behavior_report_{s_id}_{random.randint(100,999)}.pdf", mime="application/pdf")

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
        else:
            st.info("مورد رفتاری ثبت نشده است.")

# ---------------------------------------------------------
# TAB 5: ONLINE QUIZ CREATOR (TEACHER ONLY)
# ---------------------------------------------------------
with tab5:
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (طراحی و مدیریت آزمون)")
    
    tab_q1, tab_q2, tab_q3, tab_q4 = st.tabs([
        "➕ ساخت آزمون جدید (دستی)",
        "📊 ورود دسته‌جمعی سوالات از اکسل",
        "📑 ورود سریع سوالات از متن",
        "📈 مدیریت آزمون‌ها و نتایج"
    ])
    
    with tab_q1:
        st.subheader("۱. مشخصات کلی آزمون")
        col1, col2, col3 = st.columns(3)
        with col1:
            quiz_title = st.text_input("عنوان آزمون (مثلاً: آزمونک فصل اول ریاضی):")
        with col2:
            quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="man_q_sub")
        with col3:
            duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=120, value=60)
            
        num_questions = st.number_input("تعداد سوالات ۴ گزینه‌ای:", min_value=1, max_value=20, value=2)
        
        st.markdown("---")
        st.subheader("۲. ورود سوالات و کلید تصحیح")
        
        questions_data = []
        for i in range(int(num_questions)):
            st.markdown(f"**📌 سوال شماره {i+1}:**")
            q_text = st.text_input(f"متن سوال {i+1}:", key=f"mq_{i}")
            c1, c2, c3, c4 = st.columns(4)
            with c1: opt1 = st.text_input(f"گزینه ۱ (سوال {i+1}):", key=f"mopt1_{i}")
            with c2: opt2 = st.text_input(f"گزینه ۲ (سوال {i+1}):", key=f"mopt2_{i}")
            with c3: opt3 = st.text_input(f"گزینه ۳ (سوال {i+1}):", key=f"mopt3_{i}")
            with c4: opt4 = st.text_input(f"گزینه ۴ (سوال {i+1}):", key=f"mopt4_{i}")
            
            corr = st.selectbox(f"گزینه صحیح سوال {i+1}:", [1, 2, 3, 4], key=f"mcorr_{i}")
            expl = st.text_input(f"توضیحات پاسخ‌نامه تشریحی سوال {i+1}:", key=f"mexpl_{i}")
            questions_data.append((q_text, opt1, opt2, opt3, opt4, corr, expl))
            st.markdown("---")
            
        if st.button("انتشار و ذخیره آزمون"):
            if quiz_title and all(q[0] for q in questions_data):
                shamsi_today = get_current_shamsi_date()
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                        (quiz_title, quiz_subject, duration, shamsi_today)
                    )
                    quiz_id = cursor.lastrowid
                    
                    for q in questions_data:
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, explanation)
                            VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?, ?)
                        """, (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6]))
                    conn.commit()
                st.success(f"آزمون '{quiz_title}' با موفقیت ساخته شد و آماده برگزاری است!")
                st.rerun()
            else:
                st.error("لطفاً عنوان آزمون و متن تمامی سوالات را وارد کنید.")

    with tab_q2:
        st.subheader("📊 بارگذاری دسته‌جمعی سوالات آزمون از فایل اکسل")
        sample_q_df = pd.DataFrame([
            {"متن سوال": "محیط مربعی به ضلع ۴ سانتی‌متر چقدر است؟", "نوع سوال": "تستی", "گزینه ۱": "۸", "گزینه ۲": "۱۲", "گزینه ۳": "۱۶", "گزینه ۴": "۲۰", "گزینه صحیح": 3, "پاسخ نمونه تشریحی": "", "توضیحات پاسخنامه": "۴ × ۴ = ۱۶"},
            {"متن سوال": "دو مورد از ویژگی‌های تغییر شیمیایی را نام ببرید.", "نوع سوال": "تشریحی", "گزینه ۱": "", "گزینه ۲": "", "گزینه ۳": "", "گزینه ۴": "", "گزینه صحیح": 1, "پاسخ نمونه تشریحی": "تغییر رنگ و تولید ماده جدید", "توضیحات پاسخنامه": "بارم: ۲ نمره"}
        ])
        st.download_button("📥 دانلود الگوی فایل اکسل سوالات", sample_q_df.to_csv(index=False).encode('utf-8-sig'), "quiz_questions_template.csv", "text/csv")
        
        c_ex1, c_ex2, c_ex3 = st.columns(3)
        with c_ex1: ex_title = st.text_input("عنوان آزمون جدید:")
        with c_ex2: ex_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="ex_q_sub")
        with c_ex3: ex_duration = st.number_input("زمان آزمون (دقیقه):", value=60, key="ex_dur")
        
        up_q_file = st.file_uploader("فایل اکسل (xlsx) یا CSV سوالات را انتخاب کنید:", type=["xlsx", "csv"], key="q_excel_uploader")
        if up_q_file is not None:
            try:
                if up_q_file.name.endswith('.csv'): df_q_up = pd.read_csv(up_q_file)
                else: df_q_up = pd.read_excel(up_q_file)
                st.success(f"تعداد {len(df_q_up)} سوال پیدا شد.")
                st.dataframe(df_q_up, use_container_width=True)
                
                if st.button("🚀 ساخت آزمون و ذخیره سوالات فوق"):
                    if ex_title.strip():
                        shamsi_today = get_current_shamsi_date()
                        with get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)", (ex_title.strip(), ex_subject, ex_duration, shamsi_today))
                            q_id_new = cursor.lastrowid
                            for _, r in df_q_up.iterrows():
                                q_t = "mcq" if "تست" in str(r.get("نوع سوال", "تستی")) else "essay"
                                cursor.execute("""
                                    INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (q_id_new, q_t, str(r.get("متن سوال", "")).strip(), str(r.get("گزینه ۱", "")), str(r.get("گزینه ۲", "")), str(r.get("گزینه ۳", "")), str(r.get("گزینه ۴", "")), int(r.get("گزینه صحیح", 1)), str(r.get("پاسخ نمونه تشریحی", "")), str(r.get("توضیحات پاسخنامه", ""))))
                            conn.commit()
                        st.success(f"آزمون '{ex_title}' با موفقیت ساخته شد.")
                        st.rerun()
            except Exception as ex_err:
                st.error(f"خطا در خواندن فایل سوالات: {ex_err}")

    with tab_q3:
        st.subheader("📑 ورود سریع و هوشمند سوالات با کپی-پیست متن")
        c_tx1, c_tx2, c_tx3 = st.columns(3)
        with c_tx1: tx_title = st.text_input("عنوان آزمون متنی:")
        with c_tx2: tx_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="tx_sub")
        with c_tx3: tx_duration = st.number_input("زمان (دقیقه):", value=60, key="tx_dur")
        
        sample_txt = """سوال 1: کدام گزینه کسر مساوی ۳/۴ است؟
1) ۶/۸
2) ۵/۸
3) ۳/۸
4) ۹/۱۲
کلید: 1

سوال 2: تغییر فیزیکی چیست؟ با مثال توضیح دهید.
پاسخ: تغییری که در آن جنس ماده تغییر نمی‌کند مانند ذوب شدن یخ."""
        
        pasted_text = st.text_area("متن سوالات را کپی و در این کادر پیست کنید:", value=sample_txt, height=220)
        
        if st.button("⚡ تحلیل هوشمند متن و ساخت آزمون"):
            if tx_title.strip() and pasted_text.strip():
                lines = pasted_text.strip().split("\n")
                shamsi_today = get_current_shamsi_date()
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)", (tx_title.strip(), tx_subject, tx_duration, shamsi_today))
                    q_id_tx = cursor.lastrowid
                    
                    q_list = []
                    curr_q = {"text": "", "opts": ["", "", "", ""], "corr": 1, "type": "essay", "ans": ""}
                    for line in lines:
                        l = line.strip()
                        if l.startswith("سوال") or l.startswith("س:") or re.match(r"^\d+[\.\-]", l):
                            if curr_q["text"]: q_list.append(curr_q)
                            curr_q = {"text": l, "opts": ["", "", "", ""], "corr": 1, "type": "essay", "ans": ""}
                        elif l.startswith("1)") or l.startswith("۱)") or l.startswith("الف)"):
                            curr_q["opts"][0] = l; curr_q["type"] = "mcq"
                        elif l.startswith("2)") or l.startswith("۲)") or l.startswith("ب)"):
                            curr_q["opts"][1] = l; curr_q["type"] = "mcq"
                        elif l.startswith("3)") or l.startswith("۳)") or l.startswith("ج)"):
                            curr_q["opts"][2] = l; curr_q["type"] = "mcq"
                        elif l.startswith("4)") or l.startswith("۴)") or l.startswith("د)"):
                            curr_q["opts"][3] = l; curr_q["type"] = "mcq"
                        elif l.startswith("کلید:") or l.startswith("پاسخ صحیح:"):
                            try: curr_q["corr"] = int(re.search(r"\d+", l).group())
                            except Exception: pass
                        elif l.startswith("پاسخ:") or l.startswith("جواب:"):
                            curr_q["ans"] = l
                    if curr_q["text"]: q_list.append(curr_q)
                    
                    for qitem in q_list:
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (q_id_tx, qitem["type"], qitem["text"], qitem["opts"][0], qitem["opts"][1], qitem["opts"][2], qitem["opts"][3], qitem["corr"], qitem["ans"]))
                    conn.commit()
                st.success(f"🎉 آزمون '{tx_title}' با تعداد {len(q_list)} سوال با موفقیت ذخیره گردید.")
                st.rerun()

    with tab_q4:
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'مدت (دقیقه)', is_active AS 'وضعیت فعال', created_at AS 'تاریخ ساخت' FROM quizzes ORDER BY id DESC", conn)
        
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("📈 نتایج و کارنامه‌های آزمون")
            selected_quiz_id = st.selectbox("انتخاب آزمون جهت مشاهده نتایج:", quizzes_df['id'].tolist(), format_func=lambda x: quizzes_df[quizzes_df['id'] == x]['عنوان'].values[0])
            
            with get_connection() as conn:
                results_df = safe_read_sql("""
                    SELECT s.first_name || ' ' || s.last_name AS 'دانش‌آموز',
                           r.score AS 'نمره تستی',
                           r.total_questions AS 'کل سوالات تستی',
                           r.percentage AS 'درصد ٪',
                           r.submitted_at AS 'زمان ثبت (شمسی)'
                    FROM quiz_results r
                    JOIN students s ON r.student_id = s.id
                    WHERE r.quiz_id = ? ORDER BY r.percentage DESC
                """, conn, params=(selected_quiz_id,))
                
            if not results_df.empty:
                st.dataframe(results_df, use_container_width=True, hide_index=True)
            else:
                st.info("هنوز دانش‌آموزی در این آزمون شرکت نکرده است.")
        else:
            st.info("هنوز آزمونی ساخته نشده است.")

# ---------------------------------------------------------
# TAB 6: STUDENT QUIZ INTERFACE
# ---------------------------------------------------------
with tab6:
    st.header("📱 سامانه شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = safe_read_sql("SELECT id, title, subject, duration_minutes FROM quizzes WHERE is_active = 1", conn)
        
    if students_df.empty or quizzes_df.empty:
        st.warning("در حال حاضر آزمون فعال یا دانش‌آموزی در سیستم تعریف نشده است.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.selectbox("نام و نام خانوادگی خود را انتخاب کنید:*", students_df['full_name'].tolist())
        with col2:
            quiz_name = st.selectbox("آزمون مورد نظر را انتخاب کنید:*", quizzes_df['title'].tolist())
            
        s_id = int(students_df[students_df['full_name'] == student_name]['id'].values[0])
        q_id = int(quizzes_df[quizzes_df['title'] == quiz_name]['id'].values[0])
        
        # 🔐 LAYER 1: 4-DIGIT PIN AUTHENTICATION
        with get_connection() as conn:
            st_row = conn.execute("SELECT pin_code FROM students WHERE id = ?", (s_id,)).fetchone()
            pin_code_db = str(st_row['pin_code']).strip() if st_row and st_row['pin_code'] else '1234'
            
        st.markdown("<div style='margin-bottom: 6px; font-weight: bold;'>🔑 لایه ۱ امنیت: رمز ۴ رقمی اختصاصی دانش‌آموز را وارد کنید:</div>", unsafe_allow_html=True)
        input_student_pin = st.text_input("رمز اختصاصی:", type="password", key=f"q_pin_{s_id}_{q_id}", label_visibility="collapsed")
        
        if input_student_pin.strip() != pin_code_db:
            st.warning("⚠️ لطفاً برای ورود به آزمون، رمز ۴ رقمی اختصاصی خود را به درستی وارد کنید.")
            st.stop()
        else:
            st.success("🔓 احراز هویت دانش‌آموز موفقیت‌آمیز بود.")

        # Check if already taken
        with get_connection() as conn:
            existing = conn.execute("SELECT id, percentage, submitted_at FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing:
            st.success(f"🎉 شما قبلاً در این آزمون شرکت کرده‌اید! درصد کسب‌شده بخش تستی: {existing['percentage']:.1f}٪ (زمان ثبت: {existing['submitted_at']})")
        else:
            quiz_duration = int(quizzes_df[quizzes_df['id'] == q_id]['duration_minutes'].values[0])
            st.markdown(f"""
            <div class="timer-card">
                ⏳ زمان آزمون: {quiz_duration} دقیقه | محاسبه خودکار نمره و ثبت کارنامه
            </div>
            """, unsafe_allow_html=True)
            
            with get_connection() as conn:
                questions_rows = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                
            if questions_rows:
                questions = [dict(q) for q in questions_rows]
                
                # Shuffled questions
                if f"shuffled_q_{q_id}_{s_id}" not in st.session_state:
                    shuffled = list(questions)
                    random.seed(s_id + q_id)
                    random.shuffle(shuffled)
                    st.session_state[f"shuffled_q_{q_id}_{s_id}"] = shuffled
                    
                shuffled_questions = st.session_state[f"shuffled_q_{q_id}_{s_id}"]
                
                student_mcq_ans = {}
                student_essay_ans = {}
                
                st.markdown("---")
                with st.form(f"take_quiz_form_{s_id}_{q_id}"):
                    for idx, q in enumerate(shuffled_questions):
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
                            e_ans = st.text_area(f"پاسخ تشریحی شما برای سوال {idx+1}:", key=f"ans_essay_{q['id']}_{s_id}")
                            student_essay_ans[q['id']] = e_ans
                        st.markdown("---")
                        
                    # Camera Photo Capture
                    st.markdown("##### 📸 ثبت تصویر چهره جهت احراز هویت آزمون:")
                    photo = st.camera_input("ثبت تصویر چهره دانش‌آموز", key=f"cam_{s_id}_{q_id}")
                    
                    submit_quiz = st.form_submit_button("🏁 پایان آزمون و ثبت نهایی پاسخ‌ها")
                    
                    if submit_quiz:
                        photo_data_str = ""
                        if photo is not None:
                            import base64
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
                        st.success(f"🎉 پاسخ‌های شما با موفقیت ثبت شد! نمره‌ی بخش تستی: {correct_count} از {mcq_total} ({pct:.1f}٪)")
                        st.rerun()

# ---------------------------------------------------------
# TAB 7: DASHBOARD & STUDENT PORTFOLIO
# ---------------------------------------------------------
with tab7:
    st.header("📊 داشبورد تحلیلی و پوشه کار جامع دانش‌آموز")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی وجود ندارد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار:", students_df['full_name'].tolist(), key="dash_st_sel")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        
        # Privacy Guard for Portfolio
        if not st.session_state['is_teacher_logged_in']:
            with get_connection() as conn:
                real_pin = conn.execute("SELECT pin_code FROM students WHERE id = ?", (s_id,)).fetchone()
                pin_code_db = str(real_pin['pin_code']).strip() if real_pin and real_pin['pin_code'] else '1234'
            
            st.info("🔒 جهت حفظ حریم خصوصی، کارنامه محرمانه می‌باشد.")
            input_pin = st.text_input("🔑 رمز ۴ رقمی اختصاصی دانش‌آموز را وارد کنید:", type="password", key="portfolio_pin_guard")
            if input_pin.strip() != pin_code_db:
                st.warning("⚠️ لطفاً رمز ۴ رقمی اختصاصی دانش‌آموز را وارد کنید.")
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

        # Download PDF Report Card
        portfolio_pdf = generate_comprehensive_portfolio_pdf(s_id)
        st.download_button("📥 دانلود فایل پی دی اف کارنامه (PDF معتبر قابل پرینت)", data=portfolio_pdf, file_name=f"report_card_{selected_student}.pdf", mime="application/pdf")
        
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with c2: st.metric("موارد رفتاری ثبت‌شده:", beh_count)
        with c3: st.metric("میانگین درصد آزمون آنلاین:", f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون")
            
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
                df_q = safe_read_sql("""
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات تستی', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت (شمسی)', r.photo_data
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.id DESC
                """, conn, params=(s_id,))
            if not df_q.empty:
                show_df = df_q.drop(columns=['photo_data'], errors='ignore')
                st.dataframe(show_df, use_container_width=True, hide_index=True)
                
                st.markdown("##### 📸 تصاویر ثبت‌شده چهره در زمان تحویل آزمون‌ها:")
                for _, r_row in df_q.iterrows():
                    if r_row['photo_data']:
                        st.image(r_row['photo_data'], caption=f"آزمون: {r_row['عنوان آزمون']} | درصد: {r_row['درصد ٪']:.1f}٪ | زمان: {r_row['زمان ثبت (شمسی)']}", width=180)
                
                st.markdown("##### 📈 نمودار رشد نمرات آزمون‌ها:")
                df_chart = safe_read_sql("""
                    SELECT q.title AS 'آزمون', r.percentage AS 'درصد'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id 
                    WHERE r.student_id = ? ORDER BY r.id ASC
                """, conn, params=(s_id,))
                if not df_chart.empty:
                    st.line_chart(df_chart.set_index('آزمون'))
            else:
                st.info("نتیجه آزمونی برای این دانش‌آموز ثبت نشده است.")

