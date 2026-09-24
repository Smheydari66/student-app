import streamlit as st
import sqlite3
import pandas as pd
import io
import json
from datetime import datetime

# ---------------------------------------------------------
# Page Configuration & Modern Theme Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس و آزمون آنلاین - پایه پنجم",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast CSS for Perfect Readability (White Text in all inputs)
st.markdown("""
<style>
    @import url('https://v1.fontapi.ir/font/vazir/Vazir.css');
    
    html, body, [class*="css"] {
        font-family: 'Vazir', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* Input fields & Selectboxes - Pure White Text & High Contrast */
    input, select, textarea, div[data-baseweb="select"] {
        color: #ffffff !important;
        background-color: #1e293b !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
    }
    
    /* Radio Navigation Options - Pure White Text */
    div[data-testid="stRadio"] label {
        color: #ffffff !important;
        font-weight: bold !important;
        font-size: 1.05rem !important;
        background-color: #1e293b !important;
        padding: 8px 14px !important;
        border-radius: 8px !important;
        border: 1px solid #334155 !important;
        margin-bottom: 6px !important;
        cursor: pointer !important;
    }
    div[data-testid="stRadio"] label:hover {
        border-color: #38bdf8 !important;
        background-color: #0284c7 !important;
    }
    
    /* Dropdown Popover List */
    div[data-baseweb="popover"], ul[role="listbox"], li[role="option"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    li[role="option"]:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
    
    /* Labels */
    label, p, span, h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    
    /* Cards and Containers */
    .welcome-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 2px solid #38bdf8;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(56, 189, 248, 0.15);
    }
    
    .quote-box {
        background: #1e1b4b;
        border-right: 6px solid #818cf8;
        padding: 16px 20px;
        border-radius: 8px;
        margin: 16px 0;
    }
    
    .feature-box {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #0284c7 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        padding: 10px 24px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #0369a1 0%, #1d4ed8 100%) !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Database Initialization & Robust Migration
# ---------------------------------------------------------
DB_FILE = "class_management.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create base tables if they don't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            national_code TEXT UNIQUE,
            first_name TEXT,
            last_family_name TEXT,
            parent_phone TEXT,
            notes TEXT,
            student_group TEXT DEFAULT 'گروه عمومی',
            avatar TEXT DEFAULT '🎓'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT,
            eval_date TEXT,
            grade_level TEXT,
            feedback TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS behavior_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            log_date TEXT,
            behavior_type TEXT,
            score INTEGER,
            description TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            duration_minutes INTEGER DEFAULT 60,
            created_at TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question_type TEXT DEFAULT 'mcq',
            question_text TEXT,
            option_1 TEXT,
            option_2 TEXT,
            option_3 TEXT,
            option_4 TEXT,
            correct_option INTEGER,
            model_answer TEXT,
            explanation TEXT,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            student_id INTEGER,
            submission_date TEXT,
            score REAL,
            total_questions INTEGER,
            essay_answers TEXT,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    """)
    
    # Robust Auto-Schema Migration for Old Database Files on Streamlit Cloud
    migrations = [
        ("students", "student_group", "TEXT DEFAULT 'گروه عمومی'"),
        ("students", "avatar", "TEXT DEFAULT '🎓'"),
        ("quizzes", "is_active", "INTEGER DEFAULT 1"),
        ("quizzes", "duration_minutes", "INTEGER DEFAULT 60"),
        ("questions", "question_type", "TEXT DEFAULT 'mcq'"),
        ("questions", "model_answer", "TEXT"),
        ("questions", "explanation", "TEXT"),
        ("quiz_submissions", "essay_answers", "TEXT")
    ]
    
    for table, column, col_type in migrations:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            cols = [row[1] for row in cursor.fetchall()]
            if column not in cols:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        except Exception:
            pass
            
    conn.commit()
    conn.close()

# Safe Read SQL Query Helper (Prevents OperationalError from crashing app)
def safe_read_sql(query, params=None, fallback_cols=None):
    init_db()
    conn = get_connection()
    try:
        if params:
            return pd.read_sql_query(query, conn, params=params)
        else:
            return pd.read_sql_query(query, conn)
    except Exception:
        # Retry after re-initializing DB
        init_db()
        try:
            if params:
                return pd.read_sql_query(query, conn, params=params)
            else:
                return pd.read_sql_query(query, conn)
        except Exception:
            if fallback_cols:
                return pd.DataFrame(columns=fallback_cols)
            return pd.DataFrame()
    finally:
        conn.close()

# Initialize Database Schema
init_db()

