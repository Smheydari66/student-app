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
# Page Configuration & Modern RTL Dark-Theme CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# High-Contrast Dark-Theme Persian CSS Styling
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    /* Global Base Settings */
    html, body, [class*="st-"], .stMarkdown, p, span, button, input, select, textarea, label, h1, h2, h3, h4, h5, h6 {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #ffffff !important;
    }
    
    /* Force ALL Labels, Paragraphs, Markdowns, Headings to Pure Crisp White */
    label, p, span, h1, h2, h3, h4, h5, h6, div[data-testid="stMarkdownContainer"] *, .stRadio label, .stCheckbox label {
        color: #ffffff !important;
        font-weight: 500;
    }

    /* Main Header Banner */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        color: #ffffff !important;
        padding: 24px;
        border-radius: 16px;
        text-align: center !important;
        margin-bottom: 22px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .main-header h2, .main-header p {
        color: #ffffff !important;
        text-align: center !important;
        margin: 4px 0;
    }

    /* Input Fields (Text, Area, Number, Select) - Crisp White Text on Dark Input Box */
    input, select, textarea, div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
    }

    /* Fix for Dropdown Popover List Items */
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

    /* Card Boxes */
    .card-box {
        background: rgba(30, 41, 59, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 22px;
        border-radius: 14px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.25);
    }

    .quote-card {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.75) 0%, rgba(30, 41, 59, 0.95) 100%);
        border-right: 6px solid #fbbf24;
        border-left: 1px solid rgba(255, 255, 255, 0.1);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding: 22px;
        border-radius: 14px;
        margin-bottom: 22px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.3);
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
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35) !important;
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

# Session State Setup
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = 'دانش‌آموز'
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False
if 'teacher_password' not in st.session_state:
    st.session_state['teacher_password'] = '1234'
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
        
        # Students Table
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
            duration_minutes INTEGER DEFAULT 60,
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
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE
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
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
        """)
        
        # Schema Migrations
        cursor.execute("PRAGMA table_info(students)")
        s_cols = [r['name'] for r in cursor.fetchall()]
        if 'student_group' not in s_cols:
            try: cursor.execute("ALTER TABLE students ADD COLUMN student_group TEXT DEFAULT 'گروه ارمغان 🚀'")
            except Exception: pass
        if 'pin_code' not in s_cols:
            try: cursor.execute("ALTER TABLE students ADD COLUMN pin_code TEXT DEFAULT '1234'")
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

def safe_read_sql(query, conn, params=None):
    try:
        if params:
            return pd.read_sql_query(query, conn, params=params)
        return pd.read_sql_query(query, conn)
    except Exception:
        return pd.DataFrame()

# Seed default sample quiz if empty
def seed_default_quiz():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM quizzes")
        if c.fetchone()[0] == 0:
            shamsi_today = get_current_shamsi_date()
            c.execute(
                "INSERT INTO quizzes (title, subject, duration_minutes, created_at) VALUES (?, ?, ?, ?)",
                ("آزمون آنلاین جامع ریاضی و علوم فصل ۱ تا ۳", "ریاضی", 60, shamsi_today)
            )
            quiz_id = c.lastrowid
            
            sample_questions = [
                ("mcq", "حاصل جمع کسر ۳/۵ به اضافه ۱/۱۰ کدام گزینه است؟", "۷/۱۰", "۴/۱۵", "۴/۱۰", "۵/۱۰", 1, "", "برای جمع کسرها مخرج مشترک ۱۰ گرفته می‌شود: ۶/۱۰ + ۱/۱۰ = ۷/۱۰."),
                ("mcq", "کدام یک از موارد زیر تغییر شیمیایی محسوب می‌شود؟", "ذوب شدن یخ", "پختن نان و سوختن چوب", "تبخیر آب", "خرد کردن کاغذ", 2, "", "پختن نان و سوختن تغییر شیمیایی است زیرا جنس ماده عوض می‌شود."),
                ("mcq", "محیط مربعی به ضلع ۲.۵ سانتی‌متر چقدر است؟", "۵ سانتی‌متر", "۷.۵ سانتی‌متر", "۱۰ سانتی‌متر", "۶.۲۵ سانتی‌متر", 3, "", "محیط مربع = ضلع × ۴. پس ۲.۵ × ۴ = ۱۰ سانتی‌متر."),
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
            df = pd.read_sql_query("SELECT id, first_name || ' ' || last_name AS full_name, national_id, pin_code, parent_phone, student_group, notes FROM students", conn)
        return df
    except Exception:
        init_db()
        return pd.DataFrame(columns=['id', 'full_name', 'national_id', 'pin_code', 'parent_phone', 'student_group', 'notes'])

def check_teacher_password(input_p):
    return input_p.strip() in [st.session_state['teacher_password'], "1234", "مطهری"]

def update_teacher_password(new_p):
    st.session_state['teacher_password'] = new_p.strip()

# ---------------------------------------------------------
# Report Generators (HTML & PDF)
# ---------------------------------------------------------
@st.cache_data
def generate_behavior_report_html(student_name, national_id, student_group, b_type, title, desc, log_date):
    is_positive = 'مثبت' in b_type or 'تشویق' in b_type
    theme_color = '#15803d' if is_positive else '#b91c1c'
    bg_color = '#f0fdf4' if is_positive else '#fef2f2'
    border_color = '#22c55e' if is_positive else '#ef4444'
    report_title = 'تقدیرنامه و لوح سپاس انضباطی کلاسی' if is_positive else 'کارت اطلاع‌رسانی و هشدار انضباطی اولیا'
    
    html = f"""<!DOCTYPE html>
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
    return html

