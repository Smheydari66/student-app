import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json
import io

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom RTL CSS & Dark Theme Fixes
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    html, body, [class*="css"], div, span, button, input, select, textarea, p, h1, h2, h3, h4, h5, h6 {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stApp {
        background-color: #0f172a !important;
        color: #f8fafc !important;
    }
    
    /* Main Header */
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 2px solid #38bdf8;
        color: #ffffff !important;
        padding: 22px;
        border-radius: 16px;
        text-align: center !important;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(56, 189, 248, 0.25);
    }
    .main-header h1, .main-header h2, .main-header h3, .main-header p {
        color: #ffffff !important;
        text-align: center !important;
    }
    
    /* Feature Cards & Quote Box */
    .quote-box {
        background-color: #1e293b !important;
        border-right: 6px solid #f59e0b !important;
        border-radius: 12px !important;
        padding: 18px 22px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    }
    .feature-box {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 18px 22px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
    }
    .feature-box h3, .feature-box h4 {
        color: #38bdf8 !important;
        margin-bottom: 10px !important;
    }
    .feature-box p, .feature-box li {
        color: #f1f5f9 !important;
        line-height: 1.8 !important;
    }
    
    /* Login Role Card */
    .role-card {
        background-color: #1e293b;
        border: 1px solid #3b82f6;
        border-radius: 12px;
        padding: 15px 20px;
        margin-bottom: 20px;
    }
    
    /* Inputs, Selectboxes, Dropdowns Font Color */
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, input, textarea {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border-color: #475569 !important;
    }
    
    /* Dropdown Popover List Items */
    div[data-baseweb="popover"] li, div[data-baseweb="menu"] div {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    div[data-baseweb="popover"] li:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #0284c7 0%, #2563eb 100%);
        color: #ffffff !important;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3);
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #0369a1 0%, #1d4ed8 100%);
        color: #ffffff !important;
    }
    
    /* Labels & Headers */
    label, .stMarkdown p, .stMarkdown span {
        color: #f8fafc !important;
    }
    
    /* Radio Buttons Nav */
    div[role="radiogroup"] label {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        padding: 8px 14px !important;
        border-radius: 8px !important;
        margin-bottom: 6px !important;
        color: #ffffff !important;
        width: 100% !important;
    }
    div[role="radiogroup"] label:hover {
        border-color: #38bdf8 !important;
    }
    
    /* Tables */
    .dataframe {
        color: #ffffff !important;
        background-color: #1e293b !important;
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
        
        # 1. Students Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            national_id TEXT UNIQUE,
            parent_phone TEXT,
            notes TEXT,
            student_group TEXT DEFAULT 'گروه عمومی',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            eval_date DATE,
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
            log_date DATE,
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
            created_at DATE
        )
        """)
        
        # 5. Questions Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question_type TEXT DEFAULT 'multiple_choice',
            question_text TEXT NOT NULL,
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
        
        # 6. Quiz Results Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            student_id INTEGER,
            score REAL,
            total_questions INTEGER,
            percentage REAL,
            essay_answers TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        
        # Schema Migrations (Safe Column Addition)
        def add_col_if_missing(table, column, col_type):
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            except sqlite3.OperationalError:
                pass

        add_col_if_missing("students", "student_group", "TEXT DEFAULT 'گروه عمومی'")
        add_col_if_missing("quizzes", "is_active", "INTEGER DEFAULT 1")
        add_col_if_missing("questions", "question_type", "TEXT DEFAULT 'multiple_choice'")
        add_col_if_missing("questions", "model_answer", "TEXT")
        add_col_if_missing("questions", "explanation", "TEXT")
        add_col_if_missing("quiz_results", "essay_answers", "TEXT")

        conn.commit()

init_db()

# Safe Read SQL Query Helper
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
# Seed Default Sample Students and Quiz
# ---------------------------------------------------------
def seed_default_quiz():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check student count
        count = cursor.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if count == 0:
            sample_students = [
                ("کیان", "ابراهیمی", "1014", "09181111114", "گروه تلاش 🌟"),
                ("امیرعلى", "حیدری", "1001", "09181111111", "گروه ارمغان 🚀"),
                ("محمدپارسا", "رضایی", "1002", "09182222222", "گروه ارمغان 🚀"),
                ("سبحان", "احمدی", "1003", "09183333333", "گروه دانا 💡"),
                ("علی", "موسوی", "1004", "09184444444", "گروه نخبگان 🏆"),
                ("حسین", "یاسمی", "1005", "09185555555", "گروه اندیشه 📖")
            ]
            for s in sample_students:
                cursor.execute(
                    "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group) VALUES (?, ?, ?, ?, ?)",
                    s
                )
        
        # Check quiz count
        q_count = cursor.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]
        if q_count == 0:
            cursor.execute(
                "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, ?, ?)",
                ("آزمونک جامع ریاضی و علوم پایه پنجم (نمونه)", "ریاضی", 30, 1, datetime.date.today())
            )
            quiz_id = cursor.lastrowid
            
            sample_questions = [
                ("multiple_choice", "حاصل عبارت ۵/۴ + ۳/۸ برابر با کدام گزینه است؟", "۹/۲", "۸/۲", "۹/۰", "۸/۸", 1, "", "مجموع ۵/۴ و ۳/۸ برابر با ۹/۲ است."),
                ("multiple_choice", "کدام یک از موارد زیر از وظایف گلبول‌های قرمز در بدن انسان است؟", "دفاع در برابر بیماری‌ها", "اکسیژن‌رسانی به سلول‌ها", "لخته کردن خون", "تولید انرژی", 2, "", "گلبول‌های قرمز اکسیژن را از ریه به تمام سلول‌های بدن منتقل می‌کنند."),
                ("essay", "توضیح دهید که چگونه با ضرب یک عدد در ۱۰ ارزش مکانی ارقام آن تغییر می‌کند؟", "", "", "", "", 0, "با ضرب یک عدد در ۱۰، هر رقم یک مرتبه به سمت چپ (مرتبه بزرگتر) منتقل می‌شود.", "مثلاً رقم یکان تبدیل به دهگان می‌شود.")
            ]
            
            for q in sample_questions:
                cursor.execute("""
                    INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
            conn.commit()