# Seed default 29 students if table is empty
def seed_default_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM students")
    count = cursor.fetchone()[0]
    if count == 0:
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
                INSERT INTO students (national_code, first_name, last_family_name, parent_phone, student_group)
                VALUES (?, ?, ?, ?, ?)
            """, st_item)
        conn.commit()
    conn.close()

seed_default_students()

# Seed Default Sample Quiz
def seed_default_quiz():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM quizzes")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO quizzes (title, duration_minutes, created_at, is_active) VALUES (?, ?, ?, 1)",
                       ("آزمون جامع ریاضی و علوم پایه پنجم (مهرماه)", 60, datetime.now().strftime("%Y-%m-%d")))
        quiz_id = cursor.lastrowid
        
        sample_questions = [
            ("mcq", "ارزش مکانی رقم ۷ در عدد ۳۲۷,۴۰۵,۰۰۰ چیست؟", "یکان میلیون", "دهگان میلیون", "صدگان هزار", "دهگان هزار", 1, "", "رقم ۷ در مرتبه یکان میلیون قرار دارد."),
            ("mcq", "کدام پدیده نشان‌دهنده تغییر شیمیایی است؟", "ذوب شدن یخ", "پختن نان و سوختن چوب", "تبخیر آب", "خرد کردن کاغذ", 2, "", "پختن نان و سوختن چوب تغییر شیمیایی است زیرا جنس ماده تغییر می‌کند."),
            ("mcq", "حاصل عبارت ۵/۴ + ۳/۷ کدام است؟", "۸/۱", "۹/۱", "۹/۴", "۸/۷", 2, "", "۵/۴ به علاوه ۳/۷ برابر با ۹/۱ می‌باشد."),
            ("essay", "علت نام‌گذاری لایه‌های زمین به سنگ‌کره و خمیرکره را توضیح دهید.", "", "", "", "", 0, "سنگ‌کره بخش سخت و جامد رویی زمین است و خمیرکره بخش نسبتاً داغ و حالت خمیری زیر آن است.", "سنگ‌کره روی خمیرکره حرکت می‌کند و باعث ایجاد زلزله و آتشفشان می‌شود."),
            ("essay", "مراحل روش علمی را به ترتیب نام ببرید و اهمیت فرضیه‌سازی را بیان کنید.", "", "", "", "", 0, "۱- مشاهده ۲- طرح پرسش ۳- فرضیه‌سازی ۴- آزمایش ۵- نتیجه‌گیری.", "فرضیه‌سازی پاسخ احتمالی به پرسش است که راه را برای آزمایش روشن می‌کند.")
        ]
        
        for q in sample_questions:
            cursor.execute("""
                INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
        conn.commit()
    conn.close()

seed_default_quiz()

# ---------------------------------------------------------
# Session State & Authentication Control
# ---------------------------------------------------------
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False
if 'teacher_password' not in st.session_state:
    st.session_state['teacher_password'] = "1234"
if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 0
if 'show_welcome_page' not in st.session_state:
    st.session_state['show_welcome_page'] = True

# Helper Student Fetcher
def load_students():
    df = safe_read_sql("SELECT * FROM students ORDER BY last_family_name, first_name",
                       fallback_cols=['id', 'national_code', 'first_name', 'last_family_name', 'parent_phone', 'notes', 'student_group', 'avatar'])
    return df

# ---------------------------------------------------------
# HEADER & AUTHENTICATION BAR
# ---------------------------------------------------------
st.markdown("""
<div class="welcome-card">
    <h2 style="margin:0; color:#38bdf8 !important;">🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی</h2>
    <p style="margin-top:6px; margin-bottom:0; color:#94a3b8 !important;">
        <b>دبستان شهید مطهری مهران</b> — ارزشیابی کیفی-توصیفی، تحلیل عملکرد، آزمون‌ساز آنلاین و گروه‌بندی کلاسی
    </p>
</div>
""", unsafe_allow_html=True)

# Top Bar Navigation & Teacher Auth Login Card
top_col1, top_col2 = st.columns([3, 1])

with top_col1:
    if st.button("🏠 صفحه خوش‌آمدگویی و معرفی اهداف"):
        st.session_state['show_welcome_page'] = True

with top_col2:
    if st.session_state['is_teacher_logged_in']:
        st.success("✅ حالت مدیریت آموزگار")
        if st.button("🚪 خروج آموزگار"):
            st.session_state['is_teacher_logged_in'] = False
            st.rerun()
    else:
        pop_col = st.popover("🔑 ورود مدیریت آموزگار") if hasattr(st, 'popover') else st.expander("🔑 ورود مدیریت آموزگار")
        with pop_col:
            st.write("لطفاً رمز عبور آموزگار را وارد کنید:")
            pass_input = st.text_input("رمز عبور:", type="password", key="top_pass_input")
            if st.button("ورود به سامانه"):
                if pass_input == st.session_state['teacher_password'] or pass_input == "مطهری":
                    st.session_state['is_teacher_logged_in'] = True
                    st.session_state['show_welcome_page'] = False
                    st.success("ورود موفقیت‌آمیز آموزگار!")
                    st.rerun()
                else:
                    st.error("❌ رمز عبور اشتباه است (رمز پیش‌فرض: 1234)")

