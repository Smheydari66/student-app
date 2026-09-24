import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json

# ---------------------------------------------------------
# Page Configuration & Full RTL CSS Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین (نسخه v27 با ۴ لایه امنیت)",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Persian / RTL CSS Styling & Fixes
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    html, body, [class*="css"], div, span, button, input, select, textarea, label, p, h1, h2, h3, h4, h5, h6 {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
        color: #ffffff !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
    }
    
    /* Responsive Header */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white !important;
        padding: 24px;
        border-radius: 16px;
        text-align: center !important;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .main-header h2, .main-header p {
        color: #ffffff !important;
        text-align: center !important;
    }
    
    /* Card Styling */
    .card-box {
        background: rgba(30, 41, 59, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    /* Quote Box */
    .quote-card {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.6) 0%, rgba(30, 41, 59, 0.9) 100%);
        border-right: 6px solid #fbbf24;
        border-left: 1px solid rgba(255, 255, 255, 0.1);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding: 22px;
        border-radius: 14px;
        margin-bottom: 22px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.25);
    }
    
    /* Button Styles & Text Wrap Fixes */
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
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(37, 99, 235, 0.4) !important;
    }
    
    /* Text Inputs, Selectboxes, Dataframes */
    input, select, textarea, div[data-baseweb="select"] {
        color: #ffffff !important;
        background-color: #0f172a !important;
        border-radius: 8px !important;
    }
    
    /* Radio Buttons Nav */
    div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }
    
    div[role="radiogroup"] label {
        background-color: rgba(30, 41, 59, 0.7) !important;
        padding: 10px 16px !important;
        border-radius: 10px !important;
        margin-bottom: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: all 0.2s !important;
    }
    
    div[role="radiogroup"] label:hover {
        background-color: rgba(37, 99, 235, 0.4) !important;
        border-color: #3b82f6 !important;
    }
    
    /* Popover Fix */
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
            parent_phone TEXT,
            student_group TEXT DEFAULT 'بدون گروه',
            pin TEXT DEFAULT '1234',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            eval_date DATE,
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
            log_date DATE,
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
            created_at DATE
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
            essay_answers TEXT,
            photo_data TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
            ("students", "student_group", "TEXT DEFAULT 'بدون گروه'"),
            ("students", "pin", "TEXT DEFAULT '1234'"),
            ("quizzes", "is_active", "INTEGER DEFAULT 1"),
            ("questions", "question_type", "TEXT DEFAULT 'mcq'"),
            ("questions", "model_answer", "TEXT"),
            ("questions", "explanation", "TEXT"),
            ("quiz_results", "essay_answers", "TEXT"),
            ("quiz_results", "photo_data", "TEXT")
        ]
        for table, col, col_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass
                
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
# Default Quiz Seeder
# ---------------------------------------------------------
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

# ---------------------------------------------------------
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
        df = safe_read_sql("SELECT id, first_name || ' ' || last_name AS full_name, national_id, parent_phone, student_group, pin, notes FROM students", conn)
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
    st.session_state['excel_upload_key'] = 0
if 'show_welcome_page' not in st.session_state:
    st.session_state['show_welcome_page'] = True

# ---------------------------------------------------------
# WELCOME SPLASH PAGE (صفحه خوش‌آمدگویی پیش از ورود)
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
    
    if st.button("🚀 ورود به سامانه هوشمند مدیریت کلاس و آزمون آنلاین", use_container_width=True):
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

# Navigation & Login Header Bar
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
# NAVIGATION MENU (RADIO BUTTONS - 100% READONLY & CLICKABLE)
# ---------------------------------------------------------
st.markdown("### 📌 منوی بخش‌های سامانه (انتخاب کنید):")

if st.session_state['is_teacher_logged_in']:
    menu_options = [
        "1️⃣ 🏠 معرفی سامانه و اهداف آموزشی",
        "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی (۲۹ نفر)",
        "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی",
        "4️⃣ 🌟 مدیریت رفتار و مشاهدات انضباطی",
        "5️⃣ ✏️ آزمون‌ساز آنلاین و طراحی سوالات",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع"
    ]
else:
    menu_options = [
        "1️⃣ 🏠 معرفی سامانه و اهداف آموزشی",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع"
    ]

menu_choice = st.radio("منو:", menu_options, label_visibility="collapsed", key="main_nav_menu")

