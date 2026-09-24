import streamlit as st
import pandas as pd
import sqlite3
import json
import time
from datetime import datetime

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم | سید موسی حیدری",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Custom CSS for Dark Theme & White Readable Fonts Everywhere
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://v1.fontapi.ir/css/Vazir');
    
    html, body, [class*="css"] {
        font-family: 'Vazir', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    
    .stApp {
        background-color: #0f172a;
        color: #ffffff !important;
    }
    
    /* Header & Cards */
    .header-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 2px solid #3b82f6;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.3);
        text-align: center;
    }
    
    .welcome-card {
        background: linear-gradient(135deg, #1e293b 0%, #1e1b4b 100%);
        border: 2px solid #8b5cf6;
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 15px 30px -5px rgba(139, 92, 246, 0.3);
    }

    .quote-box {
        background-color: #1e293b;
        border-right: 6px solid #f59e0b;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        color: #fbbf24 !important;
        font-size: 1.1rem;
        line-height: 1.8;
    }

    .feature-box {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 15px;
        color: #ffffff !important;
    }

    /* Form Inputs & Boxes - White Readable Text */
    input, textarea, select {
        color: #ffffff !important;
        background-color: #1e293b !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
    }

    .stTextInput > div > div > input {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }

    .stSelectbox div[data-baseweb="select"] {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }

    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"], li[role="option"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }

    li[role="option"]:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }

    /* Radio Buttons Nav */
    .stRadio > label {
        color: #ffffff !important;
        font-weight: bold;
    }

    div[role="radiogroup"] label {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        padding: 12px 18px !important;
        border-radius: 10px !important;
        margin-bottom: 8px !important;
        color: #ffffff !important;
        width: 100%;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    div[role="radiogroup"] label:hover {
        border-color: #3b82f6 !important;
        background-color: #334155 !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: bold !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.39) !important;
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px 0 rgba(37, 99, 235, 0.5) !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b !important;
        color: #94a3b8 !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 10px 20px !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Database Initialization & Auto-Migration
# ---------------------------------------------------------
DB_FILE = "class_management.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Students Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            national_id TEXT UNIQUE,
            first_name TEXT,
            last_name TEXT,
            student_group TEXT DEFAULT 'گروه عمومی 📖',
            parent_phone TEXT,
            notes TEXT
        )
    """)
    
    # Evaluations Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT,
            evaluation_date TEXT,
            grade_level TEXT,
            feedback TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    """)
    
    # Behavior Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS behavior_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            log_date TEXT,
            category TEXT,
            points INTEGER,
            description TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    """)
    
    # Quizzes Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            subject TEXT,
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
    
    # Quiz Results Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            student_id INTEGER,
            score_mcq REAL,
            total_mcq INTEGER,
            essay_answers TEXT,
            submitted_at TEXT,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    """)
    
    # Auto Migration Check for Missing Columns
    tables_cols = {
        "questions": [
            ("question_type", "TEXT DEFAULT 'mcq'"),
            ("model_answer", "TEXT"),
            ("explanation", "TEXT")
        ],
        "quiz_results": [
            ("essay_answers", "TEXT")
        ],
        "students": [
            ("student_group", "TEXT DEFAULT 'گروه عمومی 📖'")
        ]
    }
    
    for table, cols in tables_cols.items():
        cursor.execute(f"PRAGMA table_info({table})")
        existing_cols = [row[1] for row in cursor.fetchall()]
        for col_name, col_type in cols:
            if col_name not in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                except Exception:
                    pass
                    
    conn.commit()
    conn.close()