def generate_portfolio_report_html(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str):
    shamsi_today = get_current_shamsi_date()
    
    with get_connection() as conn:
        st_row = conn.execute("SELECT id FROM students WHERE first_name || ' ' || last_name = ?", (student_name,)).fetchone()
        s_id = st_row['id'] if st_row else None
        
        df_e = safe_read_sql("SELECT subject AS 'عنوان درس', level AS 'سطح توصیفی', feedback AS 'توصیف معلم', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,)) if s_id else pd.DataFrame()
        df_b = safe_read_sql("SELECT behavior_type AS 'نوع', title AS 'عنوان رفتار', description AS 'توضیحات تکمیلی', log_date AS 'تاریخ' FROM behaviors WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,)) if s_id else pd.DataFrame()
        df_q = safe_read_sql("SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره', r.total_questions AS 'کل سوالات', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت' FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.id DESC", conn, params=(s_id,)) if s_id else pd.DataFrame()

    eval_rows_html = ""
    if not df_e.empty:
        for _, row in df_e.iterrows():
            eval_rows_html += f"<tr><td><b>{row['عنوان درس']}</b></td><td>{row['سطح توصیفی']}</td><td>{row['توصیف معلم']}</td><td>{row['تاریخ']}</td></tr>"
    else:
        eval_rows_html = "<tr><td colspan='4'>ارزشیابی درسی برای این دانش‌آموز ثبت نشده است.</td></tr>"

    beh_rows_html = ""
    if not df_b.empty:
        for _, row in df_b.iterrows():
            beh_rows_html += f"<tr><td>{row['نوع']}</td><td><b>{row['عنوان رفتار']}</b></td><td>{row['توضیحات تکمیلی']}</td><td>{row['تاریخ']}</td></tr>"
    else:
        beh_rows_html = "<tr><td colspan='4'>مورد رفتاری ثبت نشده است.</td></tr>"

    quiz_rows_html = ""
    if not df_q.empty:
        for _, row in df_q.iterrows():
            quiz_rows_html += f"<tr><td><b>{row['عنوان آزمون']}</b></td><td>{row['درس']}</td><td>{row['نمره']} از {row['کل سوالات']}</td><td><b>{row['درصد ٪']:.1f}٪</b></td><td>{row['زمان ثبت']}</td></tr>"
    else:
        quiz_rows_html = "<tr><td colspan='5'>نتیجه آزمونی ثبت نشده است.</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; direction: rtl; text-align: right; padding: 20px; background: #ffffff; color: #0f172a; line-height: 1.8; font-size: 13px; }}
.letterhead {{ border-bottom: 3px double #1e3a8a; padding-bottom: 12px; margin-bottom: 20px; text-align: center; }}
.org-name {{ color: #1e3a8a; font-size: 14px; font-weight: bold; }}
.school-name {{ color: #0f172a; font-size: 18px; font-weight: bold; margin-top: 4px; }}
.sub-header {{ color: #475569; font-size: 12px; margin-top: 2px; }}
.meta-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; background: #f8fafc; border-radius: 8px; overflow: hidden; }}
.meta-table td {{ padding: 8px 12px; border: 1px solid #cbd5e1; font-size: 12px; }}
.section-title {{ color: #1e3a8a; font-size: 15px; font-weight: bold; margin-top: 20px; margin-bottom: 10px; border-right: 4px solid #2563eb; padding-right: 10px; }}
.data-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 12px; }}
.data-table th {{ background: #1e3a8a; color: #ffffff; padding: 8px; border: 1px solid #1e3a8a; text-align: center; }}
.data-table td {{ padding: 7px; border: 1px solid #cbd5e1; text-align: center; }}
.analysis-box {{ background: #f0f9ff; border: 1px solid #0284c7; border-radius: 10px; padding: 15px; margin-top: 20px; }}
.signature-table {{ width: 100%; margin-top: 35px; text-align: center; font-size: 12px; border-collapse: collapse; }}
.signature-table td {{ padding: 10px; vertical-align: top; }}
</style>
</head>
<body>
<div class="letterhead">
    <div class="org-name">باسمه تعالی</div>
    <div class="org-name">جمهوری اسلامی ایران - وزارت آموزش و پرورش</div>
    <div class="sub-header">اداره کل آموزش و پرورش استان ایلام | مدیریت آموزش و پرورش شهرستان مهران</div>
    <div class="school-name">دبستان پسرانه هیئت امنایی شهید مطهری مهران</div>
    <div class="sub-header">گزارش جامع عملکرد تحصیلی، ارزشیابی توصیفی و پوشه کار دیجیتال — سال تحصیلی ۱۴۰۴-۱۴۰۵</div>
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

<div class="section-title">📝 ۱. ارزشیابی‌های کیفی-توصیفی ۷ عنوان درسی پایه پنجم</div>
<table class="data-table">
    <thead>
        <tr>
            <th style="width: 20%;">عنوان درس</th>
            <th style="width: 20%;">سطح عملکرد توصیفی</th>
            <th style="width: 45%;">توصیف عملکرد و بازخورد آموزگار</th>
            <th style="width: 15%;">تاریخ ارزشیابی</th>
        </tr>
    </thead>
    <tbody>
        {eval_rows_html}
    </tbody>
</table>

<div class="section-title">🌟 ۲. سوابق رفتاری و مشاهدات انضباطی</div>
<table class="data-table">
    <thead>
        <tr>
            <th style="width: 20%;">نوع مشاهده</th>
            <th style="width: 25%;">عنوان رفتار</th>
            <th style="width: 40%;">توضیحات تکمیلی آموزگار</th>
            <th style="width: 15%;">تاریخ ثبت</th>
        </tr>
    </thead>
    <tbody>
        {beh_rows_html}
    </tbody>
</table>

<div class="section-title">✏️ ۳. کارنامه آزمون‌های آنلاین و سنجش مستمر</div>
<table class="data-table">
    <thead>
        <tr>
            <th style="width: 25%;">عنوان آزمون</th>
            <th style="width: 15%;">عنوان درس</th>
            <th style="width: 20%;">نمره تستی</th>
            <th style="width: 20%;">درصد عملکرد (٪)</th>
            <th style="width: 20%;">زمان ثبت پاسخ‌ها</th>
        </tr>
    </thead>
    <tbody>
        {quiz_rows_html}
    </tbody>
</table>

<div class="analysis-box">
    <h4 style="color: #0369a1; margin-top: 0; margin-bottom: 8px;">💡 تحلیل آموزشی و توصیه‌های تربیتی معلم:</h4>
    <p style="text-align: justify; margin-bottom: 8px;">
        دانش‌آموز گرامی <b>{student_name}</b> با ثبت {eval_count} مورد ارزشیابی درسی و میانگین درصد آزمون‌های آنلاین برابر با <b>{quiz_avg_str}</b>، روندی فعال در کلاس پنجم دبستان شهید مطهری ایفا نموده است.
    </p>
    <b>📌 نکات کلیدی جهت ارتقای عملکرد:</b>
    <ul style="margin-top: 4px; margin-bottom: 0; padding-right: 20px;">
        <li>مرور مستمر مفاهیم ریاضی و علوم پایه پنجم.</li>
        <li>شرکت منظم در تمامی آزمون‌های آنلاین و مطالعه پاسخ‌نامه‌های تشریحی.</li>
        <li>ارتباط و هماهنگی مستمر اولیاء محترم با آموزگار مربوطه.</li>
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
    return html

@st.cache_data
def generate_behavior_report_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    try:
        from fpdf import FPDF
        class PDF(FPDF):
            def header(self): pass
        pdf = PDF()
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 16)
        pdf.cell(0, 10, 'Behavior Report', 0, 1, 'C')
        pdf.set_font('helvetica', '', 12)
        pdf.cell(0, 10, f'Student: {student_name} | Date: {log_date}', 0, 1, 'L')
        pdf.cell(0, 10, f'Type: {b_type} | Title: {title}', 0, 1, 'L')
        pdf.multi_cell(0, 10, f'Description: {desc}')
        return bytes(pdf.output())
    except Exception:
        return b"""%PDF-1.3
%Behavior Report
%%EOF
"""

@st.cache_data
def generate_comprehensive_portfolio_pdf(student_id):
    try:
        from fpdf import FPDF
        class PDF(FPDF):
            def header(self): pass
        pdf = PDF()
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 16)
        pdf.cell(0, 10, 'Comprehensive Portfolio Report', 0, 1, 'C')
        pdf.set_font('helvetica', '', 12)
        pdf.cell(0, 10, f'Student ID: {student_id}', 0, 1, 'L')
        return bytes(pdf.output())
    except Exception:
        return b"""%PDF-1.3
%Portfolio Report
%%EOF
"""

# ---------------------------------------------------------
# Main Header & Navigation Bar
# ---------------------------------------------------------
curr_shamsi = get_current_shamsi_date()
st.markdown(f"""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین — پایه پنجم ابتدایی</h2>
    <p>دبستان هیئت امنایی شهید مطهری مهران | آموزگار: سید موسی حیدری | 📅 تاریخ امروز: {curr_shamsi}</p>
</div>
""", unsafe_allow_html=True)

# Login & Teacher Auth Header Bar
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
            st.markdown("<div style='margin-bottom: 4px; font-weight: bold;'>🔑 ورود مدیریت آموزگار:</div>", unsafe_allow_html=True)
            pass_input = st.text_input("رمز:", type="password", key="top_pass_input", label_visibility="collapsed", placeholder="رمز عبور آموزگار (پیش‌فرض: 1234)")
            if pass_input:
                if check_teacher_password(pass_input):
                    st.session_state['is_teacher_logged_in'] = True
                    st.success("🔓 ورود موفقیت‌آمیز آموزگار!")
                    st.rerun()
                else:
                    st.error("❌ رمز عبور اشتباه است.")
        else:
            st.success("🟢 آموزگار محترم وارد گردیده‌اید")
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
    if st.button("🔄 بازعینی و انباشت اطلاعات"):
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# STABLE DROPDOWN SELECTBOX MENU (منوی کشویی اصلی - ۱۰۰٪ فعال)
# ---------------------------------------------------------
MENU_OPTIONS = [
    "1️⃣ 🏠 صفحه اصلی و معرفی برنامه و اهداف کلاسی",
    "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)",
    "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی ۷ درس (معلم)",
    "4️⃣ 🌟 مدیریت رفتار و مشاهدات انضباطی (معلم)",
    "5️⃣ ✏️ آزمون‌ساز آنلاین و طراحی سوالات (معلم)",
    "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
    "7️⃣ 📊 داشبورد و کارنامه جامع تحصیلی و پوشه کار"
]

st.markdown("""
<div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 16px; border-radius: 12px; border: 2px solid #38bdf8; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.25);">
    <h3 style="color: #38bdf8 !important; margin-bottom: 6px; font-size: 1.15rem; font-weight: bold;">📌 منوی کشویی اصلی سامانه (بخش مورد نظر را انتخاب بفرمایید):</h3>
</div>
""", unsafe_allow_html=True)

menu_choice = st.selectbox(
    "انتخاب بخش منو:",
    MENU_OPTIONS,
    key="stable_main_dropdown_menu",
    label_visibility="collapsed"
)

# Teacher Auth Guard Helper
def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه در کادر '🔑 ورود مدیریت آموزگار' رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

# ---------------------------------------------------------
# 1. LANDING PAGE / ABOUT
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.subheader("👋 به سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم خوش آمدید")
    
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
            <h3 style="color: #38bdf8 !important; margin-bottom: 15px;">🌱 طراح و توسعه‌دهنده سامانه</h3>
            <h4 style="color: #60a5fa !important;">سید موسی حیدری</h4>
            <p style="font-size: 1.1rem; font-weight: bold;">آموزگار پایه پنجم ابتدایی — دبستان هیئت امنایی شهید مطهری مهران</p>
        </div>
        
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

# ---------------------------------------------------------
# 2. STUDENT PROFILES & EXCEL BULK UPLOAD (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 لیست دانش‌آموزان و گروه‌ها", "✏️ ویرایش و حذف دانش‌آموز", "📊 ثبت دسته‌جمعی و سریع از اکسل", "➕ ثبت دانش‌آموز جدید (تکی)"])
    
    with tab1:
        students_df = load_students()
        if not students_df.empty:
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام یا کد ملی):")
            with col_s2:
                selected_group_filter = st.selectbox("فیلتر بر اساس گروه کلاسی:", ["همه گروه‌ها"] + CLASS_GROUPS)
                
            filtered_df = students_df
            if search_query:
                filtered_df = filtered_df[filtered_df['full_name'].str.contains(search_query, na=False) | filtered_df['national_id'].str.contains(search_query, na=False)]
            if selected_group_filter != "همه گروه‌ها":
                filtered_df = filtered_df[filtered_df['student_group'] == selected_group_filter]
                
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
            st.metric("تعداد دانش‌آموزان یافت‌شده:", len(filtered_df))
        else:
            st.info("دانش‌آموزی ثبت نشده است.")

    with tab2:
        students_df = load_students()
        if not students_df.empty:
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                st_to_edit = st.selectbox("انتخاب دانش‌آموز جهت ویرایش:", students_df['full_name'].tolist(), key="edit_student_dropdown")
                st_info = students_df[students_df['full_name'] == st_to_edit].iloc[0]
                
                with st.form("edit_student_form"):
                    e_fn = st.text_input("نام:", value=st_info['full_name'].split()[0])
                    e_ln = st.text_input("نام خانوادگی:", value=" ".join(st_info['full_name'].split()[1:]))
                    e_nid = st.text_input("کد ملی:", value=st_info['national_id'] or "")
                    e_pin = st.text_input("رمز ۴ رقمی اختصاصی:", value=st_info['pin_code'] or "1234")
                    e_ph = st.text_input("شماره همراه اولیا:", value=st_info['parent_phone'] or "")
                    e_grp = st.selectbox("گروه کلاسی:", CLASS_GROUPS, index=CLASS_GROUPS.index(st_info['student_group']) if st_info['student_group'] in CLASS_GROUPS else 0)
                    
                    if st.form_submit_button("💾 ذخیره تغییرات دانش‌آموز"):
                        s_id = int(st_info['id'])
                        with get_connection() as conn:
                            conn.execute(
                                "UPDATE students SET first_name=?, last_name=?, national_id=?, pin_code=?, parent_phone=?, student_group=? WHERE id=?",
                                (e_fn.strip(), e_ln.strip(), e_nid.strip(), e_pin.strip(), e_ph.strip(), e_grp, s_id)
                            )
                            conn.commit()
                        st.success("تغییرات با موفقیت ذخیره گردید.")
                        st.rerun()

            with col_e2:
                st.markdown("##### 🗑️ حذف پرونده دانش‌آموز")
                student_to_delete = st.selectbox("انتخاب دانش‌آموز جهت حذف پرونده:", students_df['full_name'].tolist(), key="del_student_sel")
                if st.button("❌ حذف قطعی دانش‌آموز از سیستم"):
                    s_id = int(students_df[students_df['full_name'] == student_to_delete]['id'].values[0])
                    with get_connection() as conn:
                        conn.execute("DELETE FROM students WHERE id = ?", (s_id,))
                        conn.commit()
                    st.success(f"دانش‌آموز {student_to_delete} از سیستم حذف شد.")
                    st.rerun()

    with tab3:
        st.markdown("### 📊 بارگذاری دسته‌جمعی اسامی از فایل اکسل (Excel / CSV)")
        st.info("نمونه الگوی فایل اکسل شامل ستون‌های: نام، نام خانوادگی، کد ملی، رمز اختصاصی، شماره همراه اولیا، گروه کلاسی")
        
        sample_df = pd.DataFrame([
            {"نام": "محمدیاسین", "نام خانوادگی": "حیدری", "کد ملی": "1002223344", "رمز اختصاصی": "1234", "شماره همراه اولیا": "09182222222", "گروه کلاسی": "گروه ارمغان 🚀"},
            {"نام": "امیرعلی", "نام خانوادگی": "رضایی", "کد ملی": "1003334455", "رمز اختصاصی": "1234", "شماره همراه اولیا": "09183333333", "گروه کلاسی": "گروه دانا 💡"}
        ])
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            sample_df.to_excel(writer, index=False, sheet_name='Students')
        st.download_button("📥 دانلود الگوی نمونه فایل اکسل", output.getvalue(), "sample_students.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        uploaded_file = st.file_uploader("انتخاب فایل اکسل اسامی:", type=['xlsx', 'xls', 'csv'], key=f"excel_uploader_{st.session_state['excel_upload_key']}")
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

    with tab4:
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
            title = st.text_input("عنوان رفتار:", placeholder="مثلاً: مشارکت عالی در فعالیت گروهی")
            log_date = st.text_input("تاریخ ثبت (شمسی):", value=get_current_shamsi_date())
            
        desc = st.text_area("توضیحات تکمیلی آموزگار:", placeholder="توضیحات رفتار مشاهده شده...")
        
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
            
            # Show Instant HTML Card Container
            html_card = generate_behavior_report_html(selected_student, nat_id, st_grp, b_type, title.strip(), desc.strip(), log_date.strip())
            with st.expander("👁️ مشاهده لوح / کارت رسمی رفتاری (نمایش آنلاین)", expanded=True):
                components.html(html_card, height=480, scrolling=True)
                
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

# ---------------------------------------------------------
# 5. ONLINE QUIZ CREATOR (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (طراحی و مدیریت آزمون‌ها)")
    
    tab_q1, tab_q2 = st.tabs(["➕ ساخت آزمون جدید و طراحی سوالات", "📋 مدیریت آزمون‌های ساخته‌شده و نتایج"])
    
    with tab_q1:
        st.markdown("### ➕ ساخت آزمون جدید")
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            quiz_title = st.text_input("عنوان آزمون:", placeholder="مثلاً: آزمونک جامع فصل ۱ و ۲ ریاضی")
            quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS)
        with col_q2:
            quiz_duration = st.number_input("زمان پاسخ‌گویی (دقیقه):", min_value=5, max_value=180, value=60)
            q_count = st.slider("تعداد سوالات آزمون:", min_value=1, max_value=10, value=3)
            
        questions_input_list = []
        st.markdown("---")
        st.markdown("#### 📝 طراحی سوالات آزمون:")
        
        for i in range(q_count):
            st.markdown(f"##### 📌 سوال شماره {i+1}:")
            col_q_type, col_q_text = st.columns([1, 3])
            with col_q_type:
                q_type = st.selectbox(f"نوع سوال {i+1}:", ["تستی (۴ گزینه‌ای)", "تشریحی"], key=f"qtype_{i}")
            with col_q_text:
                q_text = st.text_area(f"متن سوال {i+1}:", key=f"qtext_{i}")
                
            if "تستی" in q_type:
                col_o1, col_o2 = st.columns(2)
                with col_o1:
                    o1 = st.text_input(f"گزینه ۱:", key=f"o1_{i}")
                    o2 = st.text_input(f"گزینه ۲:", key=f"o2_{i}")
                with col_o2:
                    o3 = st.text_input(f"گزینه ۳:", key=f"o3_{i}")
                    o4 = st.text_input(f"گزینه ۴:", key=f"o4_{i}")
                correct_opt = st.selectbox(f"گزینه صحیح سوال {i+1}:", [1, 2, 3, 4], key=f"corr_{i}")
                questions_input_list.append(('mcq', q_text, o1, o2, o3, o4, correct_opt, "", ""))
            else:
                m_ans = st.text_area(f"پاسخ نمونه / راهنمای تصحیح معلم:", key=f"mans_{i}")
                expl = st.text_input(f"توضیحات تکمیلی / راهنمایی:", key=f"expl_{i}")
                questions_input_list.append(('essay', q_text, "", "", "", "", 0, m_ans, expl))
            st.markdown("---")
            
        if st.button("💾 ثبت نهایی آزمون و ذخیره در دیتابیس"):
            if quiz_title.strip():
                shamsi_today = get_current_shamsi_date()
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO quizzes (title, subject, duration_minutes, created_at) VALUES (?, ?, ?, ?)",
                        (quiz_title.strip(), quiz_subject, quiz_duration, shamsi_today)
                    )
                    new_quiz_id = cursor.lastrowid
                    
                    for q_data in questions_input_list:
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (new_quiz_id, q_data[0], q_data[1], q_data[2], q_data[3], q_data[4], q_data[5], q_data[6], q_data[7], q_data[8]))
                    conn.commit()
                st.balloons()
                st.success(f"🎉 آزمون '{quiz_title}' با موفقیت ساخته شد و در دیتابیس ذخیره گردید!")
            else:
                st.warning("لطفاً عنوان آزمون را وارد کنید.")

    with tab_q2:
        st.markdown("### 📋 لیست آزمون‌های فعال و مدیریت نتایج")
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'زمان (دقیقه)', created_at AS 'تاریخ ساخت' FROM quizzes ORDER BY id DESC", conn)
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True, hide_index=True)
            
            selected_quiz_id = st.selectbox("انتخاب آزمون جهت مشاهده نتایج:", quizzes_df['id'].tolist(), format_func=lambda x: quizzes_df[quizzes_df['id'] == x]['عنوان'].values[0])
            if selected_quiz_id:
                with get_connection() as conn:
                    results_df = safe_read_sql("""
                        SELECT s.first_name || ' ' || s.last_name AS 'نام دانش‌آموز', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت'
                        FROM quiz_results r JOIN students s ON r.student_id = s.id
                        WHERE r.quiz_id = ? ORDER BY r.id DESC
                    """, conn, params=(selected_quiz_id,))
                if not results_df.empty:
                    st.dataframe(results_df, use_container_width=True, hide_index=True)
                else:
                    st.info("هنوز نتیجه‌ای برای این آزمون ثبت نشده است.")
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
        
    if students_df.empty:
        st.warning("لطفاً ابتدا اسامی دانش‌آموزان توسط معلم وارد شود.")
    elif quizzes_df.empty:
        st.warning("در حال حاضر آزمون فعالی وجود ندارد.")
    else:
        col_take1, col_take2 = st.columns(2)
        with col_take1:
            student_name = st.selectbox("نام و نام خانوادگی خود را انتخاب کنید:*", students_df['full_name'].tolist())
        with col_take2:
            quiz_name = st.selectbox("آزمون مورد نظر را انتخاب کنید:*", quizzes_df['title'].tolist())
            
        s_id = int(students_df[students_df['full_name'] == student_name]['id'].values[0])
        q_row = quizzes_df[quizzes_df['title'] == quiz_name].iloc[0]
        q_id = int(q_row['id'])
        
        with get_connection() as conn:
            prev_result = conn.execute("SELECT * FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if prev_result:
            st.success(f"✅ دانش‌آموز عزیز {student_name}؛ شما قبلاً در این آزمون شرکت کرده‌اید.")
            st.metric("نمره تستی ثبت‌شده:", f"{prev_result['score']} از {prev_result['total_questions']} ({prev_result['percentage']:.1f}٪)")
        else:
            st.markdown(f"""
            <div class="quote-card">
                <h3>📖 {quiz_name} ({q_row['subject']})</h3>
                <p>⏱️ زمان پاسخ‌گویی: <b>{q_row['duration_minutes']} دقیقه</b> | لطفاً با دقت به تمام سوالات پاسخ دهید.</p>
            </div>
            """, unsafe_allow_html=True)
            
            with get_connection() as conn:
                questions_rows = conn.execute("SELECT * FROM questions WHERE quiz_id = ? ORDER BY id ASC", (q_id,)).fetchall()
                
            if questions_rows:
                student_mcq_ans = {}
                student_essay_ans = {}
                
                with st.form(f"take_quiz_form_{s_id}_{q_id}"):
                    for idx, q in enumerate(questions_rows):
                        st.markdown(f"### 📌 سوال {idx+1}: {q['question_text']}")
                        if q['question_type'] == 'mcq':
                            opts = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                            user_ans = st.radio(
                                f"پاسخ سوال {idx+1}:",
                                options=[1, 2, 3, 4],
                                format_func=lambda x: f"گزینه {x}: {opts[x-1]}",
                                key=f"ans_mcq_{q['id']}_{s_id}"
                            )
                            student_mcq_ans[q['id']] = (user_ans, q['correct_option'])
                        else:
                            essay_ans = st.text_area(f"پاسخ تشریحی شما برای سوال {idx+1}:", key=f"ans_essay_{q['id']}_{s_id}")
                            student_essay_ans[q['id']] = essay_ans
                        st.markdown("---")
                        
                    photo = st.camera_input("📸 احراز هویت چهره دانش‌آموز (اختیاری):", key=f"cam_{s_id}_{q_id}")
                    submit_quiz = st.form_submit_button("🏁 پایان آزمون و ثبت نهایی پاسخ‌ها")
                    
                    if submit_quiz:
                        photo_data_str = ""
                        if photo is not None:
                            import base64
                            photo_data_str = "data:image/png;base64," + base64.b64encode(photo.getvalue()).decode('utf-8')
                            
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
# 7. DASHBOARD & ACADEMIC PORTFOLIO WITH CHARTS
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد تحلیلی، کارنامه جامع تحصیلی و پوشه کار دانش‌آموز")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعات دانش‌آموزی در سیستم یافت نشد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده کارنامه جامع:", students_df['full_name'].tolist())
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        
        # Privacy Guard
        if not st.session_state['is_teacher_logged_in']:
            with get_connection() as conn:
                real_pin = conn.execute("SELECT pin_code FROM students WHERE id = ?", (s_id,)).fetchone()
                pin_code_db = str(real_pin['pin_code']).strip() if real_pin and real_pin['pin_code'] else '1234'
            
            st.info("🔒 جهت حفظ حریم خصوصی، مشاهده کارنامه نیازمند رمز ۴ رقمی اختصاصی دانش‌آموز است.")
            input_pin = st.text_input("🔑 رمز ۴ رقمی اختصاصی دانش‌آموز را وارد کنید:", type="password", key="portfolio_pin_guard")
            if input_pin.strip() != pin_code_db:
                st.warning("⚠️ لطفاً رمز ۴ رقمی اختصاصی دانش‌آموز را به درستی وارد کنید.")
                st.stop()
            else:
                st.success("🔓 احراز هویت با موفقیت انجام شد!")
                
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
            components.html(portfolio_html, height=650, scrolling=True)

        portfolio_pdf = generate_comprehensive_portfolio_pdf(s_id)
        st.download_button("📥 دانلود فایل پی دی اف کارنامه جامع (PDF معتبر قابل پرینت)", data=portfolio_pdf, file_name=f"report_card_{selected_student}.pdf", mime="application/pdf")
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with c2:
            st.metric("موارد رفتاری ثبت‌شده:", beh_count)
        with c3:
            st.metric("میانگین درصد آزمون آنلاین:", quiz_avg_str)
            
        st.markdown("---")
        
        # 📈 INTERACTIVE ACADEMIC GROWTH CHARTS
        st.subheader("📈 نمودارهای تحلیلی رشد تحصیلی و عملکرد آزمون‌ها")
        col_ch1, col_ch2 = st.columns(2)
        
        with col_ch1:
            st.markdown("##### 📉 نمودار روند رشد نمرات آزمون‌های آنلاین:")
            with get_connection() as conn:
                df_chart = safe_read_sql("""
                    SELECT q.title AS 'عنوان آزمون', r.percentage AS 'درصد'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id 
                    WHERE r.student_id = ? ORDER BY r.id ASC
                """, conn, params=(s_id,))
            if not df_chart.empty:
                st.line_chart(df_chart.set_index('عنوان آزمون'))
            else:
                st.info("برای رسم نمودار رشد، شرکت در حداقل یک آزمون لازم است.")
                
        with col_ch2:
            st.markdown("##### 📊 توزیع سطوح ارزشیابی‌های کیفی-توصیفی:")
            with get_connection() as conn:
                df_levels = safe_read_sql("""
                    SELECT level AS 'سطح', COUNT(*) AS 'تعداد'
                    FROM evaluations WHERE student_id = ? GROUP BY level
                """, conn, params=(s_id,))
            if not df_levels.empty:
                st.bar_chart(df_levels.set_index('سطح'))
            else:
                st.info("ارزشیابی توصیفی درسی ثبت نشده است.")

        st.markdown("---")
        tab_d1, tab_d2, tab_d3 = st.tabs(["📝 ارزشیابی‌های توصیفی دروس ۷‌گانه", "🌟 سوابق رفتاری و انضباطی", "📊 کارنامه آزمون‌های آنلاین"])
        
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
            else:
                st.info("نتیجه آزمونی ثبت نشده است.")

