
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
# Page Configuration & Dark Sleek High-Contrast Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Persian / RTL CSS with forced Dark Background & White Text
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
    
    /* Forced White Text for All Markdown & Text Elements */
    p, span, label, h1, h2, h3, h4, h5, h6, div[data-testid="stMarkdownContainer"] *, .stRadio label, .stCheckbox label {
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
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .main-header h2, .main-header p {
        color: #ffffff !important;
        text-align: center !important;
        margin: 4px 0;
    }
    
    /* Card Boxes */
    .card-box {
        background-color: #1e293b !important;
        border: 1px solid #3b82f6 !important;
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    .quote-card {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%);
        border-right: 6px solid #fbbf24;
        border-left: 1px solid rgba(255, 255, 255, 0.15);
        border-top: 1px solid rgba(255, 255, 255, 0.15);
        border-bottom: 1px solid rgba(255, 255, 255, 0.15);
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 20px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.35);
    }
    
    /* Native Tabs Custom Styling for Mobile & Desktop */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: #1e293b !important;
        padding: 8px !important;
        border-radius: 12px !important;
        border: 1px solid #334155 !important;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #0f172a !important;
        color: #94a3b8 !important;
        border-radius: 8px !important;
        padding: 10px 16px !important;
        font-weight: 700 !important;
        border: 1px solid #334155 !important;
        font-size: 0.95rem !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: 1px solid #60a5fa !important;
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

def safe_read_sql(query, conn, params=()):
    try:
        return pd.read_sql_query(query, conn, params=params)
    except Exception:
        return pd.DataFrame()

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
            photo_data TEXT,
            essay_answers TEXT,
            submitted_at TEXT,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        
        # PRAGMA Migration Guards
        cursor.execute("PRAGMA table_info(students)")
        s_cols = [r['name'] for r in cursor.fetchall()]
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
            try: cursor.execute("ALTER TABLE quiz_results ADD COLUMN photo_data TEXT")
            except Exception: pass
        if 'essay_answers' not in r_cols:
            try: cursor.execute("ALTER TABLE quiz_results ADD COLUMN essay_answers TEXT")
            except Exception: pass

        conn.commit()

init_db()

# ---------------------------------------------------------
# Teacher Password Management
# ---------------------------------------------------------
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False

def check_teacher_password(input_pass):
    return input_pass.strip() in ["1234", "مطهری"]

# ---------------------------------------------------------
# Helper Functions & Constants
# ---------------------------------------------------------
FIFTH_GRADE_SUBJECTS = [
    "ریاضی", "علوم تجربی", "فارسی (خوانداری)", "نگارش فارسی",
    "مطالعات اجتماعی", "هدیه‌های آسمان", "آموزش قرآن"
]

EVALUATION_LEVELS = [
    "خیلی خوب 🌟", "خوب 🟢", "قابل قبول 🟡", "نیاز به تلاش مجدد 🔴"
]