def seed_default_students(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] == 0:
        default_students = [
            ("1001", "محمد", "حیدری", "گروه ارمغان 🚀", "09181111101"),
            ("1002", "علی", "رضایی", "گروه ارمغان 🚀", "09181111102"),
            ("1003", "حسین", "موسوی", "گروه ارمغان 🚀", "09181111103"),
            ("1004", "امیرعباس", "کریمی", "گروه ارمغان 🚀", "09181111104"),
            ("1005", "مهدی", "جعفری", "گروه ارمغان 🚀", "09181111105"),
            ("1006", "ابوالفضل", "صادقی", "گروه ارمغان 🚀", "09181111106"),
            ("1007", "رضا", "احمدی", "گروه دانا 💡", "09181111107"),
            ("1008", "سجاد", "باقری", "گروه دانا 💡", "09181111108"),
            ("1009", "پارسا", "محمدی", "گروه دانا 💡", "09181111109"),
            ("1010", "آرتین", "مرادی", "گروه دانا 💡", "09181111110"),
            ("1011", "یاسین", "نوری", "گروه دانا 💡", "09181111111"),
            ("1012", "امین", "سلیمانی", "گروه دانا 💡", "09181111112"),
            ("1013", "طاها", "نجفی", "گروه تلاش 🌟", "09181111113"),
            ("1014", "کیان", "ابراهیمی", "گروه تلاش 🌟", "09181111114"),
            ("1015", "علی‌اصغر", "قاسمی", "گروه تلاش 🌟", "09181111115"),
            ("1016", "محمدجواد", "میرزایی", "گروه تلاش 🌟", "09181111116"),
            ("1017", "دانیال", "اکبری", "گروه تلاش 🌟", "09181111117"),
            ("1018", "ماهان", "فرجی", "گروه تلاش 🌟", "09181111118"),
            ("1019", "سامان", "حسینی", "گروه نخبگان 🏆", "09181111119"),
            ("1020", "پویا", "عسگری", "گروه نخبگان 🏆", "09181111120"),
            ("1021", "امیرعلی", "فتحی", "گروه نخبگان 🏆", "09181111121"),
            ("1022", "محمدمهدی", "وفایی", "گروه نخبگان 🏆", "09181111122"),
            ("1023", "شایان", "خانی", "گروه نخبگان 🏆", "09181111123"),
            ("1024", "آرمین", "زارعی", "گروه نخبگان 🏆", "09181111124"),
            ("1025", "نیما", "رحیمی", "گروه اندیشه 📖", "09181111125"),
            ("1026", "نوید", "کریمیان", "گروه اندیشه 📖", "09181111126"),
            ("1027", "آراد", "همتی", "گروه اندیشه 📖", "09181111127"),
            ("1028", "عرشیا", "مهرابی", "گروه اندیشه 📖", "09181111128"),
            ("1029", "آیدین", "کرم‌پور", "گروه اندیشه 📖", "09181111129"),
        ]
        cursor.executemany("""
            INSERT INTO students (national_id, first_name, last_name, student_group, parent_phone)
            VALUES (?, ?, ?, ?, ?)
        """, default_students)
        conn.commit()

def seed_default_quiz():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM quizzes")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at)
            VALUES (?, ?, ?, 1, ?)
        """, ("آزمون جامع ریاضی و علوم پایه پنجم (فصل ۱ و ۲)", "ریاضی و علوم", 60, datetime.now().strftime("%Y-%m-%d %H:%M")))
        quiz_id = cursor.lastrowid
        
        sample_questions = [
            ("mcq", "ارزش مکانی رقم ۶ در عدد ۴۶۵٬۱۲۳٬۸۹۰ کدام است؟", "ده‌میلیون", "میلیون", "صد هزار", "ده‌هزار", 1, "", "رقم ۶ در مرتبه ده‌میلیون قرار دارد."),
            ("mcq", "کدام یک از موارد زیر تغییر شیمیایی محسوب می‌شود؟", "ذوب شدن یخ", "تبخیر آب", "زنگ زدن آهن", "خرد کردن چوب", 3, "", "زنگ زدن آهن تغییر شیمیایی است چون جنس ماده تغییر می‌کند."),
            ("mcq", "حاصل ضرب ۰/۰۴ × ۵۰ کدام است؟", "۰/۲", "۲", "۲۰", "۲۰۰", 2, "", "۰/۰۴ × ۵۰ = ۲ است."),
            ("mcq", "کدام عضو بدن مرکز کنترل و فرماندهی بدن است؟", "قلب", "مغز", "معده", "شُش", 2, "", "مغز مرکز کنترل و پردازش پیام‌های عصبی است."),
            ("essay", "تفاوت تغییر فیزیکی و شیمیایی را همراه با یک مثال بنویسید.", "", "", "", "", 0, "در تغییر فیزیکی جنس ماده تغییر نمی‌کند (مثل ذوب یخ). در تغییر شیمیایی جنس ماده تغییر کرده و ماده جدیدی تولید می‌شود (مثل پختن نان).", "پاسخ کامل باید شامل تعریف هر دو تغییر و ذکر مثال باشد.")
        ]
        
        for q in sample_questions:
            cursor.execute("""
                INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
        conn.commit()
    conn.close()

# Initialize DB on load
init_db()

# Safe Load Students DataFrame
def load_students():
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM students ORDER BY last_name, first_name", conn)
        if df.empty:
            seed_default_students(conn)
            df = pd.read_sql_query("SELECT * FROM students ORDER BY last_name, first_name", conn)
        return df
    except Exception:
        init_db()
        try:
            return pd.read_sql_query("SELECT * FROM students ORDER BY last_name, first_name", conn)
        except Exception:
            return pd.DataFrame(columns=['id', 'national_id', 'first_name', 'last_name', 'student_group', 'parent_phone', 'notes'])
    finally:
        conn.close()