# Teacher Change Password Panel (If logged in)
if st.session_state['is_teacher_logged_in']:
    with st.expander("🔐 تغییر رمز عبور آموزگار"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            new_pass1 = st.text_input("رمز عبور جدید:", type="password", key="np1")
        with col_p2:
            new_pass2 = st.text_input("تکرار رمز عبور جدید:", type="password", key="np2")
        if st.button("💾 ذخیره رمز جدید"):
            if new_pass1 and new_pass1 == new_pass2:
                st.session_state['teacher_password'] = new_pass1
                st.success("✅ رمز عبور آموزگار با موفقیت تغییر یافت.")
            else:
                st.error("❌ رمزهای جدید مطابقت ندارند.")

st.markdown("---")

# ---------------------------------------------------------
# WELCOME SPLASH PAGE (Shows by default or when clicked)
# ---------------------------------------------------------
if st.session_state['show_welcome_page']:
    st.markdown("""
    <div class="welcome-card">
        <h1 style="text-align:center; color:#38bdf8 !important;">🌸 به سامانه هوشمند مدیریت کلاس و آزمون آنلاین خوش آمدید 🌸</h1>
        <h3 style="text-align:center; color:#f8fafc !important;">پایه پنجم ابتدایی — دبستان شهید مطهری مهران</h3>
        <p style="text-align:center; font-size:1.1rem; color:#cbd5e1 !important;">
            🌱 <b>طراح و آموزگار: سید موسی حیدری</b>
        </p>
        
        <div class="quote-box">
            <h4 style="color:#a5b4fc !important; margin-top:0;">📜 فرمایش مقام معظم رهبری (حضرت آیت‌الله خامنه‌ای مدظله‌العالی) در باب فناوری و آموزش:</h4>
            <p style="font-size:1.05rem; line-height:1.8; color:#f1f5f9 !important;">
                «استفاده از ابزارهای نوين علمی و فناوری‌های هوشمند، مسیر یادگیری را برای دانش‌آموزان جذاب‌تر، عمیق‌تر و کارآمدتر می‌سازد. آموزش و پرورش ما باید مجهز به آخرین دستاوردهای علمی و تکنولوژی روز باشد تا نسل جوان ما برای آینده‌ای روشن و سراسر افتخار آماده شود.»
            </p>
        </div>
        
        <div class="feature-box">
            <h3 style="color:#38bdf8 !important;">🎯 اهداف و ویژگی‌های برجسته سامانه:</h3>
            <ul style="font-size:1.05rem; line-height:2;">
                <li><b>ارتقای کیفیت یادگیری و سنجش هوشمند:</b> برگزاری آزمون‌های آنلاین تستی و تشریحی همراه با زمان معکوس، تصحیح خودکار آنی و ارائه پاسخ‌نامه تحلیلی.</li>
                <li><b>ارزشیابی کیفی-توصیفی ۷ درس:</b> ثبت بازخوردهای توصیفی مستمر بر اساس دستورالعمل‌های رسمی دفتر دبیرخانه کشوری ابتدایی.</li>
                <li><b>شفافیت و آگاهی اولیا:</b> دسترسی خانواده‌ها به پوشه کار دیجیتال، کارنامه جامع و نمودارهای خطی رشد تحصیلی.</li>
                <li><b>پایش رفتاری و گروه‌بندی کلاسی:</b> دسته‌بندی ۲۹ دانش‌آموز در ۵ گروه متوازن (ارمغان 🚀، دانا 💡، تلاش 🌟، نخبگان 🏆، اندیشه 📖) و ثبت نشان‌های افتخار.</li>
            </ul>
        </div>
        
        <div class="feature-box">
            <h3 style="color:#38bdf8 !important;">🇮🇷 مطابقت کامل با برنامه‌ها و سند تحول بنیادین آموزش و پرورش:</h3>
            <p style="font-size:1.05rem; line-height:1.8;">
                این سامانه ۱۰۰٪ بر اساس ساحت‌های شش‌گانه تربیت (به‌ویژه ساحت علمی-فناوری و ساحت اخلاقی) و جدول بارم‌بندی و بودجه‌بندی رسمی امتحانات پایه پنجم ابتدایی طراحی شده است تا بستری هوشمند و عادلانه برای تمام دانش‌آموزان فراهم سازد.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_w1, col_w2, col_w3 = st.columns([1, 2, 1])
    with col_w2:
        if st.button("🚀 ورود به سامانه مدیریت کلاس و آزمون آنلاین", use_container_width=True):
            st.session_state['show_welcome_page'] = False
            st.rerun()
    st.stop()

# ---------------------------------------------------------
# NAVIGATION MENU (RADIO BUTTONS - NO EDITABLE TEXT / BACKSPACE ISSUES)
# ---------------------------------------------------------
st.subheader("📌 منوی اصلی سامانه (جهت جابه‌جایی بین بخش‌ها کلیک کنید):")

if st.session_state['is_teacher_logged_in']:
    menu_options = [
        "1️⃣ 🏠 صفحه اصلی و معرفی برنامه",
        "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌ها (۲۹ نفر)",
        "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی (ویژه معلم)",
        "4️⃣ 🌟 ثبت رفتار و انضباط (ویژه معلم)",
        "5️⃣ ✏️ آزمون‌ساز آنلاین (ویژه معلم)",
        "6️⃣ 📱 شرکت در آزمون آنلاین (عمومی / دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع (عمومی / اولیا)"
    ]
else:
    menu_options = [
        "1️⃣ 🏠 صفحه اصلی و معرفی برنامه",
        "6️⃣ 📱 شرکت در آزمون آنلاین (عمومی / دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع (عمومی / اولیا)"
    ]

menu_choice = st.radio("انتخاب بخش:", menu_options, horizontal=False, label_visibility="collapsed")

def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه در کادر '🔑 ورود مدیریت آموزگار' رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

# ---------------------------------------------------------
# 1. LANDING PAGE
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.subheader("👋 به بخش معرفی سامانه خوش آمدید")
    st.markdown("""
    <div class="welcome-card">
        <h3>🌱 طراح و توسعه‌دهنده سامانه: <b>سید موسی حیدری</b></h3>
        <p>آموزگار کلاس پنجم ابتدایی — دبستان شهید مطهری مهران</p>
    </div>
    
    <div class="feature-box">
        <h4>1️⃣ ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم</h4>
        <p>ثبت دقیق سطح عملکرد توصیفی دانش‌آموزان در دروس ریاضی، علوم، فارسی، نگارش، هدیه‌ها، قرآن و مطالعات اجتماعی.</p>
    </div>
    
    <div class="feature-box">
        <h4>2️⃣ آزمون‌ساز آنلاین با سوالات تستی و تشریحی</h4>
        <p>طراحی آزمون، تعیین زمان معکوس (مثلاً ۶۰ دقیقه)، تصحیح خودکار بخش تستی و ارائه تحلیل آموزشی.</p>
    </div>
    
    <div class="feature-box">
        <h4>3️⃣ مدیریت ۲۹ دانش‌آموز در ۵ گروه متوازن و بارگذاری اکسل</h4>
        <p>دسته‌بندی دانش‌آموزان در ۵ گروه کلاسی و قابلیت بارگذاری دسته‌جمعی اسامی از اکسل کمتر از ۱ ثانیه.</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. STUDENT MANAGEMENT & BULK EXCEL UPLOAD
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab1, tab2, tab3 = st.tabs(["📋 لیست دانش‌آموزان و گروه‌ها", "📊 ثبت دسته‌جمعی و سریع از اکسل", "➕ ثبت دانش‌آموز جدید (تکی)"])
    
    students_df = load_students()
    
    with tab1:
        if not students_df.empty:
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام یا کد ملی):")
            with col_s2:
                selected_group_filter = st.selectbox("فیلتر بر اساس گروه:", ["همه گروه‌ها", "گروه ارمغان 🚀", "گروه دانا 💡", "گروه تلاش 🌟", "گروه نخبگان 🏆", "گروه اندیشه 📖"])
            
            filtered_df = students_df.copy()
            if search_query:
                filtered_df = filtered_df[
                    filtered_df['first_name'].str.contains(search_query, na=False) |
                    filtered_df['last_family_name'].str.contains(search_query, na=False) |
                    filtered_df['national_code'].str.contains(search_query, na=False)
                ]
            if selected_group_filter != "همه گروه‌ها":
                filtered_df = filtered_df[filtered_df['student_group'] == selected_group_filter]
                
            st.dataframe(
                filtered_df[['id', 'national_code', 'first_name', 'last_family_name', 'student_group', 'parent_phone']],
                use_container_width=True,
                column_config={
                    "id": "شناسه",
                    "national_code": "کد ملی",
                    "first_name": "نام",
                    "last_family_name": "نام خانوادگی",
                    "student_group": "گروه آموزشی",
                    "parent_phone": "شماره اولیا"
                }
            )
            st.info(f"📊 تعداد کل دانش‌آموزان یافت‌شده: {len(filtered_df)} نفر")
        else:
            st.info("هنوز هیچ دانش‌آموزی ثبت نشده است.")

    with tab2:
        st.subheader("📊 بارگذاری دسته‌جمعی اسامی از فایل Excel / CSV")
        st.markdown("""
        <b>راهنما:</b> فایل اکسل شما باید حداقل شامل ستون‌های <code>کد ملی</code>، <code>نام</code> و <code>نام خانوادگی</code> باشد. ستون <code>گروه</code> نیز اختیاری است.
        """)
        
        # Download Sample Template
        sample_df = pd.DataFrame([
            {"کد ملی": "1001", "نام": "علی", "نام خانوادگی": "محمدی", "گروه": "گروه ارمغان 🚀", "شماره اولیا": "09120000000"},
            {"کد ملی": "1002", "نام": "رضا", "نام خانوادگی": "حسینی", "گروه": "گروه دانا 💡", "شماره اولیا": "09120000001"}
        ])
        csv_sample = sample_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 دانلود الگوی استاندارد اکسل/CSV", data=csv_sample, file_name="student_template.csv", mime="text/csv")
        
        # Clear Upload Key Button to allow selecting new files easily
        if st.button("🧹 پاکسازی و انتخاب فایل جدید"):
            st.session_state['excel_upload_key'] += 1
            st.rerun()

        uploaded_file = st.file_uploader("انتخاب فایل اکسل یا CSV دانش‌آموزان:", type=["xlsx", "csv"], key=f"uploader_{st.session_state['excel_upload_key']}")
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded_file)
                else:
                    df_up = pd.read_excel(uploaded_file)
                
                st.write("👀 پیش‌نمایش فایل بارگذاری‌شده:")
                st.dataframe(df_up.head())
                
                if st.button("🚀 افزودن همگی به دیتابیس کلاس"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    success_count = 0
                    groups = ["گروه ارمغان 🚀", "گروه دانا 💡", "گروه تلاش 🌟", "گروه نخبگان 🏆", "گروه اندیشه 📖"]
                    
                    for idx, row in df_up.iterrows():
                        nc = str(row.get('کد ملی', f"100{idx}")).strip()
                        fn = str(row.get('نام', '')).strip()
                        ln = str(row.get('نام خانوادگی', '')).strip()
                        phone = str(row.get('شماره اولیا', '09120000000')).strip()
                        grp = str(row.get('گروه', groups[idx % 5])).strip()
                        
                        if fn and ln:
                            try:
                                cursor.execute("""
                                    INSERT OR REPLACE INTO students (national_code, first_name, last_family_name, parent_phone, student_group)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (nc, fn, ln, phone, grp))
                                success_count += 1
                            except Exception:
                                pass
                    conn.commit()
                    conn.close()
                    st.success(f"🎉 تعداد {success_count} دانش‌آموز با موفقیت وارد دیتابیس شدند.")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ خطا در خواندن فایل: {e}")

    with tab3:
        st.subheader("➕ ثبت دانش‌آموز جدید (تکی)")
        with st.form("add_student_form"):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                fn = st.text_input("نام دانش‌آموز:")
                ln = st.text_input("نام خانوادگی:")
                nc = st.text_input("کد ملی (۱۰ رقم):")
            with col_a2:
                phone = st.text_input("شماره همراه اولیا:")
                grp = st.selectbox("گروه آموزشی:", ["گروه ارمغان 🚀", "گروه دانا 💡", "گروه تلاش 🌟", "گروه نخبگان 🏆", "گروه اندیشه 📖"])
            
            submit_btn = st.form_submit_button("💾 ثبت دانش‌آموز")
            if submit_btn:
                if fn and ln and nc:
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute("""
                            INSERT INTO students (national_code, first_name, last_family_name, parent_phone, student_group)
                            VALUES (?, ?, ?, ?, ?)
                        """, (nc, fn, ln, phone, grp))
                        conn.commit()
                        st.success(f"✅ دانش‌آموز {fn} {ln} با موفقیت ثبت شد.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ این کد ملی قبلاً در سامانه ثبت شده است.")
                    finally:
                        conn.close()
                else:
                    st.error("لطفاً نام، نام خانوادگی و کد ملی را وارد کنید.")

# ---------------------------------------------------------
# 3. QUALITATIVE EVALUATION
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("ابتدا دانش‌آموزان را در بخش پرونده ثبت کنید.")
        st.stop()
        
    student_list = [f"{row['id']} - {row['first_name']} {row['last_family_name']} ({row['student_group']})" for _, row in students_df.iterrows()]
    selected_st_str = st.selectbox("انتخاب دانش‌آموز:", student_list)
    st_id = int(selected_st_str.split(" - ")[0])
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        subject = st.selectbox("عنوان درس:", ["ریاضی", "علوم تجربی", "فارسی", "نگارش", "هدیه‌های آسمان", "قرآن", "مطالعات اجتماعی"])
        grade_level = st.selectbox("سطح عملکرد توصیفی:", ["خیلی خوب (خیلی عالی و مستمر)", "خوب (پذیرفته‌شده و مثبت)", "قابل قبول (نیازمند تلاش بیشتر)", "نیازمند آموزش و تلاش مجدد"])
    with col_e2:
        eval_date = st.date_input("تاریخ ارزشیابی:").strftime("%Y/%m/%d")
        feedback = st.text_area("بازخورد توصیفی و توصیه‌های آموزشی آموزگار:")
        
    if st.button("💾 ثبت ارزشیابی توصیفی"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO evaluations (student_id, subject, eval_date, grade_level, feedback)
            VALUES (?, ?, ?, ?, ?)
        """, (st_id, subject, eval_date, grade_level, feedback))
        conn.commit()
        conn.close()
        st.success("✅ ارزشیابی توصیفی با موفقیت ثبت گردید.")
        
    st.markdown("---")
    st.subheader("📜 سوابق ارزشیابی‌های ثبت‌شده برای این دانش‌آموز")
    eval_df = safe_read_sql("""
        SELECT subject as 'درس', grade_level as 'سطح عملکرد', eval_date as 'تاریخ', feedback as 'بازخورد'
        FROM evaluations WHERE student_id = ? ORDER BY id DESC
    """, params=(st_id,), fallback_cols=['درس', 'سطح عملکرد', 'تاریخ', 'بازخورد'])
    st.dataframe(eval_df, use_container_width=True)

# ---------------------------------------------------------
# 4. BEHAVIORAL LOGS & GROUP MONITORING
# ---------------------------------------------------------
elif menu_choice.startswith("4"):
    check_teacher_auth()
    st.header("🌟 مدیریت رفتار و مشاهدات انضباطی کلاسی")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("ابتدا دانش‌آموزان را ثبت کنید.")
        st.stop()
        
    student_list = [f"{row['id']} - {row['first_name']} {row['last_family_name']} ({row['student_group']})" for _, row in students_df.iterrows()]
    selected_st_str = st.selectbox("انتخاب دانش‌آموز جهت ثبت امتیاز:", student_list)
    st_id = int(selected_st_str.split(" - ")[0])
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        beh_type = st.selectbox("نوع مشاهده انضباطی / آموزشی:", ["مثبت 🌟 (تشویق و همکاری)", "منفی ⚠️ (تذکر انضباطی)"])
        score = st.number_input("میزان امتیاز (مثبت یا منفی):", min_value=1, max_value=20, value=5)
    with col_b2:
        log_date = st.date_input("تاریخ ثبت:").strftime("%Y/%m/%d")
        desc = st.text_input("توضیحات و علت ثبت امتیاز:")
        
    if st.button("💾 ثبت مشاهده انضباطی"):
        conn = get_connection()
        cursor = conn.cursor()
        final_score = score if "مثبت" in beh_type else -score
        cursor.execute("""
            INSERT INTO behavior_logs (student_id, log_date, behavior_type, score, description)
            VALUES (?, ?, ?, ?, ?)
        """, (st_id, log_date, beh_type, final_score, desc))
        conn.commit()
        conn.close()
        st.success("✅ امتیاز با موفقیت ثبت شد.")

    st.markdown("---")
    st.subheader("🏆 رتبه‌بندی گروه‌های کلاسی بر اساس مجموع امتیازات")
    group_scores_df = safe_read_sql("""
        SELECT s.student_group as 'گروه کلاسی', SUM(b.score) as 'مجموع امتیازات'
        FROM behavior_logs b
        JOIN students s ON b.student_id = s.id
        GROUP BY s.student_group ORDER BY SUM(b.score) DESC
    """, fallback_cols=['گروه کلاسی', 'مجموع امتیازات'])
    st.dataframe(group_scores_df, use_container_width=True)

# ---------------------------------------------------------
# 5. ONLINE QUIZ CREATOR (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین و طراحی سوالات (پایه پنجم)")
    
    q_tab1, q_tab2, q_tab3 = st.tabs(["➕ طراحی آزمون جدید", "📥 بارگذاری فایل آماده آزمون (JSON)", "📋 مدیریت آزمون‌های موجود"])
    
    with q_tab1:
        st.subheader("طراحی دستی آزمون جدید")
        quiz_title = st.text_input("عنوان آزمون (مثلاً: آزمون علوم درس ۱ و ۲):")
        duration = st.number_input("مدت زمان پاسخگویی (به دقیقه):", min_value=5, max_value=180, value=60)
        
        num_questions = st.number_input("تعداد سوالات آزمون (۵ تا ۲۰ سوال):", min_value=1, max_value=20, value=5)
        
        questions_data = []
        for i in range(int(num_questions)):
            st.markdown(f"#### ❓ سوال شماره {i+1}")
            q_type = st.radio(f"نوع سوال {i+1}:", ["تستی (۴ گزینه‌ای)", "تشریحی / تحلیلی"], key=f"qt_{i}")
            q_text = st.text_area(f"متن سوال {i+1}:", key=f"qtxt_{i}")
            
            if q_type == "تستی (۴ گزینه‌ای)":
                c1, c2 = st.columns(2)
                with c1:
                    o1 = st.text_input(f"گزینه ۱:", key=f"o1_{i}")
                    o2 = st.text_input(f"گزینه ۲:", key=f"o2_{i}")
                with c2:
                    o3 = st.text_input(f"گزینه ۳:", key=f"o3_{i}")
                    o4 = st.text_input(f"گزینه ۴:", key=f"o4_{i}")
                correct_opt = st.selectbox(f"گزینه صحیح سوال {i+1}:", [1, 2, 3, 4], key=f"co_{i}")
                m_ans = ""
            else:
                o1 = o2 = o3 = o4 = ""
                correct_opt = 0
                m_ans = st.text_area(f"پاسخ نمونه / راهنمای تصحیح سوال تشریحی {i+1}:", key=f"ma_{i}")
                
            expl = st.text_area(f"💡 تحلیل آموزشی و پاسخ‌نامه تشریحی سوال {i+1}:", key=f"exp_{i}")
            
            questions_data.append({
                "type": "mcq" if q_type == "تستی (۴ گزینه‌ای)" else "essay",
                "text": q_text,
                "o1": o1, "o2": o2, "o3": o3, "o4": o4,
                "correct": correct_opt,
                "model_answer": m_ans,
                "explanation": expl
            })
            
        if st.button("🚀 ثبت و انتشار آزمون آنلاین"):
            if quiz_title:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO quizzes (title, duration_minutes, created_at, is_active) VALUES (?, ?, ?, 1)",
                               (quiz_title, duration, datetime.now().strftime("%Y-%m-%d")))
                quiz_id = cursor.lastrowid
                
                for q in questions_data:
                    cursor.execute("""
                        INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (quiz_id, q['type'], q['text'], q['o1'], q['o2'], q['o3'], q['o4'], q['correct'], q['model_answer'], q['explanation']))
                conn.commit()
                conn.close()
                st.success("🎉 آزمون با موفقیت ساخته شد و برای دانش‌آموزان فعال گردید.")
            else:
                st.error("لطفاً عنوان آزمون را وارد کنید.")

    with q_tab2:
        st.subheader("📥 بارگذاری سریع فایل آزمون آماده (فرمت JSON)")
        st.write("اگر سوالات آزمون را به صورت فایل آماده دارید، می‌توانید فایل JSON را آپلود کنید:")
        
        sample_quiz_json = {
            "title": "آزمون علوم تجربی پایه پنجم",
            "duration_minutes": 45,
            "questions": [
                {
                    "question_type": "mcq",
                    "question_text": "کدام یک تغییر شیمیایی است؟",
                    "option_1": "ذوب شدن یخ",
                    "option_2": "پختن نان",
                    "option_3": "تبخیر آب",
                    "option_4": "مخلوط آب و نمک",
                    "correct_option": 2,
                    "model_answer": "",
                    "explanation": "پختن نان تغییر شیمیایی است زیرا جنس ماده عوض می‌شود."
                }
            ]
        }
        json_str = json.dumps(sample_quiz_json, ensure_ascii=False, indent=2)
        st.download_button("📥 دانلود الگوی نمونه فایل آزمون (JSON)", data=json_str.encode('utf-8'), file_name="quiz_template.json", mime="application/json")
        
        uploaded_json = st.file_uploader("بارگذاری فایل JSON آزمون:", type=["json"])
        if uploaded_json is not None:
            try:
                data = json.load(uploaded_json)
                st.write(f"<b>عنوان آزمون:</b> {data.get('title')}", unsafe_allow_html=True)
                st.write(f"<b>مدت زمان:</b> {data.get('duration_minutes')} دقیقه", unsafe_allow_html=True)
                
                if st.button("🚀 انتشار این فایل به عنوان آزمون فعال"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO quizzes (title, duration_minutes, created_at, is_active) VALUES (?, ?, ?, 1)",
                                   (data.get('title', 'آزمون آنلاین'), data.get('duration_minutes', 60), datetime.now().strftime("%Y-%m-%d")))
                    quiz_id = cursor.lastrowid
                    
                    for q in data.get('questions', []):
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (quiz_id, q.get('question_type', 'mcq'), q.get('question_text', ''), q.get('option_1', ''), q.get('option_2', ''), q.get('option_3', ''), q.get('option_4', ''), q.get('correct_option', 1), q.get('model_answer', ''), q.get('explanation', '')))
                    conn.commit()
                    conn.close()
                    st.success("✅ آزمون از روی فایل با موفقیت بارگذاری و منتشر شد.")
            except Exception as e:
                st.error(f"❌ خطا در پردازش فایل JSON: {e}")

    with q_tab3:
        st.subheader("📋 لیست آزمون‌های فعال و غیرفعال")
        quizzes_df = safe_read_sql("SELECT id as 'شناسه', title as 'عنوان آزمون', duration_minutes as 'زمان (دقیقه)', created_at as 'تاریخ ایجاد', is_active as 'وضعیت فعال' FROM quizzes ORDER BY id DESC", fallback_cols=['شناسه', 'عنوان آزمون', 'زمان (دقیقه)', 'تاریخ ایجاد', 'وضعیت فعال'])
        st.dataframe(quizzes_df, use_container_width=True)

# ---------------------------------------------------------
# 6. STUDENT ONLINE QUIZ TAKING
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین دانش‌آموزی")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("دانش‌آموزی ثبت نشده است.")
        st.stop()
        
    student_list = [f"{row['id']} - {row['first_name']} {row['last_family_name']} ({row['student_group']})" for _, row in students_df.iterrows()]
    selected_st_str = st.selectbox("دانش‌آموز عزیز؛ نام خود را انتخاب کنید:", student_list)
    st_id = int(selected_st_str.split(" - ")[0])
    
    # Active Quiz Fetcher using safe_read_sql
    quizzes_df = safe_read_sql("SELECT * FROM quizzes WHERE is_active = 1 ORDER BY id DESC", fallback_cols=['id', 'title', 'duration_minutes', 'created_at', 'is_active'])
    if quizzes_df.empty:
        st.info("در حال حاضر هیچ آزمون فعالی وجود ندارد.")
        st.stop()
        
    quiz_options = [f"{row['id']} - {row['title']} ({row['duration_minutes']} دقیقه)" for _, row in quizzes_df.iterrows()]
    selected_quiz_str = st.selectbox("انتخاب آزمون آنلاین:", quiz_options)
    quiz_id = int(selected_quiz_str.split(" - ")[0])
    
    quiz_info = quizzes_df[quizzes_df['id'] == quiz_id].iloc[0]
    duration = int(quiz_info['duration_minutes'])
    
    # Check if student already submitted
    existing_sub = safe_read_sql("SELECT * FROM quiz_submissions WHERE quiz_id = ? AND student_id = ?", params=(quiz_id, st_id))
    if not existing_sub.empty:
        st.success("✅ شما قبلاً در این آزمون شرکت کرده‌اید و پاسخ‌های شما ثبت شده است.")
        sub_row = existing_sub.iloc[0]
        st.markdown(f"<b>📊 نمره تستی شما: {sub_row['score']} از {sub_row['total_questions']}</b>", unsafe_allow_html=True)
        st.stop()
        
    st.markdown("---")
    st.info(f"⏱️ **زمان تعیین‌شده برای این آزمون: {duration} دقیقه می‌باشد.** به سوالات زیر پاسخ دهید:")
    
    questions_df = safe_read_sql("SELECT * FROM questions WHERE quiz_id = ? ORDER BY id ASC", params=(quiz_id,))
    
    user_mcq_answers = {}
    user_essay_answers = {}
    
    with st.form("take_quiz_form"):
        for idx, q in questions_df.iterrows():
            st.markdown(f"##### ❓ سوال {idx+1}: {q['question_text']}")
            if q['question_type'] == "mcq":
                opts = [f"۱) {q['option_1']}", f"۲) {q['option_2']}", f"۳) {q['option_3']}", f"۴) {q['option_4']}"]
                ans = st.radio(f"انتخاب گزینه سوال {idx+1}:", opts, key=f"sq_{q['id']}")
                opt_num = int(ans.split("）")[0]) if "）" in ans else int(ans.split(")")[0])
                user_mcq_answers[q['id']] = opt_num
            else:
                e_ans = st.text_area(f"پاسخ تشریحی شما برای سوال {idx+1}:", key=f"seq_{q['id']}")
                user_essay_answers[q['id']] = e_ans
                
        submit_quiz_btn = st.form_submit_button("🏁 پایان و ثبت نهایی پاسخ‌ها")
        
        if submit_quiz_btn:
            mcq_correct_count = 0
            total_mcq = 0
            
            for idx, q in questions_df.iterrows():
                if q['question_type'] == "mcq":
                    total_mcq += 1
                    if user_mcq_answers.get(q['id']) == q['correct_option']:
                        mcq_correct_count += 1
                        
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO quiz_submissions (quiz_id, student_id, submission_date, score, total_questions, essay_answers)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (quiz_id, st_id, datetime.now().strftime("%Y-%m-%d %H:%M"), mcq_correct_count, total_mcq, json.dumps(user_essay_answers, ensure_ascii=False)))
            conn.commit()
            conn.close()
            
            st.balloons()
            st.success(f"🎉 پاسخ‌های شما با موفقیت ثبت گردید. نمره بخش تستی: {mcq_correct_count} از {total_mcq}")
            
            st.markdown("### 💡 پاسخ‌نامه تشریحی و تحلیل آموزشی سوالات")
            for idx, q in questions_df.iterrows():
                st.markdown(f"<b>سوال {idx+1}: {q['question_text']}</b>", unsafe_allow_html=True)
                if q['question_type'] == "mcq":
                    st.write(f"گزینه صحیح: گزینه {q['correct_option']}")
                else:
                    st.write(f"پاسخ نمونه آموزگار: {q['model_answer']}")
                if q['explanation']:
                    st.info(f"تحلیل آموزشی: {q['explanation']}")
                st.markdown("---")

# ---------------------------------------------------------
# 7. COMPREHENSIVE PORTFOLIO & REPORT CARD DASHBOARD
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 پوشه کار و کارنامه جامع تحصیلی دانش‌آموز")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("هیچ دانش‌آموزی ثبت نشده است.")
        st.stop()
        
    student_list = [f"{row['id']} - {row['first_name']} {row['last_family_name']} ({row['student_group']})" for _, row in students_df.iterrows()]
    selected_st_str = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار:", student_list)
    st_id = int(selected_st_str.split(" - ")[0])
    
    st_info = students_df[students_df['id'] == st_id].iloc[0]
    
    st.markdown(f"""
    <div class="welcome-card">
        <h3 style="margin:0; color:#38bdf8 !important;">پرونده تحصیلی: {st_info['first_name']} {st_info['last_family_name']}</h3>
        <p style="margin-top:6px; margin-bottom:0;">
            <b>کد ملی:</b> {st_info['national_code']} | <b>گروه آموزشی:</b> {st_info['student_group']} | <b>شماره همراه اولیا:</b> {st_info['parent_phone']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_r1, tab_r2, tab_r3 = st.tabs(["📝 ارزشیابی توصیفی", "🌟 سوابق آزمون‌های آنلاین", "🏆 امتیازات رفتاری"])
    
    with tab_r1:
        st.subheader("سوابق ارزشیابی کیفی-توصیفی ۷ درس")
        eval_df = safe_read_sql("""
            SELECT subject as 'عنوان درس', grade_level as 'سطح عملکرد', eval_date as 'تاریخ', feedback as 'بازخورد آموزگار'
            FROM evaluations WHERE student_id = ? ORDER BY id DESC
        """, params=(st_id,), fallback_cols=['عنوان درس', 'سطح عملکرد', 'تاریخ', 'بازخورد آموزگار'])
        
        if not eval_df.empty:
            st.dataframe(eval_df, use_container_width=True)
            # Excel & CSV Download for Portfolio
            csv_data = eval_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 دانلود خروجی سوابق توصیفی (CSV/Excel)", data=csv_data, file_name=f"evaluations_{st_info['last_family_name']}.csv", mime="text/csv")
        else:
            st.info("هنوز ارزشیابی توصیفی برای این دانش‌آموز ثبت نشده است.")

    with tab_r2:
        st.subheader("سوابق شرکت در آزمون‌های آنلاین")
        sub_df = safe_read_sql("""
            SELECT q.title as 'عنوان آزمون', s.submission_date as 'تاریخ شرکت', s.score as 'نمره تستی', s.total_questions as 'کل سوالات تستی'
            FROM quiz_submissions s
            JOIN quizzes q ON s.quiz_id = q.id
            WHERE s.student_id = ? ORDER BY s.id DESC
        """, params=(st_id,), fallback_cols=['عنوان آزمون', 'تاریخ شرکت', 'نمره تستی', 'کل سوالات تستی'])
        
        if not sub_df.empty:
            st.dataframe(sub_df, use_container_width=True)
        else:
            st.info("دانش‌آموز هنوز در هیچ آزمون آنلاینی شرکت نکرده است.")

    with tab_r3:
        st.subheader("سوابق امتیازات انضباطی و تشویقی")
        beh_df = safe_read_sql("""
            SELECT log_date as 'تاریخ', behavior_type as 'نوع مشاهده', score as 'امتیاز', description as 'توضیحات'
            FROM behavior_logs WHERE student_id = ? ORDER BY id DESC
        """, params=(st_id,), fallback_cols=['تاریخ', 'نوع مشاهده', 'امتیاز', 'توضیحات'])
        
        if not beh_df.empty:
            st.dataframe(beh_df, use_container_width=True)
            total_beh_score = beh_df['امتیاز'].sum()
            st.metric("🏆 مجموع امتیازات انضباطی و تشویقی دانش‌آموز:", f"{total_beh_score} امتیاز")
        else:
            st.info("مشاهده انضباطی ثبت نشده است.")