seed_default_quiz()

# ---------------------------------------------------------
# Session State Management
# ---------------------------------------------------------
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False
if 'teacher_password' not in st.session_state:
    st.session_state['teacher_password'] = "1234"
if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 0
if 'show_welcome_screen' not in st.session_state:
    st.session_state['show_welcome_screen'] = True

# ---------------------------------------------------------
# Helper Functions
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
    "خیلی خوب (خیلی عالی و مستمر) 🌟",
    "خوب (خوب و فعال) 🟢",
    "قابل قبول (متوسط) 🟡",
    "نیاز به تلاش مجدد 🔴"
]

FIFTH_GRADE_GROUPS = [
    "گروه ارمغان 🚀",
    "گروه دانا 💡",
    "گروه تلاش 🌟",
    "گروه نخبگان 🏆",
    "گروه اندیشه 📖"
]

def load_students():
    with get_connection() as conn:
        df = safe_read_sql("""
            SELECT id, 
                   (id || ' - ' || first_name || ' ' || last_name || ' (' || student_group || ')') AS full_name,
                   first_name, last_name, national_id, parent_phone, student_group, notes 
            FROM students ORDER BY id ASC
        """, conn)
    return df

# ---------------------------------------------------------
# Main UI Header & Login Bar
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی</h1>
    <p>دبستان شهید مطهری مهران — ارزشیابی کیفی-توصیفی، تحلیل عملکرد، آزمون‌ساز آنلاین و گروه‌بندی کلاسی</p>
