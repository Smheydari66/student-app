import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json
import random
import re
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# ---------------------------------------------------------
# Page Configuration & Modern RTL CSS Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast Persian / RTL CSS (Dark Theme + Crisp White Text)
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    /* Global Base Typography */
    html, body, [class*="st-"], .stMarkdown, p, span, button, input, select, textarea, label, h1, h2, h3, h4, h5, h6 {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #ffffff !important;
    }
    
    /* Force ALL Labels, Paragraphs, Headings to Pure White */
    label, p, span, h1, h2, h3, h4, h5, h6, div[data-testid="stMarkdownContainer"] *, .stRadio label, .stCheckbox label {
        color: #ffffff !important;
        font-weight: 500;
    }
    
    /* Input Fields & Selectboxes - Crisp White Text on Dark Navy Input Box */
    input, select, textarea, div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
    }
    
    /* Dropdown Popover List Items */
    div[data-baseweb="popover"], div[data-baseweb="popover"] *, ul[role="listbox"], li[role="option"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    li[role="option"]:hover {
        background-color: #0284c7 !important;
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
    
    /* Card Styling */
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
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Pure Python Reshaper & ReportLab Helper for Persian PDFs
# ---------------------------------------------------------
ISOLATED = 0; FINAL = 1; MEDIAL = 2; INITIAL = 3
PERSIAN_FORMS = {
    'آ': ('\ufe81', '\ufe82', '\ufe82', '\ufe81'),
    'ا': ('\ufe8d', '\ufe8e', '\ufe8e', '\ufe8d'),
    'ب': ('\ufe8f', '\ufe90', '\ufe92', '\ufe91'),
    'پ': ('\ufb56', '\ufb57', '\ufb59', '\ufb58'),
    'ت': ('\ufe95', '\ufe96', '\ufe98', '\ufe97'),
    'ث': ('\ufe99', '\ufe9a', '\ufe9c', '\ufe9b'),
    'ج': ('\ufe9d', '\ufe9e', '\ufea0', '\ufe9f'),
    'چ': ('\ufb7a', '\ufb7b', '\ufb7d', '\ufb7c'),
    'ح': ('\ufea1', '\ufea2', '\ufea4', '\ufea3'),
    'خ': ('\ufea5', '\ufea6', '\ufea8', '\ufea7'),
    'د': ('\ufea9', '\ufeaa', '\ufeaa', '\ufea9'),
    'ذ': ('\ufeab', '\ufeac', '\ufeac', '\ufeab'),
    'ر': ('\ufead', '\ufeae', '\ufeae', '\ufead'),
    'ز': ('\ufeaf', '\ufeb0', '\ufeb0', '\ufeaf'),
    'ژ': ('\ufb8a', '\ufb8b', '\ufb8b', '\ufb8a'),
    'س': ('\ufeb1', '\ufeb2', '\ufeb4', '\ufeb3'),
    'ش': ('\ufeb5', '\ufeb6', '\ufeb8', '\ufeb7'),
    'ص': ('\ufeb9', '\ufeba', '\ufebc', '\ufebb'),
    'ض': ('\ufebd', '\ufebe', '\ufec0', '\ufebf'),
    'ط': ('\ufec1', '\ufec2', '\ufec4', '\ufec3'),
    'ظ': ('\ufec5', '\ufec6', '\ufec8', '\ufec7'),
    'ع': ('\ufec9', '\ufeca', '\ufecc', '\ufecb'),
    'غ': ('\ufecd', '\ufece', '\ufed0', '\ufecf'),
    'ف': ('\uffed', '\uffee', '\ufed3', '\ufed2'),
    'ق': ('\ufed5', '\ufed6', '\ufed8', '\ufed7'),
    'ک': ('\ufed9', '\ufeda', '\ufedc', '\ufedb'),
    'گ': ('\ufb92', '\ufb93', '\ufb95', '\ufb94'),
    'ل': ('\ufede', '\ufedf', '\ufee1', '\ufee0'),
    'م': ('\ufee2', '\ufee3', '\ufee5', '\ufee4'),
    'ن': ('\ufee6', '\ufee7', '\ufee9', '\ufeef'),
    'و': ('\ufeee', '\ufeef', '\ufeef', '\ufeee'),
    'ه': ('\ufef0', '\ufef1', '\ufef3', '\ufef2'),
    'ی': ('\ufef1', '\ufef2', '\ufef4', '\ufef3'),
}
NON_CONNECTING_AFTER = set('آادذرزژو')

def reshape_persian_word(word):
    if not word: return ''
    res = []
    n = len(word)
    for i, ch in enumerate(word):
        if ch not in PERSIAN_FORMS:
            res.append(ch)
            continue
        forms = PERSIAN_FORMS[ch]
        prev_ch = word[i-1] if i > 0 else None
        next_ch = word[i+1] if i < n-1 else None
        can_connect_prev = (prev_ch in PERSIAN_FORMS and prev_ch not in NON_CONNECTING_AFTER)
        can_connect_next = (next_ch in PERSIAN_FORMS)
        if can_connect_prev and can_connect_next:
            res.append(forms[MEDIAL])
        elif can_connect_prev:
            res.append(forms[FINAL])
        elif can_connect_next:
            res.append(forms[INITIAL])
        else:
            res.append(forms[ISOLATED])
    return ''.join(res)

def rtl(text):
    if not text: return ''
    words = str(text).split(' ')
    reshaped_words = []
    for w in words:
        sh = reshape_persian_word(w)
        reshaped_words.append(sh[::-1])
    return ' '.join(reshaped_words[::-1])

# Register Persian Font for ReportLab
_PERSIAN_FONT_REGISTERED = False
try:
    font_path = '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf'
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('PersianFont', font_path))
        _PERSIAN_FONT_REGISTERED = True
except Exception:
    pass

# PDF Report 1: Behavior & Discipline
def generate_behavior_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    fn = 'PersianFont' if _PERSIAN_FONT_REGISTERED else 'Helvetica'
    
    # Header bar
    c.setFillColor(colors.HexColor('#0f172a'))
    c.rect(0, h-80, w, 80, fill=1, stroke=0)
    
    c.setFillColor(colors.HexColor('#ffffff'))
    c.setFont(fn, 13)
    c.drawCentredString(w/2, h-32, rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
    c.setFont(fn, 11)
    c.drawCentredString(w/2, h-56, rtl('دبستان پسرانه شهید مطهری مهران - پایه پنجم ابتدایی'))
    
    is_pos = 'مثبت' in b_type or 'تشویق' in b_type
    rep_title = 'تقدیرنامه و لوح سپاس انضباطی کلاسی' if is_pos else 'کارت اطلاع‌رسانی و هشدار انضباطی اولیا'
    
    c.setFillColor(colors.HexColor('#1e3a8a'))
    c.setFont(fn, 14)
    c.drawCentredString(w/2, h-115, rtl(rep_title))
    
    # Student Info Table Box
    c.setFillColor(colors.HexColor('#f1f5f9'))
    c.rect(40, h-190, w-80, 55, fill=1, stroke=1)
    
    c.setFillColor(colors.HexColor('#0f172a'))
    c.setFont(fn, 10)
    c.drawRightString(w - 55, h - 155, rtl(f'نام دانش‌آموز: {student_name}'))
    c.drawRightString(w - 230, h - 155, rtl(f'کد ملی: {national_id}'))
    c.drawRightString(w - 380, h - 155, rtl(f'گروه کلاسی: {student_group}'))
    c.drawRightString(w - 55, h - 175, rtl(f'تاریخ ثبت: {log_date}'))
    
    # Content Box
    c.setFillColor(colors.HexColor('#ffffff'))
    c.rect(40, h-360, w-80, 150, fill=1, stroke=1)
    
    c.setFillColor(colors.HexColor('#0f172a'))
    c.setFont(fn, 11)
    c.drawRightString(w - 55, h - 225, rtl(f'📌 نوع مشاهده انضباطی: {b_type}'))
    c.drawRightString(w - 55, h - 250, rtl(f'📝 عنوان مشاهده: {title}'))
    c.drawRightString(w - 55, h - 280, rtl(f'📄 توضیحات و شرح معلم: {desc}'))
    
    # Signatures
    y = 120
    c.setFont(fn, 10)
    c.drawRightString(w - 80, y, rtl('آموزگار پایه پنجم: سید موسی حیدری'))
    c.drawRightString(w/2 + 40, y, rtl('مدیریت دبستان شهید مطهری مهران'))
    c.drawRightString(180, y, rtl('رویت و امضای اولیای محترم'))
    
    c.save()
    return buf.getvalue()

# PDF Report 2: Online Exams Analysis
def generate_exams_pdf(student_name, national_id, student_group, df_quizzes, quiz_avg_str):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    fn = 'PersianFont' if _PERSIAN_FONT_REGISTERED else 'Helvetica'
    
    c.setFillColor(colors.HexColor('#0f172a'))
    c.rect(0, h-80, w, 80, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#ffffff'))
    c.setFont(fn, 13)
    c.drawCentredString(w/2, h-32, rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
    c.setFont(fn, 11)
    c.drawCentredString(w/2, h-56, rtl('دبستان پسرانه شهید مطهری مهران - پایه پنجم ابتدایی'))
    
    c.setFillColor(colors.HexColor('#1e3a8a'))
    c.setFont(fn, 14)
    c.drawCentredString(w/2, h-115, rtl('گزارش تحلیلی آزمون‌های آنلاین و روند رشد تحصیلی'))
    
    c.setFillColor(colors.HexColor('#f1f5f9'))
    c.rect(40, h-180, w-80, 50, fill=1, stroke=1)
    c.setFillColor(colors.HexColor('#0f172a'))
    c.setFont(fn, 10)
    c.drawRightString(w - 55, h - 150, rtl(f'نام دانش‌آموز: {student_name}'))
    c.drawRightString(w - 230, h - 150, rtl(f'کد ملی: {national_id}'))
    c.drawRightString(w - 380, h - 150, rtl(f'گروه کلاسی: {student_group}'))
    c.drawRightString(w - 55, h - 170, rtl(f'میانگین کل درصدهای آزمون: {quiz_avg_str}'))
    
    # Table Header
    y = h - 220
    c.setFillColor(colors.HexColor('#1e3a8a'))
    c.rect(40, y-20, w-80, 20, fill=1, stroke=1)
    c.setFillColor(colors.HexColor('#ffffff'))
    c.setFont(fn, 10)
    c.drawRightString(w - 50, y - 15, rtl('عنوان آزمون'))
    c.drawRightString(w - 220, y - 15, rtl('درس'))
    c.drawRightString(w - 320, y - 15, rtl('نمره / کل'))
    c.drawRightString(w - 420, y - 15, rtl('درصد'))
    
    y -= 20
    if not df_quizzes.empty:
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(fn, 9)
        for _, row in df_quizzes.head(10).iterrows():
            y -= 18
            c.drawRightString(w - 50, y, rtl(str(row.get('عنوان آزمون', ''))))
            c.drawRightString(w - 220, y, rtl(str(row.get('درس', ''))))
            c.drawRightString(w - 320, y, rtl(f"{row.get('نمره تستی', 0)} / {row.get('کل سوالات تستی', 0)}"))
            c.drawRightString(w - 420, y, rtl(f"{row.get('درصد ٪', 0):.1f}٪"))
            
    # Signatures
    y = 120
    c.setFont(fn, 10)
    c.drawRightString(w - 80, y, rtl('آموزگار پایه پنجم: سید موسی حیدری'))
    c.drawRightString(w/2 + 40, y, rtl('مدیریت دبستان شهید مطهری مهران'))
    c.drawRightString(180, y, rtl('رویت و امضای اولیای محترم'))
    
    c.save()
    return buf.getvalue()

# PDF Report 3: Comprehensive Portfolio Report
def generate_portfolio_pdf(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str, df_e, df_b, df_q):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    fn = 'PersianFont' if _PERSIAN_FONT_REGISTERED else 'Helvetica'
    
    c.setFillColor(colors.HexColor('#0f172a'))
    c.rect(0, h-80, w, 80, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#ffffff'))
    c.setFont(fn, 13)
    c.drawCentredString(w/2, h-32, rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
    c.setFont(fn, 11)
    c.drawCentredString(w/2, h-56, rtl('دبستان پسرانه شهید مطهری مهران - پایه پنجم ابتدایی'))
    
    c.setFillColor(colors.HexColor('#1e3a8a'))
    c.setFont(fn, 13)
    c.drawCentredString(w/2, h-112, rtl('کارنامه جامع تحصیلی و پوشه کار دیجیتال (سال تحصیلی ۱۴۰۴-۱۴۰۵)'))
    
    # Meta Box
    c.setFillColor(colors.HexColor('#f1f5f9'))
    c.rect(40, h-175, w-80, 50, fill=1, stroke=1)
    c.setFillColor(colors.HexColor('#0f172a'))
    c.setFont(fn, 10)
    c.drawRightString(w - 55, h - 145, rtl(f'نام دانش‌آموز: {student_name}'))
    c.drawRightString(w - 230, h - 145, rtl(f'کد ملی: {national_id}'))
    c.drawRightString(w - 380, h - 145, rtl(f'گروه کلاسی: {student_group}'))
    c.drawRightString(w - 55, h - 165, rtl(f'شماره همراه اولیا: {parent_phone}'))
    c.drawRightString(w - 230, h - 165, rtl(f'تعداد ارزشیابی‌ها: {eval_count}'))
    c.drawRightString(w - 380, h - 165, rtl(f'میانگین آزمون‌ها: {quiz_avg_str}'))
    
    # Section 1: Evaluations
    y = h - 200
    c.setFillColor(colors.HexColor('#1e3a8a'))
    c.setFont(fn, 11)
    c.drawRightString(w - 45, y, rtl('📝 خلاصه سوابق ارزشیابی کیفی-توصیفی ۷ درس:'))
    
    y -= 15
    if not df_e.empty:
        c.setFont(fn, 9)
        c.setFillColor(colors.HexColor('#0f172a'))
        for _, r in df_e.head(6).iterrows():
            y -= 16
            c.drawRightString(w - 55, y, rtl(f"• {r.get('درس', '')}: {r.get('سطح توصیفی', '')} — {r.get('توصیف عملکرد', '')[:40]}"))
            
    # Section 2: Behaviors
    y -= 25
    c.setFillColor(colors.HexColor('#1e3a8a'))
    c.setFont(fn, 11)
    c.drawRightString(w - 45, y, rtl('🌟 خلاصه مشاهدات انضباطی و رفتاری:'))
    
    y -= 15
    if not df_b.empty:
        c.setFont(fn, 9)
        c.setFillColor(colors.HexColor('#0f172a'))
        for _, r in df_b.head(4).iterrows():
            y -= 16
            c.drawRightString(w - 55, y, rtl(f"• {r.get('نوع', '')}: {r.get('عنوان', '')} — {r.get('شرح', '')[:45]}"))
            
    # Analysis & Advice Box
    y -= 45
    c.setFillColor(colors.HexColor('#eff6ff'))
    c.rect(40, y-75, w-80, 75, fill=1, stroke=1)
    c.setFillColor(colors.HexColor('#1e40af'))
    c.setFont(fn, 11)
    c.drawRightString(w - 55, y - 20, rtl('💡 تحلیل جامع آموزشی و توصیه‌های تربیتی آموزگار:'))
    c.setFillColor(colors.HexColor('#0f172a'))
    c.setFont(fn, 9)
    c.drawRightString(w - 55, y - 40, rtl('۱. نقاط قوت: حضور منظم در کلاس، مشارکت فعال در فعالیت‌های گروهی و آزمون‌های آنلاین.'))
    c.drawRightString(w - 55, y - 60, rtl('۲. توصیه به اولیا: تمرین مستمر کسرها و مفاهیم ریاضی در منزل جهت تثبیت یادگیری.'))
    
    # Signatures
    y = 100
    c.setFont(fn, 10)
    c.drawRightString(w - 80, y, rtl('آموزگار پایه پنجم: سید موسی حیدری'))
    c.drawRightString(w/2 + 40, y, rtl('مدیریت دبستان شهید مطهری مهران'))
    c.drawRightString(180, y, rtl('رویت و امضای اولیای محترم'))
    
    c.save()
    return buf.getvalue()

# ---------------------------------------------------------
# Database Initialization & Migration
# ---------------------------------------------------------
DB_FILE = "class_management.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            national_id TEXT UNIQUE,
            parent_phone TEXT,
            student_group TEXT DEFAULT 'بدون گروه',
            notes TEXT,
            pin_code TEXT DEFAULT '1234',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
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
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_auth (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            password TEXT NOT NULL
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO teacher_auth (id, password) VALUES (1, '1234')")
    
    conn.commit()
    conn.close()

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

init_db()

# Seed default 29 students if empty
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
                INSERT INTO students (national_id, first_name, last_name, parent_phone, student_group)
                VALUES (?, ?, ?, ?, ?)
            """, st_item)
        conn.commit()
    conn.close()

seed_default_students()

# Seed default quiz
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

# Helper Constants

def parse_excel_row(row, idx):
    fname, lname = '', ''
    
    full_col = None
    for k in row.index:
        ks = str(k).strip()
        if ks in ['نام و نام خانوادگی', 'نام خانوادگی و نام', 'نام دانش آموز', 'نام کامل', 'full_name', 'fullname', 'name']:
            full_col = k
            break
            
    if full_col and pd.notna(row[full_col]):
        parts = str(row[full_col]).strip().split()
        if len(parts) >= 2:
            fname = parts[0]
            lname = ' '.join(parts[1:])
        elif len(parts) == 1:
            fname = parts[0]
            lname = 'کلاسی'
            
    if not fname or not lname:
        fn_col, ln_col = None, None
        for k in row.index:
            ks = str(k).strip()
            if ks in ['نام', 'first_name', 'fname', 'first']:
                fn_col = k
            elif ks in ['نام خانوادگی', 'فامیلی', 'نام‌خانوادگی', 'last_name', 'lname', 'last', 'family']:
                ln_col = k
        if fn_col and pd.notna(row[fn_col]): fname = str(row[fn_col]).strip()
        if ln_col and pd.notna(row[ln_col]): lname = str(row[ln_col]).strip()
        
    if not fname: fname = 'دانش‌آموز'
    if not lname: lname = f'{idx+1}'
    
    nid = ''
    nid_col = None
    for k in row.index:
        ks = str(k).strip()
        if ks in ['کد ملی', 'کدملّی', 'کدملی', 'شماره ملی', 'کد ملی واقعی', 'national_id', 'national_code', 'nid']:
            nid_col = k
            break
    if nid_col and pd.notna(row[nid_col]):
        nid_str = str(row[nid_col]).strip().replace('.0', '')
        if nid_str and nid_str.lower() != 'nan' and nid_str != 'None':
            nid = nid_str
            
    if not nid or len(nid) < 3:
        nid = f'100000{idx+1:04d}'
        
    phone = ''
    ph_col = None
    for k in row.index:
        ks = str(k).strip()
        if ks in ['شماره همراه اولیا', 'شماره اولیا', 'شماره همراه', 'تلفن اولیا', 'تلفن', 'همراه', 'parent_phone', 'phone', 'mobile']:
            ph_col = k
            break
    if ph_col and pd.notna(row[ph_col]):
        ph_str = str(row[ph_col]).strip().replace('.0', '')
        if ph_str and ph_str.lower() != 'nan' and ph_str != 'None' and ph_str != '0':
            if len(ph_str) == 10 and ph_str.startswith('9'):
                ph_str = '0' + ph_str
            phone = ph_str
        else:
            phone = '0'
    else:
        phone = '0'
        
    group = ''
    grp_col = None
    for k in row.index:
        ks = str(k).strip()
        if ks in ['گروه کلاسی', 'گروه آموزشی', 'گروه', 'student_group', 'group']:
            grp_col = k
            break
    if grp_col and pd.notna(row[grp_col]):
        g_str = str(row[grp_col]).strip()
        if g_str and g_str.lower() != 'nan' and g_str != 'None':
            group = g_str
    if not group:
        group = CLASS_GROUPS[idx % 5]
        
    pin = '1234'
    pin_col = None
    for k in row.index:
        ks = str(k).strip()
        if ks in ['رمز اختصاصی', 'رمز ۴ رقمی', 'رمز', 'pin_code', 'pin']:
            pin_col = k
            break
    if pin_col and pd.notna(row[pin_col]):
        p_str = str(row[pin_col]).strip().replace('.0', '')
        if p_str and len(p_str) == 4 and p_str.isdigit():
            pin = p_str
            
    return fname, lname, nid, phone, group, pin


FIFTH_GRADE_SUBJECTS = ["ریاضی", "علوم تجربی", "فارسی (خوانداری)", "نگارش فارسی", "مطالعات اجتماعی", "هدیه‌های آسمان", "آموزش قرآن"]
EVALUATION_LEVELS = ["خیلی خوب 🌟", "خوب 🟢", "قابل قبول 🟡", "نیاز به تلاش مجدد 🔴"]
CLASS_GROUPS = ["گروه ارمغان 🚀", "گروه دانا 💡", "گروه تلاش 🌟", "گروه نخبگان 🏆", "گروه اندیشه 📖"]

def load_students():
    with get_connection() as conn:
        df = safe_read_sql("SELECT id, national_id, first_name, last_name, parent_phone, student_group, notes FROM students ORDER BY last_name, first_name", conn)
    if not df.empty:
        df['full_name'] = df['first_name'].astype(str) + ' ' + df['last_name'].astype(str)
    else:
        df = pd.DataFrame(columns=['id', 'national_id', 'first_name', 'last_name', 'full_name', 'parent_phone', 'student_group', 'notes'])
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
if 'user_role' not in st.session_state: st.session_state['user_role'] = 'دانش‌آموز'
if 'is_teacher_logged_in' not in st.session_state: st.session_state['is_teacher_logged_in'] = False
if 'excel_upload_key' not in st.session_state: st.session_state['excel_upload_key'] = 0
if 'show_welcome_page' not in st.session_state: st.session_state['show_welcome_page'] = True

# ---------------------------------------------------------
# WELCOME SPLASH PAGE
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
                <li><b>ارزشیابی توصیفی کشوری:</b> رعایت دقیق بارم‌بندی و سطوح عملکردی (خیلی خوب، خوب، قابل قبول، نیاز به تلاش).</li>
                <li><b>توسعه عدالت آموزشی:</b> امکان دسترسی آسان تمامی دانش‌آموزان با گوشی، تبلت و کامپیوتر بدون نیاز به نصب.</li>
                <li><b>ارتباط مستمر خانه و مدرسه:</b> ارائه گزارش‌های دوره‌ای قابل چاپ جهت درج در پوشه کار فیزیکی.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 ورود به سامانه هوشمند مدیریت کلاس و آزمون آنلاین"):
        st.session_state['show_welcome_page'] = False
        st.rerun()
    st.stop()

# ---------------------------------------------------------
# TOP APP HEADER & AUTH BAR
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین — پایه پنجم ابتدایی</h2>
    <p>دبستان شهید مطهری مهران | آموزگار: سید موسی حیدری</p>
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

with col_h3:
    if st.button("🏠 صفحه خوش‌آمدگویی"):
        st.session_state['show_welcome_page'] = True
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# NAVIGATION MENU (CLEAN, COMPACT DROPDOWN SELECTBOX)
# ---------------------------------------------------------
if st.session_state['is_teacher_logged_in']:
    MENU_OPTIONS = [
        "1️⃣ 🏠 معرفی سامانه و اهداف آموزشی",
        "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی (۲۹ نفر)",
        "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی (ویژه معلم)",
        "4️⃣ 🌟 مدیریت رفتار و مشاهدات انضباطی (ویژه معلم)",
        "5️⃣ ✏️ آزمون‌ساز آنلاین و طراحی سوالات (ویژه معلم)",
        "6️⃣ 📱 شرکت در آزمون آنلاین (عمومی / دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع (عمومی / اولیا)"
    ]
else:
    MENU_OPTIONS = [
        "1️⃣ 🏠 معرفی سامانه و اهداف آموزشی",
        "6️⃣ 📱 شرکت در آزمون آنلاین (عمومی / دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع (عمومی / اولیا)"
    ]

st.markdown("""
<div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 14px 20px; border-radius: 12px; border: 2px solid #38bdf8; margin-bottom: 15px;">
    <h3 style="color: #38bdf8 !important; margin: 0; font-size: 1.15rem;">📌 منوی اصلی سامانه (بخش مورد نظر را انتخاب کنید):</h3>
</div>
""", unsafe_allow_html=True)

menu_choice = st.selectbox(
    "انتخاب بخش منو:",
    MENU_OPTIONS,
    label_visibility="collapsed",
    key="main_selectbox_nav"
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
        <h4>2️⃣ آزمون‌ساز آنلاین با امنیت ۴ لایه (رمز، سوالات تصادفی، قفل ارسال و ثبت چهره)</h4>
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
    
    # Global import success message
    if 'import_success_msg' in st.session_state and st.session_state['import_success_msg']:
        st.success(st.session_state['import_success_msg'])
        st.session_state['import_success_msg'] = ''
        
    tab1, tab2, tab3 = st.tabs(["📋 لیست دانش‌آموزان و گروه‌ها", "📊 ثبت دسته‌جمعی و سریع از اکسل", "➕ ثبت دانش‌آموز جدید (تکی)"])
    
    with tab1:
        students_df = load_students()
        if not students_df.empty:
            st.info(f"📊 هم‌اکنون تعداد {len(students_df)} دانش‌آموز در دیتابیس کلاس ثبت شده است.")
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام یا کد ملی):")
            with col_s2:
                selected_group_filter = st.selectbox("فیلتر بر اساس گروه:", ["همه گروه‌ها"] + CLASS_GROUPS)
                
            filtered_df = students_df.copy()
            if search_query:
                filtered_df = filtered_df[filtered_df['full_name'].str.contains(search_query, na=False) | filtered_df['national_id'].astype(str).str.contains(search_query, na=False)]
            if selected_group_filter != "همه گروه‌ها":
                filtered_df = filtered_df[filtered_df['student_group'] == selected_group_filter]
                
            st.dataframe(filtered_df.rename(columns={
                'id': 'شناسه',
                'full_name': 'نام و نام خانوادگی',
                'national_id': 'کد ملی',
                'parent_phone': 'شماره اولیا',
                'student_group': 'گروه کلاسی',
                'notes': 'توضیحات'
            })[['شناسه', 'نام و نام خانوادگی', 'کد ملی', 'شماره اولیا', 'گروه کلاسی', 'توضیحات']], use_container_width=True)
            
            st.markdown("---")
            st.subheader("🗑️ مدیریت یا حذف پرونده دانش‌آموز")
            
            student_display_list = [f"{row['id']} - {row['full_name']} (کد ملی: {row['national_id']} | گروه: {row['student_group']})" for _, row in students_df.iterrows()]
            student_to_delete_str = st.selectbox("انتخاب دانش‌آموز جهت حذف:", student_display_list, key="del_student_select")
            if st.button("🗑️ حذف پرونده دانش‌آموز انتخابی"):
                s_id_del = int(student_to_delete_str.split(" - ")[0])
                with get_connection() as conn:
                    conn.execute("DELETE FROM evaluations WHERE student_id = ?", (s_id_del,))
                    conn.execute("DELETE FROM behavior_logs WHERE student_id = ?", (s_id_del,))
                    conn.execute("DELETE FROM behaviors WHERE student_id = ?", (s_id_del,))
                    conn.execute("DELETE FROM quiz_submissions WHERE student_id = ?", (s_id_del,))
                    conn.execute("DELETE FROM quiz_results WHERE student_id = ?", (s_id_del,))
                    conn.execute("DELETE FROM students WHERE id = ?", (s_id_del,))
                    conn.commit()
                st.session_state['import_success_msg'] = "پرونده دانش‌آموز با موفقیت حذف گردید."
                st.rerun()
                
            with st.expander("⚠️ پاکسازی کلی تمام اسامی دانش‌آموزان دیتابیس (ریست کامل)"):
                st.warning("توجه: این عمل تمام اسامی دانش‌آموزان و سوابق آن‌ها را به‌طور کامل پاک می‌کند!")
                confirm_del_all = st.checkbox("تایید می‌کنم که تمام اسامی پاک شوند")
                if st.button("💥 پاکسازی کامل دیتابیس دانش‌آموزان") and confirm_del_all:
                    with get_connection() as conn:
                        conn.execute("DELETE FROM evaluations")
                        conn.execute("DELETE FROM behavior_logs")
                        conn.execute("DELETE FROM behaviors")
                        conn.execute("DELETE FROM quiz_submissions")
                        conn.execute("DELETE FROM quiz_results")
                        conn.execute("DELETE FROM students")
                        conn.commit()
                    st.session_state['import_success_msg'] = "تمام اسامی دانش‌آموزان و سوابق آن‌ها پاکسازی شدند."
                    st.rerun()
        else:
            st.info("هنوز هیچ دانش‌آموزی در دیتابیس ثبت نشده است. لطفاً از زبانه '📊 ثبت دسته‌جمعی و سریع از اکسل' فایل اکسل اسامی را آپلود فرمایید.")

    with tab2:
        st.subheader("📊 ورود یکجای اسامی دانش‌آموزان از فایل اکسل (Excel/CSV)")
        st.info("💡 پشتیبانی هوشمند از تمام فرمت‌های اکسل: فایل اکسل شما می‌تواند شامل ستون‌های 'نام'، 'نام خانوادگی'، 'کد ملی'، 'شماره همراه اولیا' و 'گروه کلاسی' باشد.")
        
        sample_data = pd.DataFrame({
            'نام و نام خانوادگی': ['آرتین آب روشن', 'هیمن ازوار'],
            'کد ملی': ['4520183571', '4520183421'],
            'شماره همراه اولیا': ['09921029563', '09183425450'],
            'گروه کلاسی': ['گروه ارمغان 🚀', 'گروه دانا 💡']
        })
        st.download_button(
            "📥 دانلود نمونه فایل الگوی اکسل استاندارد (CSV)",
            sample_data.to_csv(index=False).encode('utf-8-sig'),
            "students_template_sample.csv",
            "text/csv"
        )
        
        if 'excel_upload_key' not in st.session_state:
            st.session_state['excel_upload_key'] = 0
            
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
                    
                st.success(f"👀 پیش‌نمایش فایل: تعداد {len(df_upload)} دانش‌آموز در فایل اکسل شناسایی گردید.")
                st.dataframe(df_upload, use_container_width=True)
                
                if st.button("🚀 ذخیره و ورود تمام اسامی به دیتابیس"):
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        added_cnt = 0
                        for idx, row in df_upload.iterrows():
                            fn, ln, nid, ph, grp, pin = parse_excel_row(row, idx)
                            try:
                                cursor.execute("""
                                    INSERT OR REPLACE INTO students (first_name, last_name, national_id, parent_phone, student_group, pin_code)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (fn, ln, nid, ph, grp, pin))
                                added_cnt += 1
                            except Exception as ex_err:
                                pass
                        conn.commit()
                    
                    st.session_state['import_success_msg'] = f"🎉 با موفقیت انجام شد! تعداد {added_cnt} دانش‌آموز در دیتابیس ذخیره شدند. می‌توانید در زبانه '📋 لیست دانش‌آموزان و گروه‌ها' اسامی آن‌ها را مشاهده فرمایید."
                    st.session_state['excel_upload_key'] += 1
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در خواندن فایل اکسل: {e}")

    with tab3:
        st.subheader("➕ ثبت دانش‌آموز جدید (تکی)")
        with st.form("add_single_st_form"):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                first_name = st.text_input("نام:*")
                national_id = st.text_input("کد ملی دانش‌آموز:")
                student_group = st.selectbox("گروه آموزشی کلاسی:", CLASS_GROUPS)
            with col_a2:
                last_name = st.text_input("نام خانوادگی:*")
                parent_phone = st.text_input("شماره همراه اولیا:")
                notes = st.text_area("توضیحات تکمیلی:")
                
            if st.form_submit_button("💾 ثبت دانش‌آموز"):
                if first_name.strip() and last_name.strip():
                    nid_val = national_id.strip() if national_id.strip() else f"100000{random.randint(1000,9999)}"
                    with get_connection() as conn:
                        conn.execute("""
                            INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group, notes)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (first_name.strip(), last_name.strip(), nid_val, parent_phone.strip(), student_group, notes.strip()))
                        conn.commit()
                    st.session_state['import_success_msg'] = f"دانش‌آموز {first_name.strip()} {last_name.strip()} با موفقیت ثبت گردید."
                    st.rerun()
                else:
                    st.error("نام و نام خانوادگی الزامی است.")

elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی (پایه پنجم)")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("لطفاً ابتدا اسامی دانش‌آموزان را ثبت کنید.")
    else:
        student_display_list = [f"{row['id']} - {row['full_name']} (کد ملی: {row['national_id']} | گروه: {row['student_group']})" for _, row in students_df.iterrows()]
        
        col1, col2 = st.columns(2)
        with col1:
            selected_student_str = st.selectbox("انتخاب دانش‌آموز:", student_display_list, key="eval_st_sel")
            selected_subject = st.selectbox("انتخاب درس:", FIFTH_GRADE_SUBJECTS)
        with col2:
            selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
            eval_date = st.date_input("تاریخ ارزشیابی:", datetime.date.today())
            
        feedback_text = st.text_area("توصیف عملکرد و بازخورد آموزگار:")
        
        if st.button("💾 ثبت ارزشیابی توصیفی"):
            s_id = int(selected_student_str.split(" - ")[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text, eval_date)
                )
                conn.commit()
            st.success("ارزشیابی توصیفی ثبت شد.")

        st.markdown("---")
        s_id = int(selected_student_str.split(" - ")[0])
        st.subheader(f"📋 سوابق ارزشیابی دانش‌آموز انتخابی")
        with get_connection() as conn:
            eval_h = safe_read_sql("""
                SELECT id, subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'بازخورد معلم', eval_date AS 'تاریخ'
                FROM evaluations WHERE student_id = ? ORDER BY eval_date DESC
            """, conn, params=(s_id,))
        if not eval_h.empty:
            st.dataframe(eval_h.drop(columns=['id'], errors='ignore'), use_container_width=True)
            
            with st.expander("🗑️ حذف یک رکورد ارزشیابی"):
                del_eval_id = st.selectbox("شناسه ارزشیابی جهت حذف:", eval_h['id'].tolist(), key="del_eval_sel")
                if st.button("حذف ارزشیابی انتخابی"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM evaluations WHERE id = ?", (del_eval_id,))
                        conn.commit()
                    st.success("ارزشیابی حذف شد.")
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
        student_display_list = [f"{row['id']} - {row['full_name']} (کد ملی: {row['national_id']} | گروه: {row['student_group']})" for _, row in students_df.iterrows()]
        
        col1, col2 = st.columns(2)
        with col1:
            selected_student_str = st.selectbox("انتخاب دانش‌آموز:", student_display_list, key="beh_st_sel")
            b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
        with col2:
            title = st.text_input("عنوان رفتار:")
            log_date = st.date_input("تاریخ ثبت:", datetime.date.today())
            
        desc = st.text_area("جزییات و اقدامات انجام‌شده:")
        
        if st.button("💾 ثبت مشاهده رفتاری"):
            s_id = int(selected_student_str.split(" - ")[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, b_type, title, desc, log_date)
                )
                conn.commit()
            st.success("مشاهده رفتاری ذخیره شد.")

        st.markdown("---")
        s_id = int(selected_student_str.split(" - ")[0])
        st.subheader(f"📋 سوابق رفتاری دانش‌آموز انتخابی")
        with get_connection() as conn:
            beh_h = safe_read_sql("""
                SELECT id, behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ'
                FROM behaviors WHERE student_id = ? ORDER BY log_date DESC
            """, conn, params=(s_id,))
        if not beh_h.empty:
            st.dataframe(beh_h.drop(columns=['id'], errors='ignore'), use_container_width=True)
            with st.expander("🗑️ حذف یک مورد رفتاری"):
                del_beh_id = st.selectbox("شناسه مورد رفتاری جهت حذف:", beh_h['id'].tolist(), key="del_beh_sel")
                if st.button("حذف مورد رفتاری انتخابی"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM behaviors WHERE id = ?", (del_beh_id,))
                        conn.commit()
                    st.success("مورد رفتاری حذف شد.")
                    st.rerun()

# ---------------------------------------------------------
# 5. ONLINE QUIZ CREATOR (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (طراحی و انتشار آزمون)")
    
    tab_q1, tab_q2, tab_q3, tab_q4 = st.tabs(["➕ طراحی دستی آزمون", "📊 بارگذاری از فایل اکسل (Excel/CSV)", "📋 کپی-پیست متن سوالات", "🗑️ مدیریت و حذف آزمون‌ها"])
    
    with tab_q1:
        col1, col2, col3 = st.columns(3)
        with col1: quiz_title = st.text_input("عنوان آزمون:", key="q1_t")
        with col2: quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="q1_s")
        with col3: duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=180, value=60, key="q1_d")
            
        num_q = st.number_input("تعداد سوالات:", min_value=1, max_value=30, value=3, key="q1_n")
        
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
        st.subheader("📊 ورود سوالات از فایل اکسل (Excel / CSV)")
        ex_t = st.text_input("عنوان آزمون اکسل:", key="ex_t")
        ex_sub = st.selectbox("درس:", FIFTH_GRADE_SUBJECTS, key="ex_sub")
        ex_dur = st.number_input("زمان (دقیقه):", value=45, key="ex_dur")
        
        up_ex = st.file_uploader("فایل اکسل سوالات را انتخاب کنید:", type=["xlsx", "csv"], key="ex_up_q")
        if up_ex is not None and ex_t.strip():
            try:
                df_ex_q = pd.read_csv(up_ex) if up_ex.name.endswith('.csv') else pd.read_excel(up_ex)
                st.dataframe(df_ex_q.head())
                if st.button("🚀 ساخت آزمون از فایل اکسل"):
                    with get_connection() as conn:
                        cur = conn.cursor()
                        cur.execute("INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                                    (ex_t.strip(), ex_sub, ex_dur, datetime.date.today()))
                        qid = cur.lastrowid
                        cnt = 0
                        for _, r in df_ex_q.iterrows():
                            q_txt = str(r.get('متن سوال', r.get('سوال', ''))).strip()
                            o1 = str(r.get('گزینه ۱', r.get('گزینه 1', ''))).strip()
                            o2 = str(r.get('گزینه ۲', r.get('گزینه 2', ''))).strip()
                            o3 = str(r.get('گزینه ۳', r.get('گزینه 3', ''))).strip()
                            o4 = str(r.get('گزینه ۴', r.get('گزینه 4', ''))).strip()
                            c_opt = int(r.get('گزینه صحیح', 1))
                            exp_txt = str(r.get('تحلیل', '')).strip()
                            if q_txt:
                                cur.execute("""
                                    INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, explanation)
                                    VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?, ?)
                                """, (qid, q_txt, o1, o2, o3, o4, c_opt, exp_txt))
                                cnt += 1
                        conn.commit()
                    st.success(f"آزمون '{ex_t}' با {cnt} سوال ایجاد شد.")
            except Exception as e:
                st.error(f"خطا در بارگذاری اکسل: {e}")

    with tab_q3:
        st.subheader("📋 کپی-پیست مستقیم متن سوالات")
        tx_t = st.text_input("عنوان آزمون متنی:", key="tx_t")
        tx_sub = st.selectbox("درس:", FIFTH_GRADE_SUBJECTS, key="tx_sub")
        tx_dur = st.number_input("زمان (دقیقه):", value=30, key="tx_dur")
        
        sample_txt = "سوال ۱: حاصل کسر ۲/۵ + ۳/۱۰ کدام است؟ | گزینه ۱: ۷/۱۰ | گزینه ۲: ۵/۱۵ | گزینه ۳: ۱/۲ | گزینه ۴: ۴/۱۰ | پاسخ صحیح: ۱\nسوال ۲: کدام‌یک تغییر شیمیایی است؟ | گزینه ۱: ذوب یخ | گزینه ۲: تبخیر آب | گزینه ۳: سوختن چوب | گزینه ۴: خرد کردن کاغذ | پاسخ صحیح: ۳"
        pasted_txt = st.text_area("متن سوالات را پیست کنید (با | جدا کنید):", value=sample_txt, height=180)
        
        if st.button("🚀 ساخت آزمون از متن کپی شده"):
            if tx_t.strip() and pasted_txt.strip():
                lines = pasted_txt.strip().split("\n")
                with get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                                (tx_t.strip(), tx_sub, tx_dur, datetime.date.today()))
                    qid = cur.lastrowid
                    cnt = 0
                    for line in lines:
                        if not line.strip(): continue
                        parts = [p.strip() for p in line.split("|")]
                        q_txt = parts[0]
                        o1 = parts[1].replace('گزینه ۱:', '').replace('گزینه 1:', '').strip() if len(parts)>1 else ''
                        o2 = parts[2].replace('گزینه ۲:', '').replace('گزینه 2:', '').strip() if len(parts)>2 else ''
                        o3 = parts[3].replace('گزینه ۳:', '').replace('گزینه 3:', '').strip() if len(parts)>3 else ''
                        o4 = parts[4].replace('گزینه ۴:', '').replace('گزینه 4:', '').strip() if len(parts)>4 else ''
                        corr = 1
                        if len(parts) > 5:
                            try: corr = int(re.sub(r'\D', '', parts[5]))
                            except ValueError: corr = 1
                        cur.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option)
                            VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?)
                        """, (qid, q_txt, o1, o2, o3, o4, corr))
                        cnt += 1
                    conn.commit()
                st.success(f"آزمون '{tx_t}' با {cnt} سوال ایجاد شد.")

    with tab_q4:
        st.subheader("🗑️ مدیریت و حذف آزمون‌های موجود")
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id, title AS 'عنوان آزمون', subject AS 'درس', duration_minutes AS 'زمان', is_active AS 'وضعیت' FROM quizzes ORDER BY id DESC", conn)
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True)
            
            del_quiz_str = st.selectbox("انتخاب آزمون جهت حذف:", [f"{row['id']} - {row['عنوان آزمون']}" for _, row in quizzes_df.iterrows()], key="del_q_sel")
            if st.button("🗑️ حذف آزمون انتخابی"):
                del_qid = int(del_quiz_str.split(" - ")[0])
                with get_connection() as conn:
                    conn.execute("DELETE FROM quizzes WHERE id = ?", (del_qid,))
                    conn.commit()
                st.success("آزمون با موفقیت حذف شد.")
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
        student_display_list = [f"{row['id']} - {row['full_name']} (کد ملی: {row['national_id']} | گروه: {row['student_group']})" for _, row in students_df.iterrows()]
        quiz_display_list = [f"{row['id']} - {row['title']} ({row['subject']} | {row['duration_minutes']} دقیقه)" for _, row in quizzes_df.iterrows()]
        
        col1, col2 = st.columns(2)
        with col1:
            student_sel_str = st.selectbox("نام دانش‌آموز (خود را انتخاب کنید):", student_display_list, key="st_quiz_st_sel")
        with col2:
            quiz_sel_str = st.selectbox("انتخاب آزمون:", quiz_display_list, key="st_quiz_q_sel")
            
        s_id = int(student_sel_str.split(" - ")[0])
        q_id = int(quiz_sel_str.split(" - ")[0])
        
        with get_connection() as conn:
            existing = conn.execute("SELECT id, percentage FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing:
            st.success(f"شما قبلاً در این آزمون شرکت کرده‌اید. درصد تستی کسب‌شده: {existing['percentage']:.1f}٪")
        else:
            duration_min = int(quizzes_df[quizzes_df['id'] == q_id]['duration_minutes'].values[0])
            st.info(f"⏱️ زمان پاسخگویی: {duration_min} دقیقه می‌باشد.")
            
            with get_connection() as conn:
                questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                
            student_mcq_ans = {}
            student_essay_ans = {}
            
            st.markdown("---")
            with st.form("take_quiz_form_v55"):
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
                        e_ans = st.text_area(f"پاسخ تشریحی شما برای سوال {idx+1}:", key=f"ans_essay_{q['id']}")
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
# 7. DASHBOARD & COMPREHENSIVE STUDENT PORTFOLIO
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد تحلیلی و پوشه کار جامع دانش‌آموز")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("هیچ دانش‌آموزی در سامانه ثبت نشده است.")
    else:
        student_display_list = [f"{row['id']} - {row['full_name']} (کد ملی: {row['national_id']} | گروه: {row['student_group']})" for _, row in students_df.iterrows()]
        selected_student_str = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار و گزارشات:", student_display_list, key="port_st_sel")
        s_id = int(selected_student_str.split(" - ")[0])
        
        st_row = students_df[students_df['id'] == s_id].iloc[0]
        s_name = st_row['full_name']
        s_nat = str(st_row['national_id'])
        s_grp = str(st_row['student_group'])
        s_phone = str(st_row['parent_phone'])
        
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg_str = f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون"
            
            df_e = safe_read_sql("SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ? ORDER BY eval_date DESC", conn, params=(s_id,))
            df_b = safe_read_sql("SELECT behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ' FROM behaviors WHERE student_id = ? ORDER BY log_date DESC", conn, params=(s_id,))
            df_q = safe_read_sql("""
                SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات تستی', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت', r.photo_data
                FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.submitted_at DESC
            """, conn, params=(s_id,))
            
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with c2: st.metric("موارد رفتاری ثبت‌شده:", beh_count)
        with c3: st.metric("میانگین درصد آزمون آنلاین:", quiz_avg_str)
            
        st.markdown("---")
        st.subheader("📥 دانلود ۳ گزارش رسمی PDF مستقل همراه با اطلاعات و جداول کامل:")
        
        col_pdf1, col_pdf2, col_pdf3 = st.columns(3)
        
        with col_pdf1:
            pdf1_bytes = generate_behavior_pdf(s_name, s_nat, s_grp, "مشاهدات انضباطی", "گزارش رفتاری کلاسی", f"تعداد {beh_count} مورد رفتاری ثبت شده است.", datetime.date.today().strftime("%Y/%m/%d"))
            st.download_button(
                "📄 ۱. دانلود PDF گزارش رفتار و انضباط",
                data=pdf1_bytes,
                file_name=f"behavior_report_{s_nat}.pdf",
                mime="application/pdf",
                key="dl_pdf1"
            )
            
        with col_pdf2:
            pdf2_bytes = generate_exams_pdf(s_name, s_nat, s_grp, df_q, quiz_avg_str)
            st.download_button(
                "📈 ۲. دانلود PDF گزارش آزمون‌های آنلاین",
                data=pdf2_bytes,
                file_name=f"exams_report_{s_nat}.pdf",
                mime="application/pdf",
                key="dl_pdf2"
            )
            
        with col_pdf3:
            pdf3_bytes = generate_portfolio_pdf(s_name, s_nat, s_phone, s_grp, eval_count, beh_count, quiz_avg_str, df_e, df_b, df_q)
            st.download_button(
                "🏆 ۳. دانلود PDF کارنامه جامع و پوشه کار",
                data=pdf3_bytes,
                file_name=f"comprehensive_portfolio_{s_nat}.pdf",
                mime="application/pdf",
                key="dl_pdf3"
            )
            
        st.markdown("---")
        
        tab_d1, tab_d2, tab_d3 = st.tabs(["📝 ارزشیابی‌های توصیفی", "🌟 سوابق رفتاری", "📊 کارنامه و تصویر چهره آزمون‌ها"])
        
        with tab_d1:
            if not df_e.empty:
                st.dataframe(df_e, use_container_width=True)
            else:
                st.info("ارزشیابی درسی برای این دانش‌آموز ثبت نشده است.")
                
        with tab_d2:
            if not df_b.empty:
                st.dataframe(df_b, use_container_width=True)
            else:
                st.info("مورد رفتاری برای این دانش‌آموز ثبت نشده است.")
                
        with tab_d3:
            if not df_q.empty:
                show_df = df_q.drop(columns=['photo_data'], errors='ignore')
                st.dataframe(show_df, use_container_width=True)
                
                st.markdown("##### 📈 نمودار رشد نمرات آزمون‌ها:")
                df_chart = safe_read_sql("""
                    SELECT q.title AS 'آزمون', r.percentage AS 'درصد'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id 
                    WHERE r.student_id = ? ORDER BY r.id ASC
                """, conn, params=(s_id,))
                if not df_chart.empty:
                    st.line_chart(df_chart.set_index('آزمون'))
                    
                st.markdown("##### 📸 تصاویر ثبت‌شده چهره در زمان تحویل آزمون‌ها:")
                for _, r_row in df_q.iterrows():
                    if r_row['photo_data']:
                        st.image(r_row['photo_data'], caption=f"آزمون: {r_row['عنوان آزمون']} | درصد: {r_row['درصد ٪']:.1f}٪", width=180)
            else:
                st.info("نتیجه آزمونی برای این دانش‌آموز ثبت نشده است.")