# Teacher Auth Guard Helper
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
        <h4>2️⃣ آزمون‌ساز آنلاین با سوالات تستی و تشریحی</h4>
        <p>طراحی آزمون، تعیین زمان معکوس (مثلاً ۶۰ دقیقه)، تصحیح خودکار بخش تستی و ارائه تحلیل آموزشی.</p>
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
    
    tab1, tab2, tab3 = st.tabs(["📋 لیست دانش‌آموزان و گروه‌ها", "📊 ثبت دسته‌جمعی و سریع از اکسل", "➕ ثبت دانش‌آموز جدید (تکی)"])
    
    with tab1:
        students_df = load_students()
        if not students_df.empty:
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام یا کد ملی):")
            with col_s2:
                selected_group_filter = st.selectbox("فیلتر بر اساس گروه:", ["همه گروه‌ها"] + CLASS_GROUPS)
                
            filtered_df = students_df.copy()
            if search_query:
                filtered_df = filtered_df[filtered_df['full_name'].str.contains(search_query) | filtered_df['national_id'].str.contains(search_query)]
            if selected_group_filter != "همه گروه‌ها":
                filtered_df = filtered_df[filtered_df['student_group'] == selected_group_filter]
                
            st.dataframe(filtered_df.rename(columns={
                'id': 'شناسه',
                'full_name': 'نام و نام خانوادگی',
                'national_id': 'کد ملی',
                'parent_phone': 'شماره اولیا',
                'student_group': 'گروه کلاسی',
                'notes': 'توضیحات'
            }), use_container_width=True)
            
            st.markdown("---")
            st.subheader("🗑️ مدیریت یا حذف پرونده")
            student_to_delete = st.selectbox("انتخاب دانش‌آموز جهت حذف:", students_df['full_name'].tolist(), key="del_student")
            if st.button("حذف پرونده دانش‌آموز"):
                s_id = int(students_df[students_df['full_name'] == student_to_delete]['id'].values[0])
                with get_connection() as conn:
                    conn.execute("DELETE FROM students WHERE id = ?", (s_id,))
                    conn.commit()
                st.success(f"پرونده {student_to_delete} با موفقیت حذف شد.")
                st.rerun()
        else:
            st.info("هنوز هیچ دانش‌آموزی ثبت نشده است. می‌توانید از زبانه 'ثبت دسته‌جمعی از اکسل' استفاده کنید.")

    with tab2:
        st.subheader("📊 ورود یکجای اسامی دانش‌آموزان از فایل اکسل (Excel/CSV)")
        st.info("فایل اکسل شما باید حداقل دارای ستون‌های 'first_name' (نام) و 'last_name' (نام خانوادگی) باشد. ستون‌های کد ملی، تلفن اولیا و گروه اختیاری هستند.")
        
        sample_data = pd.DataFrame({
            'first_name': ['علی', 'محمد'],
            'last_name': ['حیدری', 'رضایی'],
            'national_id': ['1234567890', '0987654321'],
            'parent_phone': ['09181112233', '09184445566'],
            'student_group': ['گروه ارمغان 🚀', 'گروه دانا 💡']
        })
        st.download_button(
            "📥 دانلود نمونه فایل الگوی اکسل (CSV)",
            sample_data.to_csv(index=False).encode('utf-8-sig'),
            "sample_students.csv",
            "text/csv"
        )
        
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
                    
                st.write("👀 پیش‌نمایش اطلاعات فایل آپلود شده:")
                st.dataframe(df_upload.head(10), use_container_width=True)
                
                if st.button("⚡ بارگذاری و ذخیره تمام اسامی در دیتابیس"):
                    added_count = 0
                    with get_connection() as conn:
                        for idx, row in df_upload.iterrows():
                            fname = str(row.get('first_name', '')).strip()
                            lname = str(row.get('last_name', '')).strip()
                            nid = str(row.get('national_id', '')).strip() if pd.notna(row.get('national_id')) else f"100{idx+1}"
                            phone = str(row.get('parent_phone', '')).strip() if pd.notna(row.get('parent_phone')) else ""
                            group = str(row.get('student_group', '')).strip() if pd.notna(row.get('student_group')) else CLASS_GROUPS[idx % 5]
                            
                            if fname and lname and fname != 'nan' and lname != 'nan':
                                try:
                                    conn.execute(
                                        "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group) VALUES (?, ?, ?, ?, ?)",
                                        (fname, lname, nid, phone, group)
                                    )
                                    added_count += 1
                                except sqlite3.IntegrityError:
                                    pass
                        conn.commit()
                    st.success(f"🎉 تعداد {added_count} دانش‌آموز با موفقیت وارد سامانه شدند.")
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در خواندن فایل اکسل: {e}")

    with tab3:
        with st.form("add_single_student"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("نام:")
                national_id = st.text_input("کد ملی:")
                student_group = st.selectbox("گروه آموزشی کلاسی:", CLASS_GROUPS)
            with col2:
                last_name = st.text_input("نام خانوادگی:")
                parent_phone = st.text_input("شماره همراه اولیا:")
                notes = st.text_area("توضیحات ویژه:")
                
            if st.form_submit_button("ثبت دانش‌آموز"):
                if first_name and last_name:
                    try:
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group, pin, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (first_name, last_name, national_id, parent_phone, student_group, student_pin, notes)
                            )
                            conn.commit()
                        st.success(f"دانش‌آموز {first_name} {last_name} ثبت شد.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("کد ملی تکراری است.")

# ---------------------------------------------------------
# 3. QUALITATIVE EVALUATION (TEACHER ONLY)
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
            eval_date = st.date_input("تاریخ ارزشیابی:", datetime.date.today())
            
        feedback_text = st.text_area("توصیف عملکرد و بازخورد آموزگار:")
        
        if st.button("ثبت ارزشیابی توصیفی"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text, eval_date)
                )
                conn.commit()
            st.success("ارزشیابی توصیفی ثبت شد.")

        st.markdown("---")
        st.subheader(f"📋 سوابق ارزشیابی: {selected_student}")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        with get_connection() as conn:
            eval_h = safe_read_sql("""
                SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'بازخورد معلم', eval_date AS 'تاریخ'
                FROM evaluations WHERE student_id = ? ORDER BY eval_date DESC
            """, conn, params=(s_id,))
        if not eval_h.empty:
            st.dataframe(eval_h, use_container_width=True)

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
            log_date = st.date_input("تاریخ ثبت:", datetime.date.today())
            
        desc = st.text_area("جزییات و اقدامات انجام‌شده:")
        
        if st.button("ثبت مشاهده رفتاری"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, b_type, title, desc, log_date)
                )
                conn.commit()
            st.success("مشاهده رفتاری ذخیره شد.")