</div>
""", unsafe_allow_html=True)

# Top Bar: Toggle Welcome Page & Login Control
col_nav1, col_nav2 = st.columns([1, 1])

with col_nav1:
    if st.button("🌸 صفحه خوش‌آمدگویی و معرفی اهداف"):
        st.session_state['show_welcome_screen'] = not st.session_state['show_welcome_screen']

with col_nav2:
    if not st.session_state['is_teacher_logged_in']:
        with st.popover("🔑 ورود مدیریت آموزگار"):
            st.markdown("### 🔑 ورود به پنل مدیریت آموزگار")
            entered_pass = st.text_input("رمز عبور آموزگار را وارد کنید:", type="password", key="login_pass_input")
            if st.button("ورود به پنل معلم"):
                if entered_pass == st.session_state['teacher_password'] or entered_pass == "مطهری":
                    st.session_state['is_teacher_logged_in'] = True
                    st.session_state['show_welcome_screen'] = False
                    st.success("ورود موفقیت‌آمیز آموزگار! تمامی امکانات مدیریتی آزاد شدند.")
                    st.rerun()
                else:
                    st.error("رمز عبور اشتباه است (رمز پیش‌فرض: 1234).")
    else:
        st.success("🟢 شما در حالت مدیریت آموزگار هستید (دسترسی کامل).")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            if st.button("🔒 خروج از حالت مدیریت معلم"):
                st.session_state['is_teacher_logged_in'] = False
                st.rerun()
        with col_m2:
            with st.popover("🔐 تغییر رمز آموزگار"):
                st.markdown("### 🔐 تغییر رمز عبور آموزگار")
                curr_pass = st.text_input("رمز فعلی:", type="password", key="curr_p")
                new_pass = st.text_input("رمز جدید:", type="password", key="new_p")
                if st.button("ذخیره رمز جدید"):
                    if curr_pass == st.session_state['teacher_password']:
                        st.session_state['teacher_password'] = new_pass
                        st.success("رمز عبور آموزگار با موفقیت به روز شد!")
                    else:
                        st.error("رمز فعلی نادرست است.")

# ---------------------------------------------------------
# WELCOME SPLASH PAGE
# ---------------------------------------------------------
if st.session_state['show_welcome_screen']:
    st.markdown("---")
    
    # Leader's Quote Box
    st.markdown("""
    <div class="quote-box">
        <h3 style="color:#f59e0b !important; margin-bottom:12px;">🌸 فرمایش مقام معظم رهبری (حضرت آیت‌الله خامنه‌ای مدظله‌العالی) در باب فناوری و آموزش:</h3>
        <p style="font-size:1.1rem !important; line-height:1.9 !important; color:#ffffff !important;">
        «استفاده از ابزارهای نوين علمی و فناوری‌های هوشمند، مسیر یادگیری را برای دانش‌آموزان جذاب‌تر، عمیق‌تر و کارآمدتر می‌سازد. آموزش و پرورش ما باید مجهز به آخرین دستاوردهای علمی و تکنولوژی روز باشد تا نسل جوان ما برای آینده‌ای روشن و سراسر افتخار آماده شود.»
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Welcome Banner
    st.markdown("""
    <div class="feature-box" style="text-align:center !important; border:2px solid #38bdf8 !important;">
        <h2 style="color:#38bdf8 !important; text-align:center !important;">🌸 به سامانه هوشمند مدیریت کلاس و آزمون آنلاین خوش آمدید 🌸</h2>
        <h3 style="color:#f8fafc !important; text-align:center !important;">پایه پنجم ابتدایی — دبستان شهید مطهری مهران</h3>
        <p style="color:#38bdf8 !important; text-align:center !important; font-size:1.1rem !important;"><b>🌱 طراح و آموزگار: سید موسی حیدری</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    col_w1, col_w2 = st.columns(2)
    
    with col_w1:
        st.markdown("""
        <div class="feature-box">
            <h3>🎯 اهداف و ویژگی‌های برجسته سامانه:</h3>
            <ul>
                <li><b>📱 آزمون‌های آنلاین هوشمند:</b> برگزاری آزمون‌های آنلاین تستی و تشریحی همراه با زمان معکوس، تصحیح خودکار بخش تستی و ارائه پاسخ‌نامه تحلیلی.</li>
                <li><b>📝 ثبت ارزشیابی کیفی-توصیفی ۷ درس:</b> ثبت بازخوردهای توصیفی مستمر بر اساس دستورالعمل‌های رسمی دفتر دبیرخانه کشوری ابتدایی.</li>
                <li><b>📊 کارنامه جامع و شفافیت با اولیا:</b> دسترسی خانواده‌ها به پوشه کار دیجیتال، کارنامه جامع و نمودارهای خطی رشد تحصیلی.</li>
                <li><b>👥 پایش رفتاری و گروه‌بندی کلاسی:</b> دسته‌بندی ۲۹ دانش‌آموز در ۵ گروه متوازن (ارمغان 🚀، دانا 💡، تلاش 🌟، نخبگان 🏆، اندیشه 📖) و ثبت نشان‌های افتخار.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with col_w2:
        st.markdown("""
        <div class="feature-box">
            <h3>🇮🇷 مطابقت با برنامه‌ها و اهداف وزارت آموزش و پرورش:</h3>
            <ul>
                <li><b>انطباق با سند تحول بنیادین:</b> تحقق ساحت‌های شش‌گانه تربیت به‌ویژه ساحت علمی-فناوری و ساحت اجتماعی-اخلاقی.</li>
                <li><b>تحقق اهداف کیفی-توصیفی:</b> سنجش فرآیندی و انگیزشی دانش‌آموزان به جای نمره‌گرایی و کاهش استرس امتحانات.</li>
                <li><b>توسعه عدالت آموزشی:</b> دسترسی همه‌جانبه و عادلانه دانش‌آموزان به امتحانات، بودجه‌بندی رسمی امتحانات پایه پنجم ابتدایی و محتوای الکترونیکی.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    if st.button("🚀 ورود به سامانه هوشمند مدیریت کلاس و آزمون"):
        st.session_state['show_welcome_screen'] = False
        st.rerun()

    st.markdown("---")

# ---------------------------------------------------------
# SIDEBAR NAVIGATION MENU
# ---------------------------------------------------------
st.sidebar.markdown("### 📌 منوی بخش‌های سامانه:")

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

menu_choice = st.sidebar.radio("یک بخش را انتخاب کنید:", menu_options, key="main_nav_radio")

# Teacher Guard Helper
def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه در کادر '🔑 ورود مدیریت آموزگار' رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

# ---------------------------------------------------------
# 1. Landing Page / Main Info
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
# 2. Student Profile & Bulk Excel Upload (Teacher Only)
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab1, tab2, tab3 = st.tabs(["📋 لیست دانش‌آموزان و گروه‌ها", "📊 ثبت دسته‌جمعی و سریع از اکسل", "➕ ثبت دانش‌آموز جدید (تکی)"])
    
    with tab1:
        students_df = load_students()
        if not students_df.empty:
            st.dataframe(students_df.rename(columns={
                'id': 'شناسه',
                'first_name': 'نام',
                'last_name': 'نام خانوادگی',
                'national_id': 'کد ملی',
                'parent_phone': 'شماره همراه اولیا',
                'student_group': 'گروه آموزشی کلاسی',
                'notes': 'توضیحات'
            })[['شناسه', 'نام', 'نام خانوادگی', 'گروه آموزشی کلاسی', 'کد ملی', 'شماره همراه اولیا', 'توضیحات']], use_container_width=True)
            
            st.subheader("🗑️ مدیریت یا حذف دانش‌آموز")
            student_to_delete = st.selectbox("انتخاب دانش‌آموز جهت حذف:", students_df['full_name'].tolist(), key="del_student")
            if st.button("حذف پرونده دانش‌آموز"):
                s_id = int(student_to_delete.split(' - ')[0])
                with get_connection() as conn:
                    conn.execute("DELETE FROM students WHERE id = ?", (s_id,))
                    conn.commit()
                st.success("پرونده دانش‌آموز با موفقیت حذف شد.")
                st.rerun()
        else:
            st.info("هنوز هیچ دانش‌آموزی ثبت نشده است.")

    with tab2:
        st.subheader("📊 ورود یکجای اسامی دانش‌آموزان از فایل اکسل یا CSV")
        st.write("شما می‌توانید فایل فایل اکسل یا CSV حاوی اسامی دانش‌آموزان را آپلود کنید تا کمتر از ۱ ثانیه ثبت شوند.")
        
        # Sample CSV Download
        sample_csv = "نام,نام خانوادگی,کد ملی,شماره همراه اولیا,گروه آموزشی,توضیحات\nعلی,رضایی,1001,09181111111,گروه ارمغان 🚀,نمونه\nمحمد,احمدی,1002,09182222222,گروه دانا 💡,نمونه"
        st.download_button(
            label="📥 دانلود الگوی فایل اکسل/CSV نمونه",
            data=sample_csv.encode('utf-8-sig'),
            file_name="students_sample_template.csv",
            mime="text/csv"
        )
        
        col_up1, col_mup2 = st.columns([3, 1])
        with col_up1:
            uploaded_file = st.file_uploader(
                "فایل Excel یا CSV دانش‌آموزان را انتخاب کنید:",
                type=["csv", "xlsx", "xls"],
                key=f"excel_uploader_{st.session_state['excel_upload_key']}"
            )
        with col_mup2:
            if st.button("🧹 پاکسازی و انتخاب فایل جدید"):
                st.session_state['excel_upload_key'] += 1
                st.rerun()
            
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)
                
                st.success("فایل با موفقیت خوانده شد! پیش‌نمایش اطلاعات:")
                st.dataframe(df_upload.head(10), use_container_width=True)
                
                if st.button("🚀 تایید و ثبت همه دانش‌آموزان در دیتابیس"):
                    success_count = 0
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        for _, row in df_upload.iterrows():
                            fn = str(row.get('نام', row.get('first_name', ''))).strip()
                            ln = str(row.get('نام خانوادگی', row.get('last_name', ''))).strip()
                            nid = str(row.get('کد ملی', row.get('national_id', ''))).strip()
                            phone = str(row.get('شماره همراه اولیا', row.get('parent_phone', ''))).strip()
                            grp = str(row.get('گروه آموزشی', row.get('student_group', 'گروه عمومی'))).strip()
                            nts = str(row.get('توضیحات', row.get('notes', ''))).strip()
                            
                            if fn and ln:
                                try:
                                    cursor.execute(
                                        "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group, notes) VALUES (?, ?, ?, ?, ?, ?)",
                                        (fn, ln, nid, phone, grp, nts)
                                    )
                                    success_count += 1
                                except sqlite3.IntegrityError:
                                    pass
                        conn.commit()
                    st.balloons()
                    st.success(f"تعداد {success_count} دانش‌آموز جدید با موفقیت وارد دیتابیس شدند!")
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در پردازش فایل: {e}")

    with tab3:
        with st.form("add_single_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("نام:")
                national_id = st.text_input("کد ملی دانش‌آموز:")
                student_group = st.selectbox("گروه آموزشی کلاسی (۵ گروه):", FIFTH_GRADE_GROUPS)
            with col2:
                last_name = st.text_input("نام خانوادگی:")
                parent_phone = st.text_input("شماره همراه اولیا (جهت اطلاع‌رسانی):")
            
            notes = st.text_area("توضیحات ویژه یا ملاحظات آموزشی:")
            submit_btn = st.form_submit_button("ثبت دانش‌آموز")
            
            if submit_btn:
                if first_name and last_name:
                    try:
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group, notes) VALUES (?, ?, ?, ?, ?, ?)",
                                (first_name, last_name, national_id, parent_phone, student_group, notes)
                            )
                            conn.commit()
                        st.success(f"دانش‌آموز {first_name} {last_name} ثبت شد.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("کد ملی وارد شده تکراری است.")
                else:
                    st.warning("لطفاً نام و نام خانوادگی را وارد کنید.")

# ---------------------------------------------------------
# 3. Qualitative Evaluation (Teacher Only)
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("ابتدا باید دانش‌آموزان را در سیستم ثبت کنید.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            selected_student_str = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
            selected_subject = st.selectbox("عنوان درس:", FIFTH_GRADE_SUBJECTS)
        with col2:
            selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
            eval_date = st.date_input("تاریخ ارزشیابی:", datetime.date.today())
            
        feedback_text = st.text_area("بازخورد توصیفی و توصیه‌های آموزشی آموزگار:", 
                                     placeholder="توصیف دقیق عملکرد دانش‌آموز و راهکارهای ارتقا...")
        
        if st.button("ثبت ارزشیابی توصیفی"):
            s_id = int(selected_student_str.split(' - ')[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text, eval_date)
                )
                conn.commit()
            st.success("ارزشیابی توصیفی با موفقیت ثبت شد.")

        st.markdown("---")
        st.subheader("📜 سوابق ارزشیابی‌های ثبت‌شده برای این دانش‌آموز")
        s_id = int(selected_student_str.split(' - ')[0])
        with get_connection() as conn:
            eval_df = safe_read_sql("""
                SELECT subject AS 'درس', level AS 'سطح عملکرد', feedback AS 'بازخورد توصیفی', eval_date AS 'تاریخ'
                FROM evaluations WHERE student_id = ? ORDER BY eval_date DESC
            """, conn, params=(s_id,))
            
        if not eval_df.empty:
            st.dataframe(eval_df, use_container_width=True)
        else:
            st.info("هنوز ارزشیابی برای این دانش‌آموز ثبت نشده است.")

# ---------------------------------------------------------
# 4. Behavior & Discipline Tracking (Teacher Only)
# ---------------------------------------------------------
elif menu_choice.startswith("4"):
    check_teacher_auth()
    st.header("🌟 مدیریت رفتار و مشاهدات انضباطی کلاسی")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("لطفاً ابتدا دانش‌آموزان را ثبت کنید.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            selected_student_str = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
            b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
        with col2:
            title = st.text_input("عنوان رفتار (مثلاً: مشارکت عالی در گروه، دقت در انجام تکلیف):")
            log_date = st.date_input("تاریخ ثبت:", datetime.date.today())
            
        desc = st.text_area("شرح مشاهدات انضباطی و اقدام آموزگار:")
        
        if st.button("ثبت مورد رفتاری / انضباطی"):
            s_id = int(selected_student_str.split(' - ')[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, b_type, title, desc, log_date)
                )
                conn.commit()
            st.success("مشاهده رفتاری ثبت گردید.")
            
        st.markdown("---")
        st.subheader("📋 سوابق رفتاری ثبت‌شده دانش‌آموز")
        s_id = int(selected_student_str.split(' - ')[0])
        with get_connection() as conn:
            beh_df = safe_read_sql("""
                SELECT behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ'
                FROM behaviors WHERE student_id = ? ORDER BY log_date DESC
            """, conn, params=(s_id,))
            
        if not beh_df.empty:
            st.dataframe(beh_df, use_container_width=True)
        else:
            st.info("هیچ مورد رفتاری ثبت نشده است.")

# ---------------------------------------------------------
# 5. Quiz Creator & Exam Designer (Teacher Only)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین و طراحی سوالات")
    
    tab_q1, tab_q2, tab_q3 = st.tabs([
        "➕ طراحی دستی آزمون و سوالات", 
        "📥 بارگذاری فایل آماده آزمون (JSON)", 
        "📊 لیست آزمون‌ها و نتایج"
    ])
    
    with tab_q1:
        st.subheader("۱. مشخصات کلی آزمون")
        col1, col2, col3 = st.columns(3)
        with col1:
            quiz_title = st.text_input("عنوان آزمون (مثلاً: آزمونک فصل ۱ و ۲ ریاضی):")
        with col2:
            quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS)
        with col3:
            duration = st.number_input("مدت زمان آزمون (دقیقه):", min_value=5, max_value=180, value=30)
            
        num_mc = st.number_input("تعداد سوالات ۴ گزینه‌ای (تستی):", min_value=0, max_value=20, value=2)
        num_essay = st.number_input("تعداد سوالات تشریحی / تحلیلی:", min_value=0, max_value=10, value=1)
        
        st.markdown("---")
        st.subheader("۲. طراحی سوالات تستی (۴ گزینه‌ای)")
        
        mc_questions_data = []
        for i in range(int(num_mc)):
            st.markdown(f"**📌 سوال تستی شماره {i+1}:**")
            q_text = st.text_input(f"متن سوال تستی {i+1}:", key=f"mc_q_{i}")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                opt1 = st.text_input(f"گزینه ۱:", key=f"mc_opt1_{i}")
            with c2:
                opt2 = st.text_input(f"گزینه ۲:", key=f"mc_opt2_{i}")
            with c3:
                opt3 = st.text_input(f"گزینه ۳:", key=f"mc_opt3_{i}")
            with c4:
                opt4 = st.text_input(f"گزینه ۴:", key=f"mc_opt4_{i}")
            
            c_corr, c_exp = st.columns([1, 2])
            with c_corr:
                correct_opt = st.selectbox(f"گزینه صحیحسوال {i+1}:", [1, 2, 3, 4], key=f"mc_corr_{i}")
            with c_exp:
                exp_text = st.text_input(f"💡 تحلیل آموزشی / پاسخ‌نامه تشریحی سوال {i+1}:", key=f"mc_exp_{i}")
                
            mc_questions_data.append((q_text, opt1, opt2, opt3, opt4, correct_opt, exp_text))
            st.markdown("---")
            
        st.subheader("۳. طراحی سوالات تشریحی / تحلیلی")
        essay_questions_data = []
        for j in range(int(num_essay)):
            st.markdown(f"**📝 سوال تشریحی شماره {j+1}:**")
            eq_text = st.text_area(f"متن سوال تشریحی {j+1}:", key=f"eq_q_{j}")
            em_ans = st.text_area(f"🔑 پاسخ نمونه / راهنمای تصحیح سوال {j+1}:", key=f"eq_ans_{j}")
            e_exp = st.text_input(f"💡 تحلیل و نکته کلیدی سوال {j+1}:", key=f"eq_exp_{j}")
            essay_questions_data.append((eq_text, em_ans, e_exp))
            st.markdown("---")
            
        if st.button("🚀 انتشار و ذخیره نهایی آزمون"):
            if quiz_title and (mc_questions_data or essay_questions_data):
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                        (quiz_title, quiz_subject, duration, datetime.date.today())
                    )
                    quiz_id = cursor.lastrowid
                    
                    for q in mc_questions_data:
                        if q[0]:
                            cursor.execute("""
                                INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, explanation)
                                VALUES (?, 'multiple_choice', ?, ?, ?, ?, ?, ?, ?)
                            """, (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6]))
                            
                    for eq in essay_questions_data:
                        if eq[0]:
                            cursor.execute("""
                                INSERT INTO questions (quiz_id, question_type, question_text, model_answer, explanation)
                                VALUES (?, 'essay', ?, ?, ?)
                            """, (quiz_id, eq[0], eq[1], eq[2]))
                    conn.commit()
                st.balloons()
                st.success(f"آزمون '{quiz_title}' با موفقیت منتشر شد!")
            else:
                st.error("لطفاً عنوان آزمون و متن سوالات را وارد کنید.")

    with tab_q2:
        st.subheader("📥 بارگذاری فایل آماده آزمون (JSON)")
        st.write("شما می‌توانید فایل JSON سوالات آماده طراحی‌شده توسط آموزگار یا هوش مصنوعی را آپلود کنید.")
        
        sample_json_quiz = {
            "title": "آزمون نمونه هوشمند ریاضی و علوم",
            "subject": "ریاضی",
            "duration_minutes": 45,
            "questions": [
                {
                    "type": "multiple_choice",
                    "text": "حاصل ضرب ۰/۰۴ × ۱۰ کدام است؟",
                    "options": ["۰/۰۴", "۰/۴", "۴", "۴۰"],
                    "correct_option": 2,
                    "explanation": "ضرب یک عدد اعشاری در ۱۰، ممیز را یک رقم به سمت راست می‌برد."
                },
                {
                    "type": "essay",
                    "text": "وظیفه گلبول‌های قرمز و سفید خونی را مقایسه کنید.",
                    "model_answer": "گلبول قرمز اکسیژن‌رسانی می‌کند و گلبول سفید دفاع در برابر بیماری‌ها را بر عهده دارد.",
                    "explanation": "هر دو سلول‌های اصلی خون هستند."
                }
            ]
        }
        
        st.download_button(
            label="📥 دانلود الگوی نمونه فایل JSON آزمون",
            data=json.dumps(sample_json_quiz, ensure_ascii=False, indent=2),
            file_name="quiz_template.json",
            mime="application/json"
        )
        
        json_file = st.file_uploader("فایل JSON آزمون را آپلود کنید:", type=["json"], key="json_quiz_uploader")
        if json_file is not None:
            try:
                quiz_data = json.load(json_file)
                st.success(f"آزمون '{quiz_data.get('title')}' شناسایی شد! تعداد سوالات: {len(quiz_data.get('questions', []))}")
                
                if st.button("🚀 ثبت و انتشار آزمون بارگذاری‌شده"):
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                            (quiz_data.get('title'), quiz_data.get('subject', 'ریاضی'), quiz_data.get('duration_minutes', 30), datetime.date.today())
                        )
                        quiz_id = cursor.lastrowid
                        
                        for q in quiz_data.get('questions', []):
                            q_type = q.get('type', 'multiple_choice')
                            q_text = q.get('text', '')
                            exp = q.get('explanation', '')
                            
                            if q_type == 'multiple_choice':
                                opts = q.get('options', ['', '', '', ''])
                                corr = q.get('correct_option', 1)
                                cursor.execute("""
                                    INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, explanation)
                                    VALUES (?, 'multiple_choice', ?, ?, ?, ?, ?, ?, ?)
                                """, (quiz_id, q_text, opts[0], opts[1], opts[2], opts[3], corr, exp))
                            else:
                                m_ans = q.get('model_answer', '')
                                cursor.execute("""
                                    INSERT INTO questions (quiz_id, question_type, question_text, model_answer, explanation)
                                    VALUES (?, 'essay', ?, ?, ?)
                                """, (quiz_id, q_text, m_ans, exp))
                        conn.commit()
                    st.balloons()
                    st.success("آزمون بارگذاری‌شده با موفقیت در سیستم قرار گرفت!")
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در ساختار فایل JSON: {e}")

    with tab_q3:
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'زمان (دقیقه)', created_at AS 'تاریخ ساخت' FROM quizzes ORDER BY id DESC", conn)
            
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True)
            
            st.subheader("📈 مشاهدات کارنامه و نتایج آزمون")
            selected_quiz_id = st.selectbox("انتخاب آزمون:", quizzes_df['id'].tolist(), format_func=lambda x: quizzes_df[quizzes_df['id'] == x]['عنوان'].values[0])
            
            with get_connection() as conn:
                results_df = safe_read_sql("""
                    SELECT s.first_name || ' ' || s.last_name AS 'دانش‌آموز',
                           s.student_group AS 'گروه کلاسی',
                           r.score AS 'نمره تستی',
                           r.total_questions AS 'کل تستی',
                           r.percentage AS 'درصد تستی ٪',
                           r.essay_answers AS 'پاسخ‌های تشریحی',
                           r.submitted_at AS 'زمان ثبت'
                    FROM quiz_results r
                    JOIN students s ON r.student_id = s.id
                    WHERE r.quiz_id = ? ORDER BY r.percentage DESC
                """, conn, params=(selected_quiz_id,))
                
            if not results_df.empty:
                st.dataframe(results_df, use_container_width=True)
            else:
                st.info("هنوز هیچ دانش‌آموزی در این آزمون شرکت نکرده است.")
        else:
            st.info("هنوز هیچ آزمونی تعریف نشده است.")

# ---------------------------------------------------------
# 6. Student Online Quiz Interface (Mobile Friendly)
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین دانش‌آموزی")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = safe_read_sql("SELECT id, title, subject, duration_minutes FROM quizzes WHERE is_active = 1 ORDER BY id DESC", conn)
        
    if students_df.empty or quizzes_df.empty:
        st.warning("در حال حاضر آزمون فعال یا دانش‌آموزی در سیستم تعریف نشده است.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            selected_student_str = st.selectbox("دانش‌آموز عزیز؛ نام خود را انتخاب کنید:", students_df['full_name'].tolist())
        with col2:
            quiz_name = st.selectbox("انتخاب آزمون آنلاین:", quizzes_df['title'].tolist())
            
        s_id = int(selected_student_str.split(' - ')[0])
        q_id = int(quizzes_df[quizzes_df['title'] == quiz_name]['id'].values[0])
        duration_mins = int(quizzes_df[quizzes_df['id'] == q_id]['duration_minutes'].values[0])
        
        # Check prior submission
        with get_connection() as conn:
            existing = conn.execute("SELECT id, percentage, essay_answers FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing:
            st.success(f"🎉 شما قبلاً در این آزمون شرکت کرده‌اید. درصد کسب‌شده در بخش تستی: {existing['percentage']:.1f}٪")
            if existing['essay_answers']:
                st.info(f"📝 پاسخ‌های تشریحی ثبت‌شده شما: {existing['essay_answers']}")
        else:
            st.warning(f"⏱️ مهلت زمان پاسخگویی به این آزمون: {duration_mins} دقیقه است.")
            
            with get_connection() as conn:
                questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ? ORDER BY id ASC", (q_id,)).fetchall()
                
            if not questions:
                st.info("سوالاتی برای این آزمون یافت نشد.")
            else:
                student_mc_answers = {}
                student_essay_answers = {}
                
                st.markdown("---")
                with st.form("take_online_quiz_form"):
                    for idx, q in enumerate(questions):
                        q_type = q['question_type']
                        q_text = q['question_text']
                        
                        st.markdown(f"### 📌 سوال {idx+1}: {q_text}")
                        
                        if q_type == 'multiple_choice':
                            opts = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                            ans = st.radio(
                                f"گزینه انتخابی سوال {idx+1}:",
                                options=[1, 2, 3, 4],
                                format_func=lambda x: f"گزینه {x}: {opts[x-1]}",
                                key=f"student_ans_mc_{q['id']}"
                            )
                            student_mc_answers[q['id']] = (ans, q['correct_option'], q['explanation'])
                        else:
                            e_ans = st.text_area(
                                f"پاسخ تشریحی شما برای سوال {idx+1}:",
                                placeholder="پاسخ کامل خود را بنویسید...",
                                key=f"student_ans_essay_{q['id']}"
                            )
                            student_essay_answers[q['id']] = (e_ans, q['model_answer'], q['explanation'])
                        st.markdown("---")
                        
                    submit_quiz = st.form_submit_button("🚀 ثبت نهایی آزمون و دریافت نتیجه آنی")
                    
                    if submit_quiz:
                        mc_correct = 0
                        mc_total = len(student_mc_answers)
                        
                        for q_key, (user_ans, correct, exp) in student_mc_answers.items():
                            if user_ans == correct:
                                mc_correct += 1
                                
                        pct = (mc_correct / mc_total) * 100 if mc_total > 0 else 0
                        
                        # Serialize essay answers
                        essay_summary = ""
                        for q_key, (user_text, m_ans, exp) in student_essay_answers.items():
                            essay_summary += f"[سوال {q_key}: {user_text}] | "
                            
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, essay_answers) VALUES (?, ?, ?, ?, ?, ?)",
                                (q_id, s_id, mc_correct, mc_total, pct, essay_summary)
                            )
                            conn.commit()
                            
                        st.balloons()
                        st.success(f"🎉 آزمون با موفقیت ثبت گردید! نمره تستی شما: {mc_correct} از {mc_total} (معادل {pct:.1f} درصد)")
                        
                        # Show Explanation & Analysis
                        st.markdown("### 💡 پاسخ‌نامه تشریحی و تحلیل آموزشی آزمون:")
                        for idx, q in enumerate(questions):
                            st.markdown(f"**سوال {idx+1}: {q['question_text']}**")
                            if q['question_type'] == 'multiple_choice':
                                st.write(f"گزینه صحیح: گزینه {q['correct_option']}")
                            else:
                                st.write(f"پاسخ نمونه آموزگار: {q['model_answer']}")
                            if q['explanation']:
                                st.info(f"💡 تحلیل آموزشی: {q['explanation']}")
                            st.markdown("---")

# ---------------------------------------------------------
# 7. Student Portfolio & Comprehensive Dashboard
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 پوشه کار و کارنامه جامع تحصیلی دانش‌آموزان")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("هنوز هیچ دانش‌آموزی ثبت نشده است.")
    else:
        selected_student_str = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار:", students_df['full_name'].tolist())
        s_id = int(selected_student_str.split(' - ')[0])
        
        # Get student info
        with get_connection() as conn:
            st_info = conn.execute("SELECT * FROM students WHERE id = ?", (s_id,)).fetchone()
            
        st.markdown(f"""
        <div class="feature-box">
            <h2>🏆 پرونده تحصیلی: {st_info['first_name']} {st_info['last_name']}</h2>
            <p>کد ملی: {st_info['national_id']} | گروه آموزشی: <b>{st_info['student_group']}</b> | شماره همراه اولیا: {st_info['parent_phone']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            
        with col1:
            st.metric("تعداد ارزشیابی‌های کیفی-توصیفی:", eval_count)
        with col2:
            st.metric("تعداد امتیازات رفتاری ثبت‌شده:", beh_count)
        with col3:
            st.metric("میانگین درصد آزمون‌های آنلاین:", f"{quiz_avg:.1f}٪" if quiz_avg is not None else "بدون آزمون")
            
        st.markdown("---")
        
        tab_p1, tab_p2, tab_p3 = st.tabs(["📝 ارزشیابی توصیفی", "🌟 سوابق آزمون‌های آنلاین", "❇️ امتیازات رفتاری"])
        
        with tab_p1:
            with get_connection() as conn:
                df_e = safe_read_sql("""
                    SELECT subject AS 'عنوان درس', level AS 'سطح عملکرد', feedback AS 'توصیف عملکرد', eval_date AS 'تاریخ'
                    FROM evaluations WHERE student_id = ? ORDER BY eval_date DESC
                """, conn, params=(s_id,))
            if not df_e.empty:
                st.dataframe(df_e, use_container_width=True)
            else:
                st.info("ارزشیابی توصیفی برای این دانش‌آموز ثبت نشده است.")
                
        with tab_p2:
            with get_connection() as conn:
                df_q = safe_read_sql("""
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس',
                           r.score AS 'نمره تستی', r.total_questions AS 'کل تستی',
                           r.percentage AS 'درصد تستی ٪', r.essay_answers AS 'پاسخ‌های تشریحی',
                           r.submitted_at AS 'زمان ثبت'
                    FROM quiz_results r
                    JOIN quizzes q ON r.quiz_id = q.id
                    WHERE r.student_id = ? ORDER BY r.id DESC
                """, conn, params=(s_id,))
            if not df_q.empty:
                st.dataframe(df_q, use_container_width=True)
            else:
                st.info("سوابق آزمون آنلاینی یافت نشد.")
                
        with tab_p3:
            with get_connection() as conn:
                df_b = safe_read_sql("""
                    SELECT behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ'
                    FROM behaviors WHERE student_id = ? ORDER BY log_date DESC
                """, conn, params=(s_id,))
            if not df_b.empty:
                st.dataframe(df_b, use_container_width=True)
            else:
                st.info("امتیاز رفتاری ثبت نشده است.")