CLASS_GROUPS = [
    "گروه ارمغان 🚀 (۶ نفر)", "گروه دانا 💡 (۶ نفر)",
    "گروه تلاش 🌟 (۶ نفر)", "گروه نخبگان 🏆 (۶ نفر)",
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

# ---------------------------------------------------------
# HTML Generator Helpers
# ---------------------------------------------------------
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
.report-card {{ background: {bg_color}; border: 2px solid {border_color}; border-radius: 12px; padding: 20px; margin-top: 15px; }}
.report-header {{ color: {theme_color}; font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 15px; border-bottom: 1px dashed {border_color}; padding-bottom: 8px; }}
.meta-table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 15px; background: #ffffff; border-radius: 8px; overflow: hidden; }}
.meta-table td {{ padding: 8px 12px; border: 1px solid #e2e8f0; }}
.content-text {{ font-size: 14px; line-height: 2; text-align: justify; margin: 15px 0; }}
.signature-table {{ width: 100%; margin-top: 30px; text-align: center; font-size: 13px; border-collapse: collapse; }}
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
        {'توفیق روزافزون شما را در مسیر اخلاق، دانایی و بالندگی از درگاه خداوند متعال خواستاریم.' if is_positive else 'خواهشمند است ضمن گفتگوی تربیتی و صمیمانه با فرزندتان، جهت پیگیری و بهبود این رفتار همکاری لازم را مبذول فرمایید.'}
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
body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; direction: rtl; text-align: right; padding: 25px; color: #0f172a; background: #ffffff; line-height: 1.6; font-size: 12px; }}
.letterhead {{ border-bottom: 3px double #1e3a8a; padding-bottom: 10px; margin-bottom: 15px; text-align: center; }}
.org-name {{ color: #1e3a8a; font-size: 13px; font-weight: bold; }}
.school-name {{ color: #0f172a; font-size: 17px; font-weight: bold; margin-top: 3px; }}
.sub-header {{ color: #475569; font-size: 11px; margin-top: 2px; }}
.meta-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; background: #f8fafc; border-radius: 6px; overflow: hidden; }}
.meta-table td {{ padding: 6px 10px; border: 1px solid #cbd5e1; font-size: 12px; }}
.analysis-box {{ background: #f0f9ff; border: 1px solid #0284c7; border-radius: 8px; padding: 12px; margin-top: 15px; }}
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

<div class="analysis-box">
    <h4 style="color: #0369a1; margin-top: 0; margin-bottom: 8px;">💡 خلاصه وضعیت تحصیلی و پرورشی:</h4>
    <p style="text-align: justify; margin-bottom: 8px;">
        تعداد ارزشیابی‌های ثبت‌شده: <b>{eval_count}</b> | موارد رفتاری انضباطی: <b>{beh_count}</b> | میانگین آزمون‌های آنلاین: <b>{quiz_avg_str}</b>
    </p>
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

# ---------------------------------------------------------
# TOP MAIN APP HEADER
# ---------------------------------------------------------
curr_shamsi = get_current_shamsi_date()
st.markdown(f"""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین — پایه پنجم ابتدایی</h2>
    <p>دبستان شهید مطهری مهران | آموزگار: سید موسی حیدری | 📅 تاریخ امروز: <b>{curr_shamsi}</b></p>
</div>
""", unsafe_allow_html=True)

# Top Teacher Auth Login Bar
col_l1, col_l2 = st.columns([3, 1])
with col_l1:
    if st.session_state['is_teacher_logged_in']:
        st.success("🟢 ورود موفقیت‌آمیز آموزگار — تمامی بخش‌های مدیریتی فعال گردیدند.")
    else:
        st.info("👤 حالت دانش‌آموز / عمومی فعال است. (جهت ورود آموزگار، رمز عبور را در کادر مقابل وارد کنید).")

with col_l2:
    if not st.session_state['is_teacher_logged_in']:
        with st.popover("🔑 ورود آموزگار"):
            pass_in = st.text_input("رمز عبور آموزگار:", type="password", key="pop_pass")
            if st.button("ورود به پنل مدیریت"):
                if check_teacher_password(pass_in):
                    st.session_state['is_teacher_logged_in'] = True
                    st.success("ورود با موفقیت انجام شد.")
                    st.rerun()
                else:
                    st.error("رمز عبور اشتباه است.")
    else:
        if st.button("🚪 خروج آموزگار"):
            st.session_state['is_teacher_logged_in'] = False
            st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# NATIVE LIGHTNING-FAST TABS NAVIGATION (0ms LAG)
# ---------------------------------------------------------
tab_names = [
    "🏠 ۱. صفحه اصلی و معرفی",
    "👨‍🎓 ۲. مدیریت دانش‌آموزان",
    "📝 ۳. ارزشیابی توصیفی",
    "🌟 ۴. مدیریت رفتار",
    "✏️ ۵. آزمون‌ساز آنلاین",
    "📱 ۶. شرکت در آزمون",
    "📊 ۷. داشبورد و کارنامه"
]

t1, t2, t3, t4, t5, t6, t7 = st.tabs(tab_names)

# ---------------------------------------------------------
# TAB 1: LANDING & OVERVIEW PAGE
# ---------------------------------------------------------
with t1:
    st.subheader("👋 به سامانه مدیریت هوشمند کلاس پنجم خوش آمدید")
    
    st.markdown("""
    <div class="card-box">
        <h3 style="color: #60a5fa !important; margin-bottom: 8px;">🌱 طراح و توسعه‌دهنده سامانه: <b>سید موسی حیدری</b></h3>
        <p style="font-size: 1.05rem;">آموزگار پایه پنجم ابتدایی — دبستان پسرانه هیئت امنایی شهید مطهری مهران</p>
    </div>
    
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

# ---------------------------------------------------------
# TAB 2: STUDENT MANAGEMENT (TEACHER ONLY)
# ---------------------------------------------------------
with t2:
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه وارد حساب مدیریت معلم شوید.")
    else:
        st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
        students_df = load_students()
        
        tb1, tb2 = st.tabs(["📋 لیست دانش‌آموزان", "➕ ثبت دانش‌آموز جدید"])
        with tb1:
            if not students_df.empty:
                st.dataframe(students_df, use_container_width=True, hide_index=True)
            else:
                st.info("دانش‌آموزی ثبت نشده است.")
                
        with tb2:
            with st.form("add_st_form"):
                fn = st.text_input("نام:*")
                ln = st.text_input("نام خانوادگی:*")
                nid = st.text_input("کد ملی:")
                pin = st.text_input("رمز ۴ رقمی اختصاصی:", value="1234")
                ph = st.text_input("شماره همراه اولیا:")
                grp = st.selectbox("گروه کلاسی:", CLASS_GROUPS)
                if st.form_submit_button("ثبت دانش‌آموز"):
                    if fn.strip() and ln.strip():
                        shamsi_today = get_current_shamsi_date()
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO students (first_name, last_name, national_id, pin_code, parent_phone, student_group, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (fn.strip(), ln.strip(), nid.strip(), pin.strip(), ph.strip(), grp, shamsi_today)
                            )
                            conn.commit()
                        st.success("دانش‌آموز با موفقیت ثبت شد.")
                        st.rerun()

# ---------------------------------------------------------
# TAB 3: QUALITATIVE EVALUATIONS (TEACHER ONLY)
# ---------------------------------------------------------
with t3:
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه وارد حساب مدیریت معلم شوید.")
    else:
        st.header("📝 ثبت ارزشیابی کیفی-توصیفی (پایه پنجم)")
        students_df = load_students()
        if students_df.empty:
            st.info("ابتدا اسامی دانش‌آموزان را ثبت کنید.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist(), key="e_st_sel")
                selected_subject = st.selectbox("انتخاب درس:", FIFTH_GRADE_SUBJECTS, key="e_sub_sel")
            with col2:
                selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS, key="e_lvl_sel")
                eval_date = st.text_input("تاریخ ارزشیابی (شمسی):", value=get_current_shamsi_date(), key="e_dt_sel")
                
            feedback_text = st.text_area("توصیف عملکرد و بازخورد آموزگار:", key="e_fb_txt")
            if st.button("ثبت ارزشیابی توصیفی", key="btn_save_eval"):
                s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
                with get_connection() as conn:
                    conn.execute(
                        "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                        (s_id, selected_subject, selected_level, feedback_text.strip(), eval_date.strip())
                    )
                    conn.commit()
                st.success("ارزشیابی توصیفی با موفقیت ثبت گردید.")

# ---------------------------------------------------------
# TAB 4: BEHAVIOR & DISCIPLINE (TEACHER ONLY)
# ---------------------------------------------------------
with t4:
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه وارد حساب مدیریت معلم شوید.")
    else:
        st.header("🌟 مدیریت رفتار و مشاهدات انضباطی")
        students_df = load_students()
        if students_df.empty:
            st.info("ابتدا اسامی دانش‌آموزان را ثبت کنید.")
        else:
            selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist(), key="b_st_sel")
            b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"], key="b_type_sel")
            title = st.text_input("عنوان مشاهده رفتاری:", key="b_title_in")
            desc = st.text_area("شرح و توضیحات تکمیلی:", key="b_desc_in")
            log_date = st.text_input("تاریخ ثبت (شمسی):", value=get_current_shamsi_date(), key="b_dt_in")
            
            if st.button("ثبت مشاهده رفتاری", key="btn_save_beh"):
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
                st.success("مشاهده رفتاری با موفقیت ثبت شد.")
                
                html_card = generate_behavior_report_html(selected_student, nat_id, st_grp, b_type, title.strip(), desc.strip(), log_date.strip())
                components.html(html_card, height=450, scrolling=True)

# ---------------------------------------------------------
# TAB 5: ONLINE QUIZ CREATOR (TEACHER ONLY)
# ---------------------------------------------------------
with t5:
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه وارد حساب مدیریت معلم شوید.")
    else:
        st.header("✏️ آزمون‌ساز آنلاین و طراحی سوالات")
        st.info("امکان ساخت آزمون‌های آنلاین و افزودن سوالات تستی و تشریحی.")

# ---------------------------------------------------------
# TAB 6: ONLINE QUIZ TAKING (STUDENTS)
# ---------------------------------------------------------
with t6:
    st.header("📱 شرکت در آزمون آنلاین دانش‌آموزان")
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = safe_read_sql("SELECT * FROM quizzes ORDER BY id DESC", conn)
        
    if students_df.empty or quizzes_df.empty:
        st.info("آزمون یا دانش‌آموزی در سیستم ثبت نشده است.")
    else:
        selected_student = st.selectbox("نام دانش‌آموز (خود را انتخاب کنید):", students_df['full_name'].tolist(), key="q_take_st")
        selected_quiz = st.selectbox("انتخاب آزمون آنلاین:", quizzes_df['title'].tolist(), key="q_take_qz")
        st.success(f"آزمون «{selected_quiz}» آماده شروع می‌باشد.")

# ---------------------------------------------------------
# TAB 7: DASHBOARD & PORTFOLIO
# ---------------------------------------------------------
with t7:
    st.header("📊 داشبورد تحلیلی و پوشه کار جامع دانش‌آموز")
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی وجود ندارد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار:", students_df['full_name'].tolist(), key="p_st_sel")
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

        # Render HTML Report Card directly INSIDE the App Page with Iframe isolation
        portfolio_html = generate_portfolio_report_html(selected_student, nat_id_str, phone_str, grp_str, eval_count, beh_count, quiz_avg_str)
        with st.expander("👁️ مشاهده برگه رسمی کارنامه (نمایش آنلاین درون سامانه)", expanded=True):
            components.html(portfolio_html, height=500, scrolling=True)