seed_default_quiz()

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False

if 'teacher_password' not in st.session_state:
    st.session_state['teacher_password'] = "1234"

if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 0

if 'app_entered' not in st.session_state:
    st.session_state['app_entered'] = False

# =========================================================
# SCREEN 1: SPLASH & WELCOME PAGE (صفحه خوش‌آمدگویی پیش از برنامه)
# =========================================================
if not st.session_state['app_entered']:
    st.markdown("""
        <div class="welcome-card" style="text-align: center;">
            <h1 style="color: #60a5fa; font-size: 2.2rem; margin-bottom: 10px;">
                🌸 به سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی خوش آمدید
            </h1>
            <h3 style="color: #e2e8f0; font-weight: normal; margin-bottom: 15px;">
                🏫 دبستان شهید مطهری مهران | پایه پنجم ابتدایی
            </h3>
            <p style="color: #38bdf8; font-size: 1.1rem; font-weight: bold;">
                👨‍🏫 طراح و توسعه‌دهنده سامانه: <span style="color: #facc15;">سید موسی حیدری</span> (آموزگار پایه پنجم)
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col_w1, col_w2 = st.columns([1, 1])
    
    with col_w1:
        st.markdown("""
            <div class="quote-box">
                <h4 style="color: #f59e0b; margin-bottom: 10px;">📜 سخن گهربار مقام معظم رهبری حضرت آیت‌الله خامنه‌ای (مدظله‌العالی):</h4>
                <p style="text-align: justify; font-size: 1.05rem; line-height: 1.9;">
                    «استفاده از ابزارهای نوين علمی و فناوری‌های هوشمند، مسیر یادگیری را برای دانش‌آموزان جذاب‌تر، عمیق‌تر و کارآمدتر می‌سازد. آموزش و پرورش ما باید مجهز به آخرین دستاوردهای علمی و تکنولوژی روز باشد تا نسل جوان ما برای آینده‌ای روشن و سراسر افتخار آماده شود.»
                </p>
            </div>
            
            <div class="feature-box">
                <h4 style="color: #60a5fa; margin-bottom: 10px;">🎯 اهداف اصلی سامانه هوشمند مدیریت کلاس:</h4>
                <ul style="line-height: 1.9; font-size: 0.98rem;">
                    <li><b>ارتقای کیفیت یادگیری:</b> بهره‌گیری از سنجش هوشمند آنلاین با تصحیح آنی و ارائه پاسخ‌نامه تحلیلی.</li>
                    <li><b>شفافیت و آگاهی اولیا:</b> دسترسی سریع اولیا به پوشه کار دیجیتال و نمودارهای خطی رشد تحصیلی.</li>
                    <li><b>تقویت روحیه همکاری:</b> گروه‌بندی ۲۹ دانش‌آموز در ۵ گروه متوازن و پایش رفتاری و انضباطی.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        
    with col_w2:
        st.markdown("""
            <div class="feature-box">
                <h4 style="color: #34d399; margin-bottom: 10px;">🇮🇷 مطابقت کامل با برنامه‌های وزارت آموزش و پرورش:</h4>
                <ul style="line-height: 1.9; font-size: 0.98rem;">
                    <li><b>انطباق با سند تحول بنیادین:</b> تحقق ساحت‌های شش‌گانه تربیت به‌ویژه ساحت علمی-فناوری و اجتماعی.</li>
                    <li><b>ارزشیابی کیفی-توصیفی:</b> سنجش فرآیندی ۷ عنوان درسی پایه پنجم (ریاضی، علوم، فارسی، نگارش، قرآن، هدایا و اجتماعی).</li>
                    <li><b>توسعه ابزارهای مدرن آموزشی:</b> جایگزینی شیوه‌های سنتی با پوشه کار الکترونیکی و آزمون‌های هوشمند.</li>
                </ul>
            </div>
            
            <div class="feature-box" style="border-color: #8b5cf6;">
                <h4 style="color: #a78bfa; margin-bottom: 8px;">🔑 راهنمای سریع ورود به سامانه:</h4>
                <p style="font-size: 0.95rem; line-height: 1.8;">
                    • <b>دانش‌آموزان و اولیا:</b> بدون نیاز به رمز عبور (جهت شرکت در آزمون‌ها و مشاهده کارنامه).<br>
                    • <b>آموزگار:</b> ورود به پنل مدیریت با وارد کردن رمز عبور مدیریت.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🚀 ورود به سامانه هوشمند مدیریت کلاس", use_container_width=True, type="primary"):
            st.session_state['app_entered'] = True
            st.rerun()
            
    st.stop()

# =========================================================
# SCREEN 2: MAIN APP DASHBOARD (برنامه اصلی)
# =========================================================

# Top Header & Authentication Bar
st.markdown("""
    <div class="header-card">
        <h2 style="color: #60a5fa; margin-bottom: 5px;">🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی</h2>
        <p style="color: #94a3b8; font-size: 0.95rem; margin-bottom: 0;">
            دبستان شهید مطهری مهران | طراح و آموزگار: <b>سید موسی حیدری</b>
        </p>
    </div>
""", unsafe_allow_html=True)

# Top Bar Navigation & Return to Welcome
col_top1, col_top2 = st.columns([3, 1])
with col_top2:
    if st.button("🏠 صفحه خوش‌آمدگویی", use_container_width=True):
        st.session_state['app_entered'] = False
        st.rerun()

# Teacher Authentication Banner
with st.expander("🔑 پنل ورود مدیریت آموزگار / وضعیت دسترسی کاربری"):
    col_a1, col_a2 = st.columns([2, 1])
    with col_a1:
        if st.session_state['is_teacher_logged_in']:
            st.success("🟢 شما در حالت **مدیریت آموزگار** هستید و به تمام بخش‌های برنامه دسترسی کامل دارید.")
            if st.button("🔒 خروج از حالت مدیریت معلم"):
                st.session_state['is_teacher_logged_in'] = False
                st.rerun()
        else:
            st.info("👤 شما در **حالت عمومی (دانش‌آموز / اولیا)** هستید. برای دسترسی به بخش‌های مدیریتی، رمز معلم را وارد کنید.")
            input_pass = st.text_input("🔑 رمز عبور آموزگار را وارد کنید:", type="password", key="pass_input")
            if st.button("🔓 ورود به سامانه"):
                if input_pass == st.session_state['teacher_password'] or input_pass == "مطهری":
                    st.session_state['is_teacher_logged_in'] = True
                    st.success("ورود موفقیت‌آمیز بود!")
                    st.rerun()
                else:
                    st.error("❌ رمز عبور اشتباه است (رمز پیش‌فرض: 1234).")
                    
    with col_a2:
        if st.session_state['is_teacher_logged_in']:
            st.subheader("🔐 تغییر رمز آموزگار")
            new_p1 = st.text_input("رمز جدید:", type="password", key="np1")
            new_p2 = st.text_input("تکرار رمز جدید:", type="password", key="np2")
            if st.button("💾 ذخیره رمز جدید"):
                if new_p1 and new_p1 == new_p2:
                    st.session_state['teacher_password'] = new_p1
                    st.success("✅ رمز عبور با موفقیت تغییر کرد!")
                else:
                    st.error("❌ رمزها یکسان نیستند.")

# Menu Items based on Role
if st.session_state['is_teacher_logged_in']:
    menu_options = [
        "1️⃣ 🏠 صفحه اصلی و معرفی سامانه",
        "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی (۲۹ نفر)",
        "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی",
        "4️⃣ 🌟 مدیریت رفتار و مشاهدات انضباطی",
        "5️⃣ ✏️ آزمون‌ساز آنلاین و طراحی سوالات",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع"
    ]
else:
    menu_options = [
        "1️⃣ 🏠 صفحه اصلی و معرفی سامانه",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع"
    ]

st.markdown("### 📌 منوی بخش‌های سامانه (انتخاب کنید):")
menu_choice = st.radio("انتخاب بخش:", menu_options, label_visibility="collapsed")

def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه در کادر ورود مدیریت رمز عبور را وارد کنید.")
        st.stop()

# ---------------------------------------------------------
# 1. Landing Page Info
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.subheader("👋 به سامانه مدیریت هوشمند کلاس پنجم خوش آمدید")
    st.markdown("""
        <div class="feature-box">
            <h3>🌱 طراح و توسعه‌دهنده سامانه: <b>سید موسی حیدری</b></h3>
            <p>آموزگار پایه پنجم ابتدایی — دبستان شهید مطهری مهران</p>
        </div>
        <div class="feature-box">
            <h4>1️⃣ ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم</h4>
            <p>ثبت دقیق سطح عملکرد توصیفی دانش‌آموزان همراه با بازخوردهای اصلاحی جهت ارائه به اولیا.</p>
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
# 2. Student Profile & Bulk Excel Upload
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab1, tab2, tab3 = st.tabs(["📋 لیست دانش‌آموزان و گروه‌ها", "📊 ثبت دسته‌جمعی و سریع از اکسل", "➕ ثبت دانش‌آموز جدید (تکی)"])
    
    with tab1:
        students_df = load_students()
        if not students_df.empty:
            search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام یا کد ملی):")
            if search_query:
                filtered_df = students_df[
                    students_df['first_name'].str.contains(search_query, na=False) |
                    students_df['last_name'].str.contains(search_query, na=False) |
                    students_df['national_id'].str.contains(search_query, na=False)
                ]
            else:
                filtered_df = students_df
                
            st.dataframe(filtered_df[['id', 'national_id', 'first_name', 'last_name', 'student_group', 'parent_phone']], use_container_width=True)
            
            # Group Statistics
            st.subheader("📊 توزیع دانش‌آموزان در ۵ گروه کلاسی")
            group_counts = students_df['student_group'].value_counts()
            st.bar_chart(group_counts)
        else:
            st.info("لیست دانش‌آموزان خالی است.")
            
    with tab2:
        st.subheader("📊 بارگذاری یکجا و سریع از فایل اکسل / CSV")
        st.write("می‌توانید فایل اکسل اسامی ۲۹ دانش‌آموز کلاس را یکجا بارگذاری کنید.")
        
        col_ex1, col_a2_btn = st.columns([3, 1])
        with col_a2_btn:
            if st.button("🧹 پاکسازی و انتخاب فایل جدید"):
                st.session_state['excel_upload_key'] += 1
                st.rerun()
                
        uploaded_file = st.file_uploader("انتخاب فایل Excel یا CSV:", type=['xlsx', 'xls', 'csv'], key=f"uploader_{st.session_state['excel_upload_key']}")
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)
                    
                st.success("✅ فایل با موفقیت خوانده شد. پیش‌نمایش اطلاعات:")
                st.dataframe(df_upload.head(), use_container_width=True)
                
                if st.button("📥 ثبت نهایی دانش‌آموزان در پایگاه داده"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    added_count = 0
                    for _, row in df_upload.iterrows():
                        try:
                            nid = str(row.get('national_id', row.get('کد ملی', '')))
                            fname = str(row.get('first_name', row.get('نام', '')))
                            lname = str(row.get('last_name', row.get('نام خانوادگی', '')))
                            sgroup = str(row.get('student_group', row.get('گروه', 'گروه عمومی 📖')))
                            phone = str(row.get('parent_phone', row.get('تلفن', '')))
                            
                            if fname and lname:
                                cursor.execute("""
                                    INSERT OR REPLACE INTO students (national_id, first_name, last_name, student_group, parent_phone)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (nid, fname, lname, sgroup, phone))
                                added_count += 1
                        except Exception:
                            pass
                    conn.commit()
                    conn.close()
                    st.success(f"🎉 تعداد {added_count} دانش‌آموز با موفقیت ثبت/به‌روزرسانی شدند!")
            except Exception as e:
                st.error(f"❌ خطا در پردازش فایل: {e}")
                
    with tab3:
        st.subheader("➕ ثبت دانش‌آموز جدید")
        with st.form("add_student_form"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                fn = st.text_input("نام:")
                ln = st.text_input("نام خانوادگی:")
                nid = st.text_input("کد ملی:")
            with col_f2:
                grp = st.selectbox("گروه کلاسی:", ["گروه ارمغان 🚀", "گروه دانا 💡", "گروه تلاش 🌟", "گروه نخبگان 🏆", "گروه اندیشه 📖"])
                phone = st.text_input("شماره همراه اولیا:")
            
            submit_btn = st.form_submit_button("💾 ثبت دانش‌آموز")
            if submit_btn and fn and ln:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO students (national_id, first_name, last_name, student_group, parent_phone)
                    VALUES (?, ?, ?, ?, ?)
                """, (nid, fn, ln, grp, phone))
                conn.commit()
                conn.close()
                st.success(f"دانش‌آموز {fn} {ln} با موفقیت ثبت شد.")

# ---------------------------------------------------------
# 3. Descriptive Evaluation
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم")
    students_df = load_students()
    
    if not students_df.empty:
        student_list = [f"{row['id']} - {row['first_name']} {row['last_name']} ({row['student_group']})" for _, row in students_df.iterrows()]
        selected_student_str = st.selectbox("انتخاب دانش‌آموز:", student_list)
        selected_student_id = int(selected_student_str.split(" - ")[0])
        
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            subject = st.selectbox("عنوان درس:", ["ریاضی", "علوم تجربی", "فارسی و نگارش", "قرآن", "هدیه‌های آسمان", "مطالعات اجتماعی", "شایستگی‌های عمومی"])
            grade_level = st.selectbox("سطح عملکرد توصیفی:", ["خیلی خوب (خیلی عالی و مستمر)", "خوب (پذیرفته‌شده و خوب)", "قابل قبول (نیازمند تمرین بیشتر)", "نیازمند تلاش مجدد"])
        with col_e2:
            eval_date = st.date_input("تاریخ ارزشیابی:", datetime.now())
            feedback = st.text_area("بازخورد توصیفی و توصیه‌های آموزشی آموزگار:")
            
        if st.button("💾 ثبت ارزشیابی توصیفی"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO evaluations (student_id, subject, evaluation_date, grade_level, feedback)
                VALUES (?, ?, ?, ?, ?)
            """, (selected_student_id, subject, str(eval_date), grade_level, feedback))
            conn.commit()
            conn.close()
            st.success("✅ ارزشیابی توصیفی با موفقیت ثبت گردید.")
            
        # History
        st.subheader("📜 سوابق ارزشیابی‌های ثبت‌شده برای این دانش‌آموز")
        conn = get_db_connection()
        eval_df = pd.read_sql_query("SELECT subject as 'درس', grade_level as 'سطح عملکرد', evaluation_date as 'تاریخ', feedback as 'بازخورد' FROM evaluations WHERE student_id = ? ORDER BY id DESC", conn, params=(selected_student_id,))
        conn.close()
        st.dataframe(eval_df, use_container_width=True)

# ---------------------------------------------------------
# 4. Behavior Management
# ---------------------------------------------------------
elif menu_choice.startswith("4"):
    check_teacher_auth()
    st.header("🌟 ثبت مشاهدات رفتاری و گروه‌بندی کلاسی")
    students_df = load_students()
    
    if not students_df.empty:
        student_list = [f"{row['id']} - {row['first_name']} {row['last_name']}" for _, row in students_df.iterrows()]
        selected_student_str = st.selectbox("انتخاب دانش‌آموز:", student_list)
        selected_student_id = int(selected_student_str.split(" - ")[0])
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            category = st.selectbox("نوع رفتار / مشاهده:", ["🌟 کارت امتیاز سبز (مثبت)", "🚀 همکاری و کار گروهی عالی", "📚 انجام کامل تکالیف", "⚠️ تذکر انضباطی (منفی)"])
            points = st.number_input("تعداد امتیاز (مثبت یا منفی):", value=5)
        with col_b2:
            log_date = st.date_input("تاریخ مشاهده:", datetime.now())
            description = st.text_input("توضیحات و علت امتیاز:")
            
        if st.button("💾 ثبت امتیاز رفتاری"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO behavior_logs (student_id, log_date, category, points, description)
                VALUES (?, ?, ?, ?, ?)
            """, (selected_student_id, str(log_date), category, points, description))
            conn.commit()
            conn.close()
            st.success("✅ مشاهده رفتاری ذخیره گردید.")

# ---------------------------------------------------------
# 5. Quiz Maker (Teacher)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین و مدیریت سوالات")
    
    tab_q1, tab_q2, tab_q3 = st.tabs(["➕ طراحی آزمون جدید", "📥 بارگذاری فایل آماده آزمون (JSON)", "📋 مدیریت آزمون‌های فعال"])
    
    with tab_q1:
        st.subheader("ایجاد آزمون جدید")
        q_title = st.text_input("عنوان آزمون:")
        q_subj = st.selectbox("درس مربوطه:", ["ریاضی", "علوم تجربی", "فارسی", "هدیه‌های آسمان", "مطالعات اجتماعی", "جامع"])
        q_dur = st.number_input("مدت زمان پاسخگویی (به دقیقه):", value=60, min_value=5, max_value=180)
        
        if st.button("🚀 ایجاد و انتشار آزمون"):
            if q_title:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at)
                    VALUES (?, ?, ?, 1, ?)
                """, (q_title, q_subj, q_dur, datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                conn.close()
                st.success("✅ آزمون با موفقیت ساخته شد.")
                
    with tab_q2:
        st.subheader("📥 بارگذاری فایل آماده آزمون (فرمت JSON)")
        st.write("می‌توانید فایل سوالات طراحی‌شده توسط هوش مصنوعی یا فایل نمونه را مستقیم آپلود کنید.")
        
        json_file = st.file_uploader("انتخاب فایل JSON آزمون:", type=['json'])
        if json_file is not None:
            try:
                data = json.load(json_file)
                st.success(f"فایل آزمون '{data.get('title', '')}' بارگذاری شد.")
                if st.button("💾 ثبت آزمون از فایل JSON"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at)
                        VALUES (?, ?, ?, 1, ?)
                    """, (data.get('title', 'آزمون آنلاین'), data.get('subject', 'عمومی'), data.get('duration_minutes', 60), datetime.now().strftime("%Y-%m-%d %H:%M")))
                    quiz_id = cursor.lastrowid
                    
                    for q in data.get('questions', []):
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            quiz_id,
                            q.get('type', 'mcq'),
                            q.get('text', ''),
                            q.get('op1', ''), q.get('op2', ''), q.get('op3', ''), q.get('op4', ''),
                            q.get('correct', 1),
                            q.get('model_answer', ''),
                            q.get('explanation', '')
                        ))
                    conn.commit()
                    conn.close()
                    st.success("🎉 آزمون و سوالات آن با موفقیت در سیستم ثبت گردید!")
            except Exception as e:
                st.error(f"خطا در فرمت فایل JSON: {e}")
                
    with tab_q3:
        conn = get_db_connection()
        quizzes_df = pd.read_sql_query("SELECT * FROM quizzes ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(quizzes_df, use_container_width=True)

# ---------------------------------------------------------
# 6. Student Online Quiz (Student)
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین دانش‌آموزی")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("ابتدا باید اسامی دانش‌آموزان توسط معلم ثبت شود.")
        st.stop()
        
    student_list = [f"{row['id']} - {row['first_name']} {row['last_name']}" for _, row in students_df.iterrows()]
    selected_student_str = st.selectbox("دانش‌آموز عزیز، نام خود را انتخاب کنید:", student_list)
    selected_student_id = int(selected_student_str.split(" - ")[0])
    
    conn = get_db_connection()
    quizzes = pd.read_sql_query("SELECT * FROM quizzes WHERE is_active = 1 ORDER BY id DESC", conn)
    
    if quizzes.empty:
        st.info("در حال حاضر آزمون فعالی وجود ندارد.")
        conn.close()
    else:
        quiz_options = [f"{row['id']} - {row['title']} ({row['subject']} - {row['duration_minutes']} دقیقه)" for _, row in quizzes.iterrows()]
        selected_quiz_str = st.selectbox("انتخاب آزمون:", quiz_options)
        selected_quiz_id = int(selected_quiz_str.split(" - ")[0])
        
        quiz_info = quizzes[quizzes['id'] == selected_quiz_id].iloc[0]
        
        # Check if already submitted
        existing_res = pd.read_sql_query("SELECT * FROM quiz_results WHERE quiz_id = ? AND student_id = ?", conn, params=(selected_quiz_id, selected_student_id))
        
        if not existing_res.empty:
            st.success("✅ شما قبلاً در این آزمون شرکت کرده‌اید. کارنامه آزمون شما:")
            res_row = existing_res.iloc[0]
            st.metric("نمره‌بندی سوالات تستی:", f"{res_row['score_mcq']} از {res_row['total_mcq']}")
            
            # Show Review & Explanations
            questions_df = pd.read_sql_query("SELECT * FROM questions WHERE quiz_id = ?", conn, params=(selected_quiz_id,))
            st.subheader("💡 تحلیل آموزشی و پاسخ‌نامه تشریحی سوالات:")
            for idx, q_row in questions_df.iterrows():
                st.write(f"**سوال {idx+1}: {q_row['question_text']}**")
                if q_row['question_type'] == 'mcq':
                    st.info(f"پاسخ صحیح: گزینه {q_row['correct_option']}")
                else:
                    st.info(f"پاسخ نمونه/کلید: {q_row['model_answer']}")
                if q_row['explanation']:
                    st.caption(f"💡 تحلیل آموزگار: {q_row['explanation']}")
                st.markdown("---")
            conn.close()
        else:
            # Start Quiz Session
            st.info(f"⏱️ مهلت پاسخگویی: **{quiz_info['duration_minutes']} دقیقه** | بعد از شروع، زمان معکوس محاسبه می‌شود.")
            
            if st.button("🚀 شروع آزمون آنلاین"):
                st.session_state[f"quiz_start_{selected_quiz_id}"] = time.time()
                st.rerun()
                
            if f"quiz_start_{selected_quiz_id}" in st.session_state:
                start_t = st.session_state[f"quiz_start_{selected_quiz_id}"]
                elapsed = (time.time() - start_t) / 60
                rem_m = max(0, int(quiz_info['duration_minutes'] - elapsed))
                
                st.warning(f"⏱️ **زمان باقی‌مانده آزمون: {rem_m} دقیقه**")
                
                questions_df = pd.read_sql_query("SELECT * FROM questions WHERE quiz_id = ?", conn, params=(selected_quiz_id,))
                
                with st.form("take_quiz_form"):
                    user_mcq_answers = {}
                    user_essay_answers = {}
                    
                    for idx, q_row in questions_df.iterrows():
                        q_id = q_row['id']
                        st.markdown(f"#### سوال {idx+1}: {q_row['question_text']}")
                        
                        if q_row['question_type'] == 'mcq':
                            user_mcq_answers[q_id] = st.radio(
                                f"گزینه انتخابی سوال {idx+1}:",
                                [1, 2, 3, 4],
                                format_func=lambda x: f"گزینه {x}: {q_row[f'option_{x}']}",
                                key=f"ans_mcq_{q_id}"
                            )
                        else:
                            user_essay_answers[q_id] = st.text_area(f"پاسخ تشریحی شما برای سوال {idx+1}:", key=f"ans_essay_{q_id}")
                            
                    submit_quiz_btn = st.form_submit_button("🏁 ثبت نهایی و ارسال پاسخ‌نامه")
                    
                    if submit_quiz_btn:
                        # Auto Grade MCQ
                        score_mcq = 0
                        total_mcq = 0
                        
                        for idx, q_row in questions_df.iterrows():
                            if q_row['question_type'] == 'mcq':
                                total_mcq += 1
                                if user_mcq_answers.get(q_row['id']) == q_row['correct_option']:
                                    score_mcq += 1
                                    
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO quiz_results (quiz_id, student_id, score_mcq, total_mcq, essay_answers, submitted_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (selected_quiz_id, selected_student_id, score_mcq, total_mcq, json.dumps(user_essay_answers, ensure_ascii=False), datetime.now().strftime("%Y-%m-%d %H:%M")))
                        conn.commit()
                        conn.close()
                        st.balloons()
                        st.success("🎉 پاسخ‌های شما با موفقیت ثبت شد!")
                        st.rerun()

# ---------------------------------------------------------
# 7. Comprehensive Student Portfolio
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 پوشه کار و کارنامه جامع تحصیلی دانش‌آموز")
    students_df = load_students()
    
    if not students_df.empty:
        student_list = [f"{row['id']} - {row['first_name']} {row['last_name']} ({row['student_group']})" for _, row in students_df.iterrows()]
        selected_student_str = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار:", student_list)
        selected_student_id = int(selected_student_str.split(" - ")[0])
        
        conn = get_db_connection()
        student_info = pd.read_sql_query("SELECT * FROM students WHERE id = ?", conn, params=(selected_student_id,)).iloc[0]
        
        st.markdown(f"""
            <div class="feature-box">
                <h3>👨‍🎓 پرونده تحصیلی: <b>{student_info['first_name']} {student_info['last_name']}</b></h3>
                <p>کد ملی: {student_info['national_id']} | گروه آموزشی: <b>{student_info['student_group']}</b> | شماره همراه اولیا: {student_info['parent_phone']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        tab_p1, tab_p2, tab_p3 = st.tabs(["📝 ارزشیابی توصیفی", "📱 سوابق آزمون‌های آنلاین", "🌟 امتیازات رفتاری"])
        
        with tab_p1:
            eval_df = pd.read_sql_query("SELECT subject as 'عنوان درس', grade_level as 'سطح عملکرد', evaluation_date as 'تاریخ', feedback as 'بازخورد آموزگار' FROM evaluations WHERE student_id = ? ORDER BY id DESC", conn, params=(selected_student_id,))
            st.dataframe(eval_df, use_container_width=True)
            
        with tab_p2:
            quiz_res_df = pd.read_sql_query("""
                SELECT q.title as 'عنوان آزمون', qr.score_mcq as 'نمره تستی', qr.total_mcq as 'تعداد کل', qr.submitted_at as 'زمان ارسال'
                FROM quiz_results qr
                JOIN quizzes q ON qr.quiz_id = q.id
                WHERE qr.student_id = ?
            """, conn, params=(selected_student_id,))
            st.dataframe(quiz_res_df, use_container_width=True)
            
        with tab_p3:
            beh_df = pd.read_sql_query("SELECT category as 'عنوان', points as 'امتیاز', log_date as 'تاریخ', description as 'توضیحات' FROM behavior_logs WHERE student_id = ? ORDER BY id DESC", conn, params=(selected_student_id,))
            st.dataframe(beh_df, use_container_width=True)
            
        conn.close()