# ---------------------------------------------------------
# 5. ONLINE QUIZ CREATOR (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (طراحی و انتشار آزمون)")
    
    tab_q1, tab_q2, tab_q3 = st.tabs(["➕ طراحی مستقیم آزمون", "📥 بارگذاری فایل آماده آزمون (JSON)", "📊 لیست آزمون‌ها و نتایج"])
    
    with tab_q1:
        col1, col2, col3 = st.columns(3)
        with col1:
            quiz_title = st.text_input("عنوان آزمون:")
        with col2:
            quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS)
        with col3:
            duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=180, value=60)
            
        num_q = st.number_input("تعداد سوالات:", min_value=1, max_value=30, value=3)
        
        questions_input = []
        for i in range(int(num_q)):
            st.markdown(f"**📌 سوال شماره {i+1}:**")
            q_type = st.selectbox(f"نوع سوال {i+1}:", ["تستی ۴ گزینه‌ای", "تشریحی / تحلیلی"], key=f"qtype_{i}")
            q_text = st.text_area(f"متن سوال {i+1}:", key=f"qtext_{i}")
            
            if q_type == "تستی ۴ گزینه‌ای":
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    o1 = st.text_input(f"گزینه ۱:", key=f"o1_{i}")
                with c2:
                    o2 = st.text_input(f"گزینه ۲:", key=f"o2_{i}")
                with c3:
                    o3 = st.text_input(f"گزینه ۳:", key=f"o3_{i}")
                with c4:
                    o4 = st.text_input(f"گزینه ۴:", key=f"o4_{i}")
                corr = st.selectbox(f"گزینه صحیح:", [1, 2, 3, 4], key=f"corr_{i}")
                exp = st.text_area(f"تحلیل و پاسخ تشریحی سوال {i+1}:", key=f"exp_{i}")
                questions_input.append(('mcq', q_text, o1, o2, o3, o4, corr, None, exp))
            else:
                m_ans = st.text_area(f"پاسخ نمونه / کلید تصحیح سوال {i+1}:", key=f"mans_{i}")
                exp = st.text_area(f"تحلیل آموزشی سوال {i+1}:", key=f"exp_e_{i}")
                questions_input.append(('essay', q_text, None, None, None, None, 1, m_ans, exp))
            st.markdown("---")
            
        if st.button("🚀 انتشار و فعال‌سازی آزمون"):
            if quiz_title and all(q[1] for q in questions_input):
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                        (quiz_title, quiz_subject, duration, datetime.date.today())
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
        st.subheader("📥 بارگذاری فایل کامل سوالات آزمون (JSON)")
        
        sample_quiz_json = {
            "title": "آزمونک هوشمند ریاضی و علوم پایه پنجم",
            "subject": "ریاضی",
            "duration_minutes": 45,
            "questions": [
                {
                    "question_type": "mcq",
                    "question_text": "حاصل ضرب ۳/۴ در ۴/۵ کدام است؟",
                    "option_1": "۳/۵", "option_2": "۱۲/۲۰", "option_3": "۷/۹", "option_4": "۱/۵",
                    "correct_option": 1,
                    "explanation": "با ساده کردن عدد ۴ از صورت و مخرج، کسر ۳/۵ به دست می‌آید."
                },
                {
                    "question_type": "essay",
                    "question_text": "چرا هنگام انجام آزمایش‌های علوم باید از عینک ایمنی استفاده کرد؟",
                    "model_answer": "جهت محافظت از چشم‌ها در برابر پاشش مواد شیمیایی و پرتاب احتمالی اجسام.",
                    "explanation": "رعایت نکات ایمنی اولویت اول کار در آزمایشگاه علوم است."
                }
            ]
        }
        
        st.download_button(
            "📥 دانلود نمونه فایل الگوی آزمون (JSON)",
            json.dumps(sample_quiz_json, ensure_ascii=False, indent=2),
            "quiz_template.json",
            "application/json"
        )
        
        uploaded_json = st.file_uploader("فایل JSON آزمون را انتخاب کنید:", type=["json"])
        if uploaded_json is not None:
            try:
                data = json.load(uploaded_json)
                st.success(f"فایل آزمون '{data.get('title')}' شناسایی شد شامل {len(data.get('questions', []))} سوال.")
                if st.button("⚡ بارگذاری و فعال‌سازی این آزمون"):
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                            (data.get('title'), data.get('subject', 'ریاضی'), data.get('duration_minutes', 60), datetime.date.today())
                        )
                        qid = cursor.lastrowid
                        for q in data.get('questions', []):
                            cursor.execute("""
                                INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                qid, q.get('question_type', 'mcq'), q.get('question_text'),
                                q.get('option_1'), q.get('option_2'), q.get('option_3'), q.get('option_4'),
                                q.get('correct_option', 1), q.get('model_answer'), q.get('explanation')
                            ))
                        conn.commit()
                    st.success("آزمون با موفقیت بارگذاری و فعال شد!")
            except Exception as e:
                st.error(f"خطا در خواندن فایل JSON: {e}")

    with tab_q3:
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'مدت (دقیقه)', created_at AS 'تاریخ ساخت' FROM quizzes", conn)
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True)

# ---------------------------------------------------------
# 6. STUDENT QUIZ TAKING INTERFACE (MOBILE FRIENDLY + 4 SECURITY LAYERS)
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = safe_read_sql("SELECT id, title, subject, duration_minutes FROM quizzes WHERE is_active = 1", conn)
        
    if students_df.empty or quizzes_df.empty:
        st.warning("در حال حاضر آزمون فعال یا دانش‌آموزی در سیستم تعریف نشده است.")
    else:
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            student_name = st.selectbox("نام دانش‌آموز (خود را انتخاب کنید):", students_df['full_name'].tolist())
        with col2:
            quiz_name = st.selectbox("انتخاب آزمون:", quizzes_df['title'].tolist())
        with col3:
            student_pin_input = st.text_input("🔑 رمز ۴ رقمی اختصاصی:", type="password", key="quiz_pin_input")
            
        s_row = students_df[students_df['full_name'] == student_name].iloc[0]
        s_id = int(s_row['id'])
        s_pin = str(s_row.get('pin', '1234')) if pd.notna(s_row.get('pin')) else '1234'
        q_id = int(quizzes_df[quizzes_df['title'] == quiz_name]['id'].values[0])
        
        # Security Layer 1: Personal 4-digit PIN Verification
        if not student_pin_input:
            st.info("🔑 لطفاً جهت احراز هویت و شرکت در آزمون، رمز ۴ رقمی اختصاصی خود را در کادر بالا وارد کنید (رمز پیش‌فرض: 1234).")
        elif student_pin_input != s_pin:
            st.error("❌ رمز ۴ رقمی اختصاصی وارد شده اشتباه است. لطفاً رمز صحیح خود را وارد کنید.")
        else:
            # Security Layer 3: One-Time Submission Lock Check
            with get_connection() as conn:
                existing = conn.execute("SELECT id, percentage, photo_data FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
                
            if existing:
                st.success(f"🔒 این آزمون قبلاً توسط شما تحویل داده شده و قفل گردیده است. درصد بخش تستی: {existing['percentage']:.1f}٪")
                if existing['photo_data']:
                    st.image(existing['photo_data'], caption="📸 تصویر ثبت‌شده چهره هنگام تحویل آزمون", width=160)
            else:
                duration_min = int(quizzes_df[quizzes_df['id'] == q_id]['duration_minutes'].values[0])
                st.info(f"⏱️ زمان پاسخگویی: {duration_min} دقیقه | 🟢 احراز هویت با موفقیت انجام شد.")
                
                # Security Layer 4: Facial Photo Capture
                st.markdown("##### 📸 تصویر چهره دانش‌آموز (جهت ثبت در برگه آزمون):")
                captured_photo = st.camera_input("برای ثبت عکس چهره روی دکمه عکاسی کلیک کنید (اختیاری/الزامی):", key=f"cam_{s_id}_{q_id}")
                
                photo_b64 = None
                if captured_photo is not None:
                    import base64
                    photo_bytes = captured_photo.getvalue()
                    photo_b64 = "data:image/png;base64," + base64.b64encode(photo_bytes).decode('utf-8')
                
                # Security Layer 2: Question Shuffling (Randomized per student & quiz)
                with get_connection() as conn:
                    questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                    
                import random
                rng = random.Random(s_id * 1000 + q_id)
                shuffled_questions = list(questions)
                rng.shuffle(shuffled_questions)
                
                student_mcq_ans = {}
                student_essay_ans = {}
                
                st.markdown("---")
                with st.form("take_quiz_form"):
                    for idx, q in enumerate(shuffled_questions):
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
                        
                    submit_quiz = st.form_submit_button("🏁 پایان آزمون و ثبت نهایی پاسخ‌ها")
                    
                    if submit_quiz:
                        correct_count = 0
                        mcq_total = len(student_mcq_ans)
                        for qid, (u_ans, c_ans) in student_mcq_ans.items():
                            if u_ans == c_ans:
                                correct_count += 1
                        pct = (correct_count / mcq_total * 100) if mcq_total > 0 else 100.0
                        
                        essay_json_str = json.dumps(student_essay_ans, ensure_ascii=False)
                        
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, essay_answers, photo_data) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (q_id, s_id, correct_count, mcq_total, pct, essay_json_str, photo_b64)
                            )
                            conn.commit()
                            
                        st.balloons()
                        st.success(f"🎉 پاسخ‌های شما با موفقیت ثبت شد! نمره‌ی بخش تستی: {correct_count} از {mcq_total} ({pct:.1f}٪)")
                        st.rerun()

# ---------------------------------------------------------
# 7. DASHBOARD & STUDENT PORTFOLIO
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد تحلیلی و پوشه کار جامع دانش‌آموز")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی وجود ندارد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار:", students_df['full_name'].tolist())
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            
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
                df_e = safe_read_sql("SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ?", conn, params=(s_id,))
            if not df_e.empty:
                st.dataframe(df_e, use_container_width=True)
            else:
                st.info("ارزشیابی درسی ثبت نشده است.")
                
        with tab_d2:
            with get_connection() as conn:
                df_b = safe_read_sql("SELECT behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ' FROM behaviors WHERE student_id = ?", conn, params=(s_id,))
            if not df_b.empty:
                st.dataframe(df_b, use_container_width=True)
            else:
                st.info("مورد رفتاری ثبت نشده است.")
                
        with tab_d3:
            with get_connection() as conn:
                df_q = safe_read_sql("""
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات تستی', r.percentage AS 'درصد ٪', r.photo_data, r.submitted_at AS 'زمان ثبت'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ?
                """, conn, params=(s_id,))
            if not df_q.empty:
                # Display DataFrame without raw photo base64
                show_df = df_q.drop(columns=['photo_data'], errors='ignore')
                st.dataframe(show_df, use_container_width=True)
                
                # Show photos if captured
                photos = [row['photo_data'] for _, row in df_q.iterrows() if row.get('photo_data')]
                if photos:
                    st.markdown("##### 📸 تصاویر چهره ثبت‌شده هنگام شرکت در آزمون:")
                    p_cols = st.columns(min(len(photos), 4))
                    for p_idx, p_data in enumerate(photos):
                        with p_cols[p_idx % 4]:
                            st.image(p_data, caption=f"تصویر آزمون {p_idx+1}", width=140)
            else:
                st.info("نتیجه آزمونی ثبت نشده است.")

